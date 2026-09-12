"""Text mode: POST /chat drives the same Qwen3-Max brain with no mic required."""

from fastapi.testclient import TestClient

import qwen_brain
import server


def test_chat_requires_dashscope_key(monkeypatch):
    monkeypatch.delenv("DASHSCOPE_API_KEY", raising=False)
    c = TestClient(server.app)
    r = c.post(
        "/chat", json={"vertical": "dental", "messages": [{"role": "user", "content": "hola"}]}
    )
    assert r.status_code == 503 and r.json()["error"] == "qwen_not_configured"


def test_chat_rejects_empty_conversation(monkeypatch):
    monkeypatch.setenv("DASHSCOPE_API_KEY", "sk-test")
    c = TestClient(server.app)
    r = c.post("/chat", json={"vertical": "dental", "messages": []})
    assert r.status_code == 422


def test_chat_returns_reply_and_tool_events(monkeypatch):
    monkeypatch.setenv("DASHSCOPE_API_KEY", "sk-test")
    captured = {}

    def fake_run_turn(messages, tools, vertical, **kw):
        captured["system"] = messages[0]
        captured["vertical"] = vertical
        captured["tools"] = tools
        return {"reply": "Claro, ¿su nombre completo?", "tool_events": []}

    monkeypatch.setattr(qwen_brain, "run_turn", fake_run_turn)
    c = TestClient(server.app)
    r = c.post(
        "/chat",
        json={
            "vertical": "restaurant",
            "messages": [{"role": "user", "content": "una mesa para 4"}],
        },
    )
    assert r.status_code == 200
    assert r.json()["reply"].startswith("Claro")
    assert captured["vertical"] == "restaurant"
    assert captured["system"]["role"] == "system" and "Valentina" in captured["system"]["content"]
    assert captured["tools"][0]["type"] == "function"


def test_chat_upstream_error_is_502(monkeypatch):
    monkeypatch.setenv("DASHSCOPE_API_KEY", "sk-test")

    def boom(*a, **k):
        raise RuntimeError("rate limited")

    monkeypatch.setattr(qwen_brain, "run_turn", boom)
    c = TestClient(server.app)
    r = c.post("/chat", json={"messages": [{"role": "user", "content": "hi"}]})
    assert r.status_code == 502 and r.json()["error"] == "qwen_upstream"


def test_chat_booking_records_metrics_and_triggers_judge(monkeypatch):
    monkeypatch.setenv("DASHSCOPE_API_KEY", "sk-test")
    recorded, scored = [], []

    def fake_run_turn(messages, tools, vertical, **kw):
        return {
            "reply": "Su cita quedó confirmada.",
            "tool_events": [
                {"name": "book_appointment", "arguments": {}, "result": {"status": "confirmed"}}
            ],
        }

    import metrics

    monkeypatch.setattr(qwen_brain, "run_turn", fake_run_turn)
    monkeypatch.setattr(metrics, "record", lambda *a, **k: recorded.append((a, k)) or "id")
    monkeypatch.setattr(server, "_score_call_async", lambda *a, **k: scored.append(a))
    c = TestClient(server.app)
    r = c.post(
        "/chat",
        json={"vertical": "dental", "messages": [{"role": "user", "content": "sí, confirmo"}]},
    )
    assert r.status_code == 200
    assert recorded and recorded[0][0][2] == "call_handled" and recorded[0][1]["channel"] == "text"
    assert len(scored) == 1


def test_chat_without_booking_does_not_record(monkeypatch):
    monkeypatch.setenv("DASHSCOPE_API_KEY", "sk-test")
    recorded = []
    import metrics

    monkeypatch.setattr(
        qwen_brain, "run_turn", lambda *a, **k: {"reply": "¿Su nombre?", "tool_events": []}
    )
    monkeypatch.setattr(metrics, "record", lambda *a, **k: recorded.append(a) or "id")
    c = TestClient(server.app)
    r = c.post("/chat", json={"messages": [{"role": "user", "content": "hola"}]})
    assert r.status_code == 200 and recorded == []
