import json
from tablestore import Row
import integrations.tablestore_store as store

DEFAULT = {"name": "Vexium Dental", "deposit_amount": 40, "voice": "es",
           "hours": "Mon-Fri 9-6", "greeting": "", "services": []}

def load_tenant(tenant_id: str) -> dict:
    _, cols = store.get_client().get_row(store.TBL_TENANTS, [("tenant", tenant_id)], max_version=1)
    if not cols:
        return dict(DEFAULT)
    d = {k: v for k, v in cols}
    try:
        cfg = json.loads(d.get("config", "{}"))
    except (json.JSONDecodeError, TypeError):
        cfg = {}
    return {**DEFAULT, **cfg}

def save_tenant(tenant_id: str, config: dict) -> None:
    row = Row([("tenant", tenant_id)], [("config", json.dumps(config, ensure_ascii=False))])
    store.get_client().put_row(store.TBL_TENANTS, row)
