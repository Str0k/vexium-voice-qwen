import os, httpx

API = "https://api.cal.com/v2/bookings"

def create_booking(start_iso: str, name: str, phone: str, notes: str, *, http=None) -> dict:
    if not (os.getenv("CALCOM_API_KEY", "").strip() and os.getenv("CALCOM_EVENT_TYPE_ID", "").strip()):
        # Demo mode — no Cal.com credentials: succeed locally, honestly labeled, so a
        # fresh clone still completes the whole booking flow end-to-end.
        return {"status": "simulated", "booking_uid": "", "start": start_iso}
    headers = {"Authorization": f"Bearer {os.environ['CALCOM_API_KEY']}",
               "cal-api-version": "2024-08-13", "Content-Type": "application/json"}
    payload = {
        "eventTypeId": int(os.environ["CALCOM_EVENT_TYPE_ID"]),
        "start": start_iso,
        "attendee": {"name": name, "phoneNumber": phone, "timeZone": "America/Chicago", "language": "es"},
        "metadata": {"notes": notes},
    }
    client = http or httpx.Client(timeout=10)
    try:
        r = client.post(API, json=payload, headers=headers)
        if r.status_code in (200, 201):
            d = r.json().get("data", {})
            return {"status": "booked", "booking_uid": d.get("uid", ""), "start": d.get("start", start_iso)}
        return {"status": "error", "detail": f"calcom {r.status_code}: {r.text[:200]}"}
    except Exception as exc:
        return {"status": "error", "detail": str(exc)}
