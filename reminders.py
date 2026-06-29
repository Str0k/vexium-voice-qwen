"""Appointment-reminder core. Live scheduling (APScheduler), persistence, the
/run-due-reminders endpoint, the Alibaba FC timer, and Cal.com webhooks are
wired in the deploy phase. This module is the pure, idempotent core."""

DAY_MS = 24 * 3600 * 1000
HOUR_MS = 3600 * 1000

def reminder_times(start_ms: int) -> list:
    """Return the two reminder send-times for an appointment: T-24h and T-1h (epoch ms)."""
    return [start_ms - DAY_MS, start_ms - HOUR_MS]

def run_due(reminders: list, now_ms: int, *, send) -> list:
    """Fire every reminder that is due (send_at <= now) and not yet sent.
    Marks each fired reminder sent=True (idempotent). Returns the fired ids."""
    fired = []
    for r in reminders:
        if not r.get("sent") and r.get("send_at", 0) <= now_ms:
            send(r)
            r["sent"] = True
            fired.append(r.get("id"))
    return fired
