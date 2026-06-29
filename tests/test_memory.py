import memory, integrations.tablestore_store as store

class FakeOTS:
    def __init__(self): self.db = {}
    def put_row(self, table, row):
        pk = tuple(row.primary_key); self.db[pk] = row.attribute_columns
    def get_row(self, table, pk, *a, **k):
        key = tuple(pk); cols = self.db.get(key)
        return (None, None) if cols is None else (None, list(cols))

def test_round_trip_profile(monkeypatch):
    fake = FakeOTS()
    monkeypatch.setattr(store, "get_client", lambda: fake)
    assert memory.get_caller_profile("t1", "+17135550182") is None
    memory.save_caller_profile("t1", "+17135550182", {"name": "Cristian", "lang": "es"})
    p = memory.get_caller_profile("t1", "+17135550182")
    assert p["name"] == "Cristian" and p["lang"] == "es"
