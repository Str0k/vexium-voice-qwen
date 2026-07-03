"""The store must run the FULL product with zero cloud credentials (in-memory
fallback) and report its backend honestly — a fresh clone demos everything."""
import integrations.tablestore_store as store


def _fresh_memory(monkeypatch):
    for k in ("TABLESTORE_ENDPOINT", "TABLESTORE_ACCESS_KEY_ID",
              "TABLESTORE_ACCESS_KEY_SECRET", "TABLESTORE_INSTANCE"):
        monkeypatch.delenv(k, raising=False)
    store.get_client.cache_clear()


def test_backend_reports_memory_without_credentials(monkeypatch):
    _fresh_memory(monkeypatch)
    assert store.backend() == "memory"
    assert isinstance(store.get_client(), store._MemoryOTS)


def test_backend_reports_tablestore_with_credentials(monkeypatch):
    monkeypatch.setenv("TABLESTORE_ENDPOINT", "https://x.aliyuncs.com")
    monkeypatch.setenv("TABLESTORE_ACCESS_KEY_ID", "k")
    monkeypatch.setenv("TABLESTORE_ACCESS_KEY_SECRET", "s")
    monkeypatch.setenv("TABLESTORE_INSTANCE", "vx")
    assert store.backend() == "tablestore"


def test_events_round_trip_in_memory(monkeypatch):
    _fresh_memory(monkeypatch)
    store.put_event("t1", "call-1", {"type": "booking_made", "service": "Limpieza"})
    store.put_event("t1", "call-2", {"type": "call_handled"})
    store.put_event("other", "call-9", {"type": "handoff"})
    events = store.list_events("t1")
    assert len(events) == 2
    assert {e["payload"]["type"] for e in events} == {"booking_made", "call_handled"}


def test_attrs_round_trip_and_missing_row(monkeypatch):
    _fresh_memory(monkeypatch)
    pk = [("tenant", "t1"), ("phone", "+17135550182")]
    assert store.get_attrs(store.TBL_CALLERS, pk) == {}
    store.put_attrs(store.TBL_CALLERS, pk, {"profile": '{"name":"Cristian"}'})
    assert store.get_attrs(store.TBL_CALLERS, pk)["profile"] == '{"name":"Cristian"}'


def test_reminders_round_trip(monkeypatch):
    _fresh_memory(monkeypatch)
    rid = store.put_reminder("t1", {"send_at": 123, "sent": False, "phone": "+1"})
    rems = store.list_reminders("t1")
    assert len(rems) == 1 and rems[0]["id"] == rid
    rems[0]["sent"] = True
    store.save_reminder("t1", rems[0])
    assert store.list_reminders("t1")[0]["sent"] is True


def test_attr_dict_accepts_read_shape_with_timestamps():
    # Rows read back from real Tablestore carry (name, value, timestamp).
    assert store._attr_dict([("a", 1, 1234), ("b", "x", 1234)]) == {"a": 1, "b": "x"}
