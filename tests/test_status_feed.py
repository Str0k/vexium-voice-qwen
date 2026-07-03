"""Ops surface for the dashboard: /status (integration health), /feed (activity),
/run-due-reminders (scheduler entry point), /tts (Qwen spoken replies)."""
from fastapi.testclient import TestClient
import server
import metrics
import reminders
import integrations.qwen_tts as qwen_tts
import integrations.tablestore_store as store


def test_status_reports_each_integration(monkeypatch):
    for k in ("DASHSCOPE_API_KEY", "TABLESTORE_ENDPOINT", "CALCOM_API_KEY", "STRIPE_API_KEY"):
        monkeypatch.delenv(k, raising=False)
    monkeypatch.setenv("SMS_PROVIDER", "none")
    c = TestClient(server.app)
    s = c.get("/status").json()
    assert s["brain"]["connected"] is False
    assert s["store"]["backend"] == "memory"
    assert s["sms"]["connected"] is False
    assert "Qwen3-Max" in s["brain"]["provider"]
    assert "Tablestore" in s["store"]["provider"]


def test_status_connected_when_configured(monkeypatch):
    monkeypatch.setenv("DASHSCOPE_API_KEY", "sk-test")
    monkeypatch.setenv("SMS_PROVIDER", "alibaba")
    c = TestClient(server.app)
    s = c.get("/status").json()
    assert s["brain"]["connected"] is True
    assert s["sms"]["provider"] == "Alibaba Cloud SMS" and s["sms"]["connected"] is True


def test_feed_returns_newest_first(monkeypatch):
    fake = [
        {"ts": 1, "call_id": "a", "payload": {"type": "call_handled"}},
        {"ts": 3, "call_id": "b", "payload": {"type": "booking_made", "service": "Limpieza"}},
        {"ts": 2, "call_id": "c", "payload": {"type": "handoff"}},
    ]
    monkeypatch.setattr(store, "list_events", lambda t, limit=200: fake)
    c = TestClient(server.app)
    out = c.get("/feed?tenant=dental").json()["events"]
    assert [e["ts"] for e in out] == [3, 2, 1]
    assert out[0]["type"] == "booking_made"


def test_run_due_reminders_fires_and_records(monkeypatch):
    recorded = []
    monkeypatch.setattr(reminders, "run_due_from_store", lambda t: ["r1", "r2"])
    monkeypatch.setattr(metrics, "record", lambda *a, **k: recorded.append((a, k)) or "id")
    c = TestClient(server.app)
    out = c.post("/run-due-reminders?tenant=dental").json()
    assert out["count"] == 2 and len(recorded) == 2


def test_tts_returns_audio_url(monkeypatch):
    monkeypatch.setattr(qwen_tts, "synthesize", lambda text, lang, **k: {"status": "ok", "url": "https://a/b.wav"})
    c = TestClient(server.app)
    r = c.post("/tts", json={"text": "Hola, ¿en qué le puedo ayudar?"})
    assert r.status_code == 200 and r.json()["url"].endswith(".wav")


def test_tts_failure_is_502_not_fatal(monkeypatch):
    monkeypatch.setattr(qwen_tts, "synthesize", lambda text, lang, **k: {"status": "error", "detail": "x"})
    c = TestClient(server.app)
    r = c.post("/tts", json={"text": "hola"})
    assert r.status_code == 502
