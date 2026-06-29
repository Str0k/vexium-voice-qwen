import integrations.tablestore_store as store

def record(tenant: str, call_id: str, kind: str, **fields) -> str:
    return store.put_event(tenant, call_id, {"type": kind, **fields})

def summary(tenant: str) -> dict:
    events = [e.get("payload", {}) for e in store.list_events(tenant)]
    return {
        "bookings": sum(1 for e in events if e.get("type") == "booking_made"),
        "revenue_usd": float(sum(e.get("amount_usd", 0) for e in events if e.get("type") == "deposit_collected")),
        "calls": sum(1 for e in events if e.get("type") == "call_handled"),
        "handoffs": sum(1 for e in events if e.get("type") == "handoff"),
        "after_hours": sum(1 for e in events if e.get("type") == "after_hours"),
    }
