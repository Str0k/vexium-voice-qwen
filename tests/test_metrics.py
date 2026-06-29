import metrics, integrations.tablestore_store as store

def test_summary_aggregates(monkeypatch):
    fake = []
    monkeypatch.setattr(store, "put_event", lambda t, c, e: fake.append(e) or "id")
    monkeypatch.setattr(store, "list_events", lambda t, limit=200: [{"payload": e} for e in fake])
    metrics.record("t1", "c1", "booking_made")
    metrics.record("t1", "c1", "deposit_collected", amount_usd=40)
    metrics.record("t1", "c2", "call_handled")
    s = metrics.summary("t1")
    assert s["bookings"] == 1 and s["revenue_usd"] == 40 and s["calls"] == 1
