#!/usr/bin/env python3
"""Vexium Voice — FastAPI bridge and API.

Voice path: bridges a BROWSER (mic in / speaker out) to the Deepgram Voice Agent,
whose "think" step is **Qwen3-Max on Alibaba Cloud Model Studio** (DashScope
OpenAI-compatible endpoint). The browser never sees any secret — every key lives
here, server-side.

    Browser  --PCM16 16k-->  /ws  --->  Deepgram Voice Agent (STT + Qwen + TTS)
             <--PCM16 24k--        <---

Text path (no mic / no Deepgram key needed): POST /chat drives the same brain —
`qwen_brain.run_turn` calls Qwen3-Max directly with the vertical's system prompt
and tools, so judges can exercise the full booking flow from any browser.

Ops surface: /summary and /events (SSE) feed the live ROI dashboard, /feed streams
the raw event log, /status reports each cloud integration, /run-due-reminders
fires due appointment reminders (call it from cron or an Alibaba FC timer).

Run locally:
    uvicorn server:app --host 0.0.0.0 --port 8000
"""
import asyncio
import json
import os
import threading
import uuid
from datetime import datetime

import websockets
from dotenv import load_dotenv
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse

import evaluation
import metrics
import qwen_brain
import reminders
import integrations.qwen_tts as qwen_tts
import integrations.tablestore_store as store

import clinic
import restaurant
import integrations.calendar_calcom as cal
import integrations.payments_stripe as pay
from agent_config import (
    DEEPGRAM_AGENT_URL,
    VERTICALS,
    build_settings,
    build_system_prompt,
    detect_language,
    handle_function,
    speak_for_language,
)

load_dotenv()

API_KEY = os.getenv("DEEPGRAM_API_KEY")

app = FastAPI(title="Vexium Voice Bridge")

# The browser (any preview/prod URL) connects cross-origin. The WS itself isn't
# CORS-restricted, but the HTTP routes benefit from permissive CORS.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def health():
    return {"status": "ok", "service": "vexium-voice-bridge"}


# ── Ops / dashboard API ──────────────────────────────────────────────────────

@app.get("/summary")
def summary(tenant: str = "dental"):
    return JSONResponse(metrics.summary(tenant))


@app.get("/events")
async def events(tenant: str = "dental"):
    async def gen():
        while True:
            # Store reads are blocking network I/O — keep them off the event
            # loop so SSE ticks never stall live voice audio.
            summary_ = await asyncio.to_thread(metrics.summary, tenant)
            payload = {**summary_, "ts": int(datetime.now().timestamp() * 1000)}
            yield f"data: {json.dumps(payload)}\n\n"
            await asyncio.sleep(2)
    return StreamingResponse(gen(), media_type="text/event-stream")


@app.get("/feed")
def feed(tenant: str = "dental", limit: int = 50):
    """Latest raw events (newest first) for the dashboard's live activity feed."""
    evts = store.list_events(tenant)
    out = [{"ts": e.get("ts", 0), "call_id": e.get("call_id", ""), **(e.get("payload") or {})}
           for e in evts]
    out.sort(key=lambda e: e.get("ts", 0), reverse=True)
    return {"events": out[:max(1, min(limit, 200))]}


