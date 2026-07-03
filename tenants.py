"""Multi-tenant business config keyed by tenant id. One deploy serves many
clinics/restaurants: each tenant row overrides the defaults below. Persists to
Alibaba Cloud Tablestore when configured, in-process otherwise."""
import json
import integrations.tablestore_store as store

DEFAULT = {"name": "Vexium Dental", "deposit_amount": 40, "voice": "es",
           "hours": "Mon-Fri 9-6", "greeting": "", "services": []}


def load_tenant(tenant_id: str) -> dict:
    d = store.get_attrs(store.TBL_TENANTS, [("tenant", tenant_id)])
    if not d:
        return dict(DEFAULT)
    try:
        cfg = json.loads(d.get("config", "{}"))
    except (json.JSONDecodeError, TypeError):
        cfg = {}
    return {**DEFAULT, **cfg}


def save_tenant(tenant_id: str, config: dict) -> None:
    store.put_attrs(store.TBL_TENANTS, [("tenant", tenant_id)],
                    {"config": json.dumps(config, ensure_ascii=False)})
