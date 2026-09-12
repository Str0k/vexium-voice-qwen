import integrations.tablestore_store as store


class FakeOTS:
    def __init__(self):
        self.rows = []

    def put_row(self, table, row):
        self.rows.append((table, row))
        return None

    def get_range(self, *a, **k):
        return None, [], None


def test_put_event_returns_id(monkeypatch):
    monkeypatch.setattr(store, "get_client", lambda: FakeOTS())
    eid = store.put_event("bright-smile", "call-1", {"type": "booking_made", "amount": 0})
    assert isinstance(eid, str) and len(eid) > 0