@app.get("/status")
def status():
    """Which cloud integrations are live right now. Drives the dashboard's
    'stack' panel — honest about what is connected vs running on a fallback.
    Each service declares its own `state` (on | fallback | simulated | offline)
    and `alibaba` flag so the UI renders facts instead of guessing from labels."""
    sms_kind = os.getenv("SMS_PROVIDER", "none").strip().lower()
    sms_live = sms_kind in ("alibaba", "twilio")
    elevenlabs = bool(os.getenv("ELEVENLABS_API_KEY", "").strip()
                      and os.getenv("ELEVENLABS_VOICE_ID", "").strip())
    brain_on = bool(os.getenv("DASHSCOPE_API_KEY", "").strip())
    store_on = store.backend() == "tablestore"
    return {
        "brain": {
            "provider": "Qwen3-Max · Alibaba Cloud Model Studio",
            "model": os.getenv("QWEN_BRAIN_MODEL", "qwen3-max"),
            "connected": brain_on, "state": "on" if brain_on else "offline", "alibaba": True,
        },
        "store": {
            "provider": "Alibaba Cloud Tablestore",
            "backend": store.backend(),  # "tablestore" | "memory"
            "connected": store_on, "state": "on" if store_on else "fallback", "alibaba": True,
        },
        "sms": {
            "provider": {"alibaba": "Alibaba Cloud SMS", "twilio": "Twilio SMS"}.get(sms_kind, "SMS"),
            "connected": sms_live, "state": "on" if sms_live else "simulated",
            "alibaba": sms_kind != "twilio",
        },
        "voice": {"provider": "Deepgram Voice Agent (Flux STT)", "connected": bool(API_KEY),
                  "state": "on" if API_KEY else "offline", "alibaba": False},
        "tts": {"provider": "ElevenLabs Flash v2.5" if elevenlabs else "Deepgram Aura-2",
                "connected": True, "state": "on", "alibaba": False},
        "calendar": {"provider": "Cal.com", "connected": cal.is_configured(),
                     "state": "on" if cal.is_configured() else "simulated", "alibaba": False},
        "payments": {"provider": "Stripe", "connected": pay.is_configured(),
                     "state": "on" if pay.is_configured() else "simulated", "alibaba": False},
    }


@app.post("/run-due-reminders")
def run_due_reminders(tenant: str = "dental"):
    """Fire every due appointment reminder (T-24h / T-1h SMS). Called by cron —
    or by an Alibaba Function Compute timer in the cloud deploy."""
    fired = reminders.run_due_from_store(tenant)
    for rid in fired:
        metrics.record(tenant, "", "reminder_sent", reminder_id=rid)
    return {"fired": fired, "count": len(fired)}


# ── Text mode — the same Qwen3-Max brain, no microphone required ─────────────

def _openai_tools(vertical: str) -> list:
    return [{"type": "function", "function": f} for f in VERTICALS[vertical]["functions"]]


@app.post("/chat")
async def chat(payload: dict):
    """One text turn against the vertical's Qwen3-Max function-calling brain.
    Body: {vertical, messages:[{role:'user'|'assistant', content}...]}.
    Returns {reply, tool_events} — tool_events carry the structured booking data
    the UI renders as the 'booking captured' card."""
    vertical = (payload.get("vertical") or "dental").strip().lower()
    if vertical not in VERTICALS:
        vertical = "dental"
    history = [
        {"role": m.get("role"), "content": str(m.get("content", ""))[:2000]}
        for m in (payload.get("messages") or [])
        if m.get("role") in ("user", "assistant") and str(m.get("content", "")).strip()
    ][-24:]
    if not history:
        return JSONResponse({"error": "empty_conversation"}, status_code=422)
    if not os.getenv("DASHSCOPE_API_KEY", "").strip():
        return JSONResponse(
            {"error": "qwen_not_configured",
             "detail": "Set DASHSCOPE_API_KEY to enable the Qwen text mode."},
            status_code=503,
        )
    messages = [{"role": "system", "content": build_system_prompt(vertical)}, *history]
    # Mint the call id up-front and thread it through the tool calls, so a text
    # booking's events correlate with its call_handled/call_scored records —
    # exactly like the voice path.
    call_id = uuid.uuid4().hex
    try:
        out = await asyncio.to_thread(
            qwen_brain.run_turn, messages, _openai_tools(vertical), vertical,
            extra_args={"tenant": vertical, "call_id": call_id},
        )
    except Exception as exc:  # noqa: BLE001 — surface upstream API failures cleanly
        return JSONResponse({"error": "qwen_upstream", "detail": str(exc)[:300]}, status_code=502)

    # A text conversation that lands a booking counts as a handled contact and
    # gets the same Qwen-as-judge QA pass as a finished voice call.
    booked = any(
        ev.get("name") in ("book_appointment", "book_reservation")
        and (ev.get("result") or {}).get("status") == "confirmed"
        for ev in out.get("tool_events", [])
    )
    if booked:
        try:
            await asyncio.to_thread(metrics.record, vertical, call_id, "call_handled",
                                    turns=len(history) + 1, vertical=vertical, channel="text")
        except Exception as exc:  # noqa: BLE001
            print(f"[metrics] record failed: {exc}", flush=True)
        transcript = [(m["role"], m["content"]) for m in history]
        if out.get("reply"):
            transcript.append(("assistant", out["reply"]))
        _score_call_async(vertical, call_id, transcript, out.get("tool_events", []))
    return out


