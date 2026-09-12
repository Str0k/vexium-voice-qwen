"""Qwen TTS (qwen3-tts-flash) on Alibaba Cloud Model Studio — spoken replies for
the text demo mode, so the no-microphone path is still voice-first and 100% Qwen.
Returns a short-lived audio URL the browser plays directly; any upstream problem
degrades to text-only (callers must treat status != 'ok' as non-fatal)."""

import os
from urllib.parse import urlsplit

import httpx

_LANGUAGE_TYPE = {"es": "Spanish", "en": "English"}


def _api_url() -> str:
    """Same DashScope host the brain uses (QWEN_BASE_URL) — switching region or
    proxy in one env var moves brain AND voice together."""
    base = os.getenv("QWEN_BASE_URL", "https://dashscope-intl.aliyuncs.com/compatible-mode/v1")
    parts = urlsplit(base)
    host = (
        f"{parts.scheme}://{parts.netloc}"
        if parts.netloc
        else "https://dashscope-intl.aliyuncs.com"
    )
    return f"{host}/api/v1/services/aigc/multimodal-generation/generation"


def _post(url, payload, key, http):
    headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
    if http is not None:
        return http.post(url, json=payload, headers=headers)
    with httpx.Client(timeout=30) as client:
        return client.post(url, json=payload, headers=headers)


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
    try:
        r = _post(_api_url(), payload, key, http)
        if r.status_code != 200:
            return {"status": "error", "detail": f"dashscope {r.status_code}: {r.text[:200]}"}
        data = r.json()
        url = (((data.get("output") or {}).get("audio")) or {}).get("url", "")
        if not url:
            return {"status": "error", "detail": "no audio url in response"}
        return {"status": "ok", "url": url}
    except Exception as exc:  # noqa: BLE001 — TTS is a nice-to-have, never fatal
        return {"status": "error", "detail": str(exc)[:200]}
