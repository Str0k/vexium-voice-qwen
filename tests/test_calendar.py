import respx, httpx, integrations.calendar_calcom as cal

@respx.mock
def test_create_booking_success(monkeypatch):
    monkeypatch.setenv("CALCOM_API_KEY", "cal_test")
    monkeypatch.setenv("CALCOM_EVENT_TYPE_ID", "123")
    respx.post("https://api.cal.com/v2/bookings").mock(
        return_value=httpx.Response(201, json={"data": {"uid": "bk_abc", "start": "2026-07-07T14:00:00Z"}}))
    out = cal.create_booking("2026-07-07T14:00:00Z", "Cristian", "+17135550182", "Limpieza")
    assert out["status"] == "booked"
    assert out["booking_uid"] == "bk_abc"
