import tenants, integrations.tablestore_store as store

def test_default_when_missing(monkeypatch):
    monkeypatch.setattr(store, "get_client", lambda: type("F", (), {"get_row": lambda *a, **k: (None, None)})())
    t = tenants.load_tenant("unknown")
    assert t["name"] and "deposit_amount" in t

def test_stored_config_overrides_default(monkeypatch):
    saved = {}
    class F:
        def put_row(self, table, row): saved["row"] = row
        def get_row(self, *a, **k):
            import json
            return (None, [("config", json.dumps({"name": "Bright Smile", "deposit_amount": 50}))])
    monkeypatch.setattr(store, "get_client", lambda: F())
    t = tenants.load_tenant("bright-smile")
    assert t["name"] == "Bright Smile" and t["deposit_amount"] == 50
