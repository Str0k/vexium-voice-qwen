#!/usr/bin/env python3
"""Vexium Voice — browser bridge (web demo).

A small FastAPI WebSocket server that bridges a BROWSER (mic in / speaker out) to
the Deepgram Voice Agent API, reusing the exact same agent config and clinic logic
as the local mic client. The browser never sees any secret — the Deepgram key and
Bedrock credentials live here, server-side.

    Browser  --PCM16 16k-->  /ws  --->  Deepgram Voice Agent (STT+Claude/Bedrock+TTS)
             <--PCM16 24k--        <---

Run locally:
    uvicorn server:app --host 0.0.0.0 --port 8000
Then expose it with ngrok so the Vercel frontend can reach it:
    ngrok http 8000      ->   set NEXT_PUBLIC_BRIDGE_URL=wss://<id>.ngrok-free.app/ws

This is also the foundation for the Phase 3 Twilio bridge and the Phase 6 AWS deploy
(same container, just a different inbound audio source).
"""
import asyncio
import json
import os

import websockets
from dotenv import load_dotenv
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse

import metrics as metrics

from agent_config import (
    DEEPGRAM_AGENT_URL,
    VERTICALS,
    build_settings,
    detect_language,
    handle_function,
    speak_for_language,
)

load_dotenv()

API_KEY = os.getenv("DEEPGRAM_API_KEY")

app = FastAPI(title="Vexium Voice Bridge")

# The browser (any Vercel preview/prod URL) connects cross-origin. The WS itself
# isn't CORS-restricted, but the health route benefits from permissive CORS.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def health():
    return {"status": "ok", "service": "vexium-voice-bridge"}


@app.get("/summary")
def summary(tenant: str = "dental"):
    return JSONResponse(metrics.summary(tenant))


@app.get("/events")
async def events(tenant: str = "dental"):
    async def gen():
        while True:
            yield f"data: {json.dumps(metrics.summary(tenant))}\n\n"
            await asyncio.sleep(2)
    return StreamingResponse(gen(), media_type="text/event-stream")


async def _handle_function_calls(dg, browser, evt: dict, vertical: str):
    """Run the vertical's client-side functions, answer Deepgram with a
    FunctionCallResponse (so it can speak the result), AND surface the structured
    result to the browser UI so it can render the captured booking/availability."""
    for fn in evt.get("functions", []):
        name = fn.get("name", "")
        try:
            args = json.loads(fn.get("arguments") or "{}")
        except json.JSONDecodeError:
            args = {}

        result = handle_function(vertical, name, args)

        await dg.send(json.dumps({
            "type": "FunctionCallResponse",
            "id": fn.get("id"),
            "name": name,
            "content": json.dumps(result, ensure_ascii=False),
        }))
        # Surface the same structured result to the UI (the "booking captured" card).
        try:
            await browser.send_text(json.dumps({
                "type": "FunctionResult",
                "name": name,
                "arguments": args,
                "result": result,
            }, ensure_ascii=False))
        except (WebSocketDisconnect, RuntimeError):
            pass


@app.websocket("/ws")
async def ws_endpoint(browser: WebSocket):
    await browser.accept()
    if not API_KEY:
        await browser.send_text(json.dumps({"type": "Error", "description": "Server missing DEEPGRAM_API_KEY"}))
        await browser.close()
        return

    # The frontend picks the demo vertical via ?v=dental|restaurant (default dental).
    vertical = (browser.query_params.get("v") or "dental").strip().lower()
    if vertical not in VERTICALS:
        vertical = "dental"

    settings = build_settings(vertical)  # input linear16 16k, output linear16 24k

    try:
        async with websockets.connect(
            DEEPGRAM_AGENT_URL,
            subprotocols=["token", API_KEY],
            ping_interval=5,
            ping_timeout=20,
            max_size=None,
        ) as dg:
            await dg.send(json.dumps(settings))

            # Track the TTS language so we can swap the ElevenLabs voice per turn
            # (Mexican voice for Spanish, US voice for English) via UpdateSpeak.
            state = {"lang": "es"}

            async def browser_to_dg():
                try:
                    while True:
                        msg = await browser.receive()
                        if msg.get("type") == "websocket.disconnect":
                            break
                        data = msg.get("bytes")
                        if data is not None:
                            await dg.send(data)          # raw PCM16 audio frames
                        # text messages from the browser (if any) are ignored for now
                except WebSocketDisconnect:
                    pass
                finally:
                    await dg.close()

            async def dg_to_browser():
                async for message in dg:
                    if isinstance(message, (bytes, bytearray)):
                        await browser.send_bytes(bytes(message))   # agent audio
                        continue
                    # JSON event: act on function calls, swap voice per language,
                    # and forward everything to the UI.
                    try:
                        evt = json.loads(message)
                    except json.JSONDecodeError:
                        continue
                    kind = evt.get("type")
                    if kind == "FunctionCallRequest":
                        await _handle_function_calls(dg, browser, evt, vertical)
                        continue  # result is forwarded separately; don't echo the raw request
                    out = message
                    if kind == "ConversationText":
                        content = evt.get("content", "")
                        if evt.get("role") == "user":
                            # Per-turn language for the voice swap. Prefer Deepgram Flux's OWN
                            # detection (user ConversationText carries `languages`, BCP-47, sorted
                            # by word count — robust to a single borrowed word). Our setup often
                            # omits it, so fall back to the text heuristic, which switches on any
                            # clear es/en signal; a truly ambiguous turn returns None -> no flip,
                            # so the voice never jumps on a bare "okay", a name, or a phone number.
                            dg_langs = evt.get("languages") or []
                            turn_lang = dg_langs[0][:2].lower() if dg_langs else None
                            if turn_lang not in ("es", "en"):
                                turn_lang = detect_language(content)
                            switch_to = turn_lang if (turn_lang and turn_lang != state["lang"]) else None
                            if switch_to:
                                state["lang"] = switch_to
                                print(f"[lang] -> {switch_to}  (dg={dg_langs or 'none'}, '{content[:48]}')", flush=True)
                                await dg.send(json.dumps({
                                    "type": "UpdateSpeak",
                                    "speak": speak_for_language(switch_to, vertical),
                                }))
                            evt["lang"] = turn_lang if turn_lang in ("es", "en") else state["lang"]
                        else:
                            evt["lang"] = state["lang"]
                        out = json.dumps(evt, ensure_ascii=False)
                    try:
                        await browser.send_text(out)
                    except (WebSocketDisconnect, RuntimeError):
                        break

            await asyncio.gather(browser_to_dg(), dg_to_browser())
    except Exception as exc:  # noqa: BLE001 — surface any bridge error to the UI
        try:
            await browser.send_text(json.dumps({"type": "Error", "description": str(exc)}))
        except RuntimeError:
            pass
    finally:
        try:
            await browser.close()
        except RuntimeError:
            pass
