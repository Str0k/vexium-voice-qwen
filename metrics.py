"""Per-tenant call metrics on the event store: record() appends an event,
summary() aggregates the live ROI numbers plus the Qwen-as-judge quality scores
that the dashboard streams over SSE."""
import integrations.tablestore_store as store


def record(tenant: str, call_id: str, kind: str, **fields) -> str:
    return store.put_event(tenant, call_id, {"type": kind, **fields})


def summary(tenant: str) -> dict:
    events = [e.get("payload", {}) for e in store.list_events(tenant)]
    scored = [e for e in events if e.get("type") == "call_scored"]

    def _avg(key):
        vals = [e.get(key) for e in scored if isinstance(e.get(key), (int, float))]
        return round(sum(vals) / len(vals)) if vals else None

    return {
        "bookings": sum(1 for e in events if e.get("type") == "booking_made"),
        "revenue_usd": float(sum(e.get("amount_usd", 0) for e in events if e.get("type") == "deposit_collected")),
        "deposits_pending_usd": float(sum(e.get("amount_usd", 0) for e in events if e.get("type") == "deposit_pending")),
        "calls": sum(1 for e in events if e.get("type") == "call_handled"),
        "handoffs": sum(1 for e in events if e.get("type") == "handoff"),
        "after_hours": sum(1 for e in events if e.get("type") == "after_hours"),
        "reminders_sent": sum(1 for e in events if e.get("type") == "reminder_sent"),
        "scored_calls": len(scored),
        "avg_task_completion": _avg("task_completion"),
        "avg_tool_accuracy": _avg("tool_accuracy"),
        "hallucinations": sum(1 for e in scored if e.get("hallucination")),
    }
