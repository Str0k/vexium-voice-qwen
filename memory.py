"""Cross-session caller memory keyed by (tenant, phone) — a returning patient is
greeted by name and history. Persists to Alibaba Cloud Tablestore when configured,
in-process otherwise (see integrations.tablestore_store)."""
import json
import integrations.tablestore_store as store


def _pk(tenant: str, phone: str):
    return [("tenant", tenant), ("phone", phone)]


def get_caller_profile(tenant: str, phone: str):
    d = store.get_attrs(store.TBL_CALLERS, _pk(tenant, phone))
    if not d:
        return None
    try:
        return json.loads(d.get("profile", "{}"))
    except (json.JSONDecodeError, TypeError):
        return None


def save_caller_profile(tenant: str, phone: str, profile: dict) -> None:
    store.put_attrs(store.TBL_CALLERS, _pk(tenant, phone),
                    {"profile": json.dumps(profile, ensure_ascii=False)})


def append_interaction(tenant: str, phone: str, summary: str) -> None:
    prof = get_caller_profile(tenant, phone) or {}
    history = prof.get("history", [])
    history.append(summary)
    prof["history"] = history[-10:]
    save_caller_profile(tenant, phone, prof)