@app.post("/tts")
async def tts(payload: dict):
    """Speak a text-mode reply with Qwen TTS (qwen3-tts-flash). Returns a
    short-lived audio URL; the UI treats any error as 'stay text-only'."""
    text = str(payload.get("text", "")).strip()[:600]
    if not text:
        return JSONResponse({"error": "empty_text"}, status_code=422)
    lang = payload.get("language") or detect_language(text) or "auto"
    out = await asyncio.to_thread(qwen_tts.synthesize, text, lang)
    if out.get("status") != "ok":
        return JSONResponse({"error": "tts_failed", "detail": out.get("detail", "")}, status_code=502)
    return out


# ── Voice bridge ─────────────────────────────────────────────────────────────

def _is_after_hours(vertical: str = "dental", now: datetime | None = None) -> bool:
    now = now or datetime.now()
    biz = restaurant if vertical == "restaurant" else clinic
    hours = biz.BUSINESS_HOURS.get(now.weekday())
    return not hours or not (hours[0] <= now.hour < hours[1])


def _score_call_async(tenant: str, call_id: str, transcript: list, tool_events: list):
    """Post-call QA: Qwen-as-judge scores the finished call in a daemon thread
    and records the verdict as a `call_scored` event for the dashboard."""
    if len(transcript) < 2 or not os.getenv("DASHSCOPE_API_KEY", "").strip():
        return

    def _run():
        try:
            text = "\n".join(f"{role}: {content}" for role, content in transcript)
            scores = evaluation.score_call(text, tool_events)
            metrics.record(tenant, call_id, "call_scored", **scores)
        except Exception as exc:  # noqa: BLE001 — QA must never break the service
            print(f"[eval] scoring failed: {exc}", flush=True)

    threading.Thread(target=_run, daemon=True).start()


async def _handle_function_calls(dg, browser, evt: dict, vertical: str, call: dict):
    """Run the vertical's client-side functions, answer Deepgram with a
    FunctionCallResponse (so it can speak the result), AND surface the structured
    result to the browser UI so it can render the captured booking/availability."""
    for fn in evt.get("functions", []):
        name = fn.get("name", "")
        try:
            args = json.loads(fn.get("arguments") or "{}")
        except json.JSONDecodeError:
            args = {}

        # Tag the business context so handlers persist to the right tenant.
        # Handlers do blocking I/O (Cal.com, Tablestore, SMS) — run them off the
        # event loop so live audio keeps flowing for every connection.
        result = await asyncio.to_thread(
            handle_function, vertical, name,
            {**args, "tenant": call["tenant"], "call_id": call["id"]})
        call["tools"].append({"name": name, "arguments": args, "result": result})

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
    # The tenant doubles as the store partition key — allowlist it so anonymous
    # visitors can't write junk partitions or pollute another tenant's metrics.
    tenant = (browser.query_params.get("tenant") or vertical).strip().lower()
    if tenant not in VERTICALS:
        tenant = vertical

    settings = build_settings(vertical)  # input linear16 16k, output linear16 24k

    # Per-call context: id + transcript + tool log, for metrics and post-call QA.
    call = {"id": uuid.uuid4().hex, "tenant": tenant, "transcript": [], "tools": []}

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
                        await _handle_function_calls(dg, browser, evt, vertical, call)
                        continue  # result is forwarded separately; don't echo the raw request
                    out = message
                    if kind == "ConversationText":
                        content = evt.get("content", "")
                        call["transcript"].append((evt.get("role", "agent"), content))
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
        # Call bookkeeping: count the call, flag after-hours saves, run QA.
        # Store writes run off the event loop (other calls may still be live).
        if call["transcript"] or call["tools"]:
            def _bookkeep():
                try:
                    metrics.record(tenant, call["id"], "call_handled",
                                   turns=len(call["transcript"]), vertical=vertical)
                    if _is_after_hours(vertical):
                        metrics.record(tenant, call["id"], "after_hours")
                except Exception as exc:  # noqa: BLE001
                    print(f"[metrics] record failed: {exc}", flush=True)
            await asyncio.to_thread(_bookkeep)
            _score_call_async(tenant, call["id"], call["transcript"], call["tools"])
        try:
            await browser.close()
        except RuntimeError:
            pass
