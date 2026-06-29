import json
from tablestore import Row
import integrations.tablestore_store as store

def _pk(tenant: str, phone: str):
    return [("tenant", tenant), ("phone", phone)]

def get_caller_profile(tenant: str, phone: str):
    _, cols = store.get_client().get_row(store.TBL_CALLERS, _pk(tenant, phone), max_version=1)
    if not cols:
        return None
    d = {k: v for k, v in cols}
    try:
        return json.loads(d.get("profile", "{}"))
    except (json.JSONDecodeError, TypeError):
        return None

def save_caller_profile(tenant: str, phone: str, profile: dict) -> None:
    row = Row(_pk(tenant, phone), [("profile", json.dumps(profile, ensure_ascii=False))])
    store.get_client().put_row(store.TBL_CALLERS, row)

def append_interaction(tenant: str, phone: str, summary: str) -> None:
    prof = get_caller_profile(tenant, phone) or {}
    history = prof.get("history", [])
    history.append(summary)
    prof["history"] = history[-10:]
    save_caller_profile(tenant, phone, prof)
