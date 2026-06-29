#!/usr/bin/env python3
"""Vexium Voice — Phase 1 dev client (laptop mic, NO phone).

Streams your microphone to the Deepgram Voice Agent API and plays the agent's
voice back, validating the STT -> Claude (AWS Bedrock) -> TTS loop locally before
touching telephony.

    Run:  python dev_client.py
    Stop: Ctrl+C

Milestone: speak into your mic; the agent should reply with voice and you should
see the live transcript in the terminal.
"""
import asyncio
import json
import os
import queue
import sys
import threading

import sounddevice as sd
import websockets
from dotenv import load_dotenv

import clinic
from agent_config import (
    DEEPGRAM_AGENT_URL,
    build_settings,
    detect_language,
    speak_for_language,
)

# Tracks the active TTS language so we can swap voices (ES<->EN) mid-call.
_speak_state = {"lang": "es"}

load_dotenv()

MIC_RATE = 16000   # linear16 mono sent to Deepgram
SPK_RATE = 24000   # Aura-2 linear16 output
MIC_BLOCK = 1600   # 100 ms @ 16 kHz
CHANNELS = 1
SAMPLE_BYTES = 2   # int16

API_KEY = os.getenv("DEEPGRAM_API_KEY")

# Thread-safe handoff between PortAudio callback threads and the asyncio loop.
_mic_q: "queue.Queue[bytes]" = queue.Queue()
_spk_buf = bytearray()
_spk_lock = threading.Lock()


def _mic_callback(indata, frames, time_info, status):
    if status:
        print(f"[mic] {status}", file=sys.stderr)
    _mic_q.put(bytes(indata))


def _spk_callback(outdata, frames, time_info, status):
    if status:
        print(f"[spk] {status}", file=sys.stderr)
    needed = frames * CHANNELS * SAMPLE_BYTES
    with _spk_lock:
        take = min(needed, len(_spk_buf))
        chunk = bytes(_spk_buf[:take])
        del _spk_buf[:take]
    if take < needed:
        chunk += b"\x00" * (needed - take)  # pad with silence
    outdata[:] = chunk


def _enqueue_agent_audio(data: bytes):
    with _spk_lock:
        _spk_buf.extend(data)


def _flush_agent_audio():
    """Barge-in: drop agent audio still waiting to play when the user speaks."""
    with _spk_lock:
        _spk_buf.clear()


async def _sender(ws, loop, stop: asyncio.Event):
    while not stop.is_set():
        try:
            data = await loop.run_in_executor(None, _mic_q.get, True, 0.1)
        except queue.Empty:
            continue
        try:
            await ws.send(data)
        except websockets.ConnectionClosed:
            break


async def _handle_function_calls(ws, evt: dict):
    """Handle client-side FunctionCallRequests (check_availability, book_appointment).

    For each function we parse the JSON-string `arguments`, run the clinic business
    logic, log it to the console, and reply with a FunctionCallResponse so the agent
    can speak the result (offer alternatives, or confirm the booking).
    """
    for fn in evt.get("functions", []):
        name = fn.get("name", "")
        try:
            args = json.loads(fn.get("arguments") or "{}")
        except json.JSONDecodeError:
            args = {}

        if name == "check_availability":
            result = clinic.check_availability(**args)
            mark = "✅ free" if result.get("available") else "⛔ taken"
            print(f"\n🔎 CHECK {args.get('requested_datetime', '?')} → {mark}")
            if not result.get("available") and result.get("alternatives"):
                print(f"     alternatives: {', '.join(result['alternatives'])}")
            print()
        elif name == "book_appointment":
            result = clinic.book_appointment(**args)
            b = result.get("booking", {})
            print("\n📅 BOOKING CONFIRMED  " + result.get("confirmation_code", ""))
            for k in ("caller_name", "phone", "service", "preferred_datetime", "language"):
                if b.get(k):
                    print(f"     {k}: {b[k]}")
            print()
        else:
            print(f"⚠️  Unknown function requested: {name}", file=sys.stderr)
            result = {"status": "error", "message": f"unknown function {name}"}

        await ws.send(json.dumps({
            "type": "FunctionCallResponse",
            "id": fn.get("id"),
            "name": name,
            "content": json.dumps(result, ensure_ascii=False),  # content must be a string
        }))


async def _receiver(ws, stop: asyncio.Event):
    try:
        async for message in ws:
            if isinstance(message, (bytes, bytearray)):
                _enqueue_agent_audio(bytes(message))
                continue
            try:
                evt = json.loads(message)
            except json.JSONDecodeError:
                continue
            kind = evt.get("type")
            if kind == "Welcome":
                print("✓ Connected to Deepgram Voice Agent.")
            elif kind == "SettingsApplied":
                print("✓ Settings applied — start talking!  (Ctrl+C to quit)\n")
            elif kind == "ConversationText":
                role = evt.get("role", "?")
                who = "🧑 You  " if role == "user" else "🤖 Agent"
                print(f"{who}: {evt.get('content', '')}")
                if role == "user":
                    lang = detect_language(evt.get("content", ""))
                    if lang and lang != _speak_state["lang"]:
                        _speak_state["lang"] = lang
                        await ws.send(json.dumps({
                            "type": "UpdateSpeak", "speak": speak_for_language(lang),
                        }))
            elif kind == "UserStartedSpeaking":
                _flush_agent_audio()  # barge-in
            elif kind == "FunctionCallRequest":
                await _handle_function_calls(ws, evt)
            elif kind in ("Error", "Warning"):
                print(f"⚠️  {kind}: {evt}", file=sys.stderr)
            # AgentThinking / AgentStartedSpeaking / AgentAudioDone: ignored for now
    finally:
        stop.set()


async def main():
    if not API_KEY:
        sys.exit("DEEPGRAM_API_KEY missing — copy .env.example to .env and fill it in.")

    settings = build_settings()
    think = settings["agent"]["think"]["provider"]
    if not think.get("credentials", {}).get("access_key_id"):
        print("⚠️  AWS credentials look empty — Bedrock calls will fail. Check .env.\n",
              file=sys.stderr)

    print(f"Connecting to {DEEPGRAM_AGENT_URL} …")
    print(f"  STT : {settings['agent']['listen']['provider']['model']}")
    print(f"  LLM : {think['type']} / {think.get('model')}")
    print(f"  TTS : {settings['agent']['speak']['provider']['model']}\n")

    async with websockets.connect(
        DEEPGRAM_AGENT_URL,
        subprotocols=["token", API_KEY],
        ping_interval=5,
        ping_timeout=20,
        max_size=None,
    ) as ws:
        await ws.send(json.dumps(settings))

        loop = asyncio.get_running_loop()
        stop = asyncio.Event()

        in_stream = sd.RawInputStream(
            samplerate=MIC_RATE, blocksize=MIC_BLOCK, channels=CHANNELS,
            dtype="int16", callback=_mic_callback,
        )
        out_stream = sd.RawOutputStream(
            samplerate=SPK_RATE, channels=CHANNELS, dtype="int16",
            callback=_spk_callback,
        )
        with in_stream, out_stream:
            await asyncio.gather(_sender(ws, loop, stop), _receiver(ws, stop))


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Bye.")
