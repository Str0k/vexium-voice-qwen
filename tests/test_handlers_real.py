import clinic, integrations.calendar_calcom as cal, integrations.payments_stripe as pay
import integrations.sms as sms, metrics, memory

def test_book_appointment_makes_real_booking(monkeypatch):
    monkeypatch.setattr(cal, "create_booking", lambda *a, **k: {"status": "booked", "booking_uid": "bk_1", "start": a[0]})
    monkeypatch.setattr(metrics, "record", lambda *a, **k: "e1")
    monkeypatch.setattr(memory, "append_interaction", lambda *a, **k: None)
    r = clinic.book_appointment(caller_name="Cristian", phone="+17135550182",
                                service="Limpieza", preferred_datetime="2026-07-07T14:00:00Z")
    assert r["status"] == "confirmed" and r["booking_uid"] == "bk_1"

def test_take_deposit_sends_link(monkeypatch):
    monkeypatch.setattr(pay, "create_deposit_link", lambda *a, **k: {"url": "https://pay", "session_id": "cs_1"})
    sent = {}
    monkeypatch.setattr(sms, "send_sms", lambda to, body, **k: sent.update(to=to, body=body) or {"status": "sent"})
    monkeypatch.setattr(metrics, "record", lambda *a, **k: "e1")
    r = clinic.take_deposit(amount_usd=40, service="Ortodoncia", phone="+17135550182")
    assert r["status"] == "link_sent" and "https://pay" in sent["body"]
