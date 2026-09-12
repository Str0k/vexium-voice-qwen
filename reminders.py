"""Appointment reminders — pure, idempotent core plus store-backed scheduling.

`reminder_times`/`run_due` are the pure core (unit-tested, scheduler-agnostic).
`schedule_for_booking` persists the T-24h/T-1h reminders when an appointment is
booked; `run_due_from_store` is what the POST /run-due-reminders endpoint (or an
Alibaba Function Compute timer in production) calls to fire whatever is due."""

import time
import uuid
from datetime import datetime

import integrations.tablestore_store as store

DAY_MS = 24 * 3600 * 1000
HOUR_MS = 3600 * 1000


def reminder_times(start_ms: int) -> list:
    """Return the two reminder send-times for an appointment: T-24h and T-1h (epoch ms)."""
    return [start_ms - DAY_MS, start_ms - HOUR_MS]


def run_due(reminders: list, now_ms: int, *, send) -> list:
    """Fire every reminder that is due (send_at <= now) and not yet sent.
    Marks each fired reminder sent=True (idempotent). Returns the fired ids.
    A send() that RAISES leaves its reminder unsent so it retries next tick."""
    fired = []
    for r in reminders:
        if not r.get("sent") and r.get("send_at", 0) <= now_ms:
            try:
                send(r)
            except Exception:  # noqa: BLE001 — failed delivery must not mark sent
                continue
            r["sent"] = True
            fired.append(r.get("id"))
    return fired


def _parse_start_ms(start_iso: str):
    s = (start_iso or "").strip().replace(" ", "T")
    for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M", "%Y-%m-%dT%H"):
        try:
            return int(datetime.strptime(s, fmt).timestamp() * 1000)
        except ValueError:
            continue
    return None


def schedule_for_booking(
    tenant: str,
    phone: str,
    service: str,
    start_iso: str,
    language: str = "es",
    now_ms: int | None = None,
) -> list:
    """Persist the T-24h and T-1h SMS reminders for a booked appointment.
    Only future send-times are stored. Returns the stored reminder dicts."""
    start_ms = _parse_start_ms(start_iso)
    if start_ms is None or not phone:
        return []
    now_ms = int(time.time() * 1000) if now_ms is None else now_ms
    body = (
        f"Recordatorio: su cita de {service} es el {start_iso.replace('T', ' a las ')}."
        if language == "es"
        else f"Reminder: your {service} appointment is on {start_iso.replace('T', ' at ')}."
    )
    stored = []
    for send_at in reminder_times(start_ms):
        if send_at <= now_ms:
            continue
        rem = {
            "id": uuid.uuid4().hex,
            "send_at": send_at,
            "sent": False,
            "phone": phone,
            "body": body,
            "service": service,
            "start": start_iso,
        }
        store.put_reminder(tenant, rem)
        stored.append(rem)
    return stored


def run_due_from_store(tenant: str, now_ms: int | None = None, *, send=None) -> list:
    """Fire every due, unsent reminder for the tenant (SMS by default), persist
    the sent flag, and return the fired ids. Safe to call on any schedule.
    An SMS provider error leaves the reminder unsent so the next tick retries;
    'skipped' (no provider configured — demo mode) counts as delivered."""
    if send is None:
        import integrations.sms as sms

        def send(r):
            res = sms.send_sms(r.get("phone", ""), r.get("body", ""))
            if res.get("status") == "error":
                raise RuntimeError(res.get("detail", "sms failed"))

    now_ms = int(time.time() * 1000) if now_ms is None else now_ms
    rems = store.list_reminders(tenant)
    fired = set(run_due(rems, now_ms, send=send))
    for r in rems:
        if r.get("id") in fired:
            store.save_reminder(tenant, r)
    return sorted(fired)
