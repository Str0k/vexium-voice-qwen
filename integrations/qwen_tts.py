"""Qwen TTS (qwen3-tts-flash) on Alibaba Cloud Model Studio — spoken replies for
the text demo mode, so the no-microphone path is still voice-first and 100% Qwen.
Returns a short-lived audio URL the browser plays directly; any upstream problem
degrades to text-only (callers must treat status != 'ok' as non-fatal)."""
import os
import httpx

API = "https://dashscope-intl.aliyuncs.com/api/v1/services/aigc/multimodal-generation/generation"

_LANGUAGE_TYPE = {"es": "Spanish", "en": "English"}


def synthesize(text: str, language: str = "es", *, http=None) -> dict:
    key = os.environ.get("DASHSCOPE_API_KEY", "").strip()
    if not key:
        return {"status": "error", "detail": "DASHSCOPE_API_KEY not set"}
    payload = {
        "model": os.getenv("QWEN_TTS_MODEL", "qwen3-tts-flash"),
        "input": {
            "text": (text or "")[:600],
            "voice": os.getenv("QWEN_TTS_VOICE", "Cherry"),
            "language_type": _LANGUAGE_TYPE.get(language, "Auto"),
        },
    }
    client = http or httpx.Client(timeout=30)
    try:
        r = client.post(API, json=payload,
                        headers={"Authorization": f"Bearer {key}",
                                 "Content-Type": "application/json"})
        if r.status_code != 200:
            return {"status": "error", "detail": f"dashscope {r.status_code}: {r.text[:200]}"}
        data = r.json()
        url = (((data.get("output") or {}).get("audio")) or {}).get("url", "")
        if not url:
            return {"status": "error", "detail": "no audio url in response"}
        return {"status": "ok", "url": url}
    except Exception as exc:  # noqa: BLE001 — TTS is a nice-to-have, never fatal
        return {"status": "error", "detail": str(exc)[:200]}
