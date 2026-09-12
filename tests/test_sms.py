import integrations.sms as sms


def test_send_sms_skips_without_provider(monkeypatch):
    monkeypatch.setenv("SMS_PROVIDER", "none")
    out = sms.send_sms("+17135550182", "Your appointment is confirmed")
    assert out["status"] == "skipped"


def test_send_sms_uses_injected_provider():
    calls = []

    def fake(to, body):
        calls.append((to, body))
        return {"status": "sent", "provider": "fake", "detail": "ok"}

    out = sms.send_sms("+1", "hi", provider=fake)
    assert out["status"] == "sent" and calls == [("+1", "hi")]
