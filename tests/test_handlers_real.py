import clinic
import integrations.calendar_calcom as cal
import integrations.payments_stripe as pay
import integrations.sms as sms
import memory
import metrics


def test_book_appointment_makes_real_booking(monkeypatch):
    monkeypatch.setattr(
        cal,
        "create_booking",
        lambda *a, **k: {"status": "booked", "booking_uid": "bk_1", "start": a[0]},
    )
    monkeypatch.setattr(metrics, "record", lambda *a, **k: "e1")
    monkeypatch.setattr(memory, "append_interaction", lambda *a, **k: None)
    r = clinic.book_appointment(
        caller_name="Cristian",
        phone="+17135550182",
        service="Limpieza",
        preferred_datetime="2026-07-07T14:00:00Z",
    )
    assert r["status"] == "confirmed" and r["booking_uid"] == "bk_1"


def test_take_deposit_sends_link(monkeypatch):
    monkeypatch.setattr(
        pay, "create_deposit_link", lambda *a, **k: {"url": "https://pay", "session_id": "cs_1"}
    )
    sent = {}
    monkeypatch.setattr(
        sms, "send_sms", lambda to, body, **k: sent.update(to=to, body=body) or {"status": "sent"}
    )
    monkeypatch.setattr(metrics, "record", lambda *a, **k: "e1")
    r = clinic.take_deposit(amount_usd=40, service="Ortodoncia", phone="+17135550182")
    assert r["status"] == "link_sent" and "https://pay" in sent["body"]


def test_book_appointment_simulated_without_calcom(monkeypatch):
    """A fresh clone (zero keys) still completes the whole booking flow."""
    monkeypatch.delenv("CALCOM_API_KEY", raising=False)
    monkeypatch.delenv("CALCOM_EVENT_TYPE_ID", raising=False)
    monkeypatch.setattr(metrics, "record", lambda *a, **k: "e1")
    monkeypatch.setattr(memory, "append_interaction", lambda *a, **k: None)
    r = clinic.book_appointment(
        caller_name="Ana",
        phone="+17135550000",
        service="Limpieza",
        preferred_datetime="2026-07-08T15:00",
    )
    assert r["status"] == "confirmed" and r["calendar"] == "simulated"
    assert r["confirmation_code"].startswith("VX-")


def test_take_deposit_simulated_without_stripe(monkeypatch):
    monkeypatch.delenv("STRIPE_API_KEY", raising=False)
    monkeypatch.setattr(sms, "send_sms", lambda *a, **k: {"status": "skipped"})
    monkeypatch.setattr(metrics, "record", lambda *a, **k: "e1")
    r = clinic.take_deposit(amount_usd=40, service="Ortodoncia", phone="+17135550000")
    assert r["status"] == "link_sent" and r["payments"] == "simulated"
