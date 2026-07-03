"""Storage layer — Alibaba Cloud Tablestore with a zero-config in-memory fallback.

With TABLESTORE_* env set, events/bookings/callers/tenants/reminders persist to
Alibaba Cloud Tablestore (the durable, multi-tenant anchor of the deploy). Without
credentials the SAME api runs on an in-process store, so a fresh clone demos the
full product — metrics, caller memory, reminders, ROI dashboard — with zero setup.
`backend()` reports which mode is live; the dashboard surfaces it honestly.
"""
import os, json, time, uuid, functools

import tablestore
from tablestore import OTSClient, Row, Direction

TBL_EVENTS = "vx_events"
TBL_BOOKINGS = "vx_bookings"
TBL_CALLERS = "vx_callers"
TBL_TENANTS = "vx_tenants"
TBL_REMINDERS = "vx_reminders"

_ENV_KEYS = ("TABLESTORE_ENDPOINT", "TABLESTORE_ACCESS_KEY_ID",
             "TABLESTORE_ACCESS_KEY_SECRET", "TABLESTORE_INSTANCE")


def is_configured() -> bool:
    return all(os.getenv(k, "").strip() for k in _ENV_KEYS)


def backend() -> str:
    """'tablestore' when Alibaba Cloud credentials are present, else 'memory'."""
    return "tablestore" if is_configured() else "memory"


class _MemoryOTS:
    """In-process stand-in that mimics the aliyun OTSClient read/write shapes:
    get_row -> (consumed, Row|None, next_token) · get_range -> (consumed,
    next_start_pk, [Row], next_token). Lets every store call run unchanged."""

    def __init__(self):
        self.tables: dict[str, dict[tuple, list]] = {}

    def put_row(self, table, row):
        self.tables.setdefault(table, {})[tuple(row.primary_key)] = list(row.attribute_columns)

    def get_row(self, table, primary_key, *a, **k):
        cols = self.tables.get(table, {}).get(tuple(primary_key))
        row = Row(list(primary_key), cols) if cols is not None else None
        return None, row, None

    def get_range(self, table, direction, start_pk, end_pk, *a, limit=200, **k):
        # Match on the fixed (non-INF) leading pk components, e.g. the tenant.
        fixed = [(k_, v) for k_, v in start_pk
                 if v is not tablestore.INF_MIN and v is not tablestore.INF_MAX]
        rows = []
        for pk, cols in self.tables.get(table, {}).items():
            if all(item in pk for item in fixed):
                rows.append(Row(list(pk), list(cols)))
        return None, None, rows[:limit], None


@functools.lru_cache(maxsize=1)
def get_client():
    if not is_configured():
        return _MemoryOTS()
    return OTSClient(
        os.environ["TABLESTORE_ENDPOINT"],
        os.environ["TABLESTORE_ACCESS_KEY_ID"],
        os.environ["TABLESTORE_ACCESS_KEY_SECRET"],
        os.environ["TABLESTORE_INSTANCE"],
    )


def _now_ms() -> int:
    return int(time.time() * 1000)


def _attr_dict(cols) -> dict:
    """Attribute list -> dict. Written rows carry (k, v); rows read back from the
    real Tablestore carry (k, v, timestamp). Accept both."""
    return {c[0]: c[1] for c in (cols or [])}


def _extract_cols(res):
    """Pull the attribute list out of a get_row result, tolerating the real SDK
    3-tuple (consumed, Row, token), our memory clone, and simpler test fakes."""
    for x in (res if isinstance(res, tuple) else (res,)):
        if x is None:
            continue
        if hasattr(x, "attribute_columns"):
            return x.attribute_columns or []
        if isinstance(x, list) and (not x or isinstance(x[0], tuple)):
            return x
    return []


def get_attrs(table: str, primary_key: list) -> dict:
    """Read one row's attributes as a dict ({} when the row doesn't exist)."""
    res = get_client().get_row(table, primary_key, max_version=1)
    return _attr_dict(_extract_cols(res))


def put_attrs(table: str, primary_key: list, attrs: dict) -> None:
    get_client().put_row(table, Row(list(primary_key), list(attrs.items())))


def _range_rows(res) -> list:
    """Row list from a get_range result: index 2 in the real SDK 4-tuple; fall
    back to the first list element for simpler fakes."""
    if isinstance(res, tuple):
        if len(res) >= 3 and isinstance(res[2], list):
            return res[2]
        return next((x for x in res if isinstance(x, list)), [])
    return []


def _scan(table: str, tenant: str, second_pk: str, limit: int) -> list[dict]:
    start = [("tenant", tenant), (second_pk, tablestore.INF_MIN)]
    end = [("tenant", tenant), (second_pk, tablestore.INF_MAX)]
    res = get_client().get_range(table, Direction.FORWARD, start, end, limit=limit)
    return [_attr_dict(r.attribute_columns) for r in _range_rows(res)]


# ── Events (metrics / ROI feed) ──────────────────────────────────────────────

def put_event(tenant: str, call_id: str, event: dict) -> str:
    eid = uuid.uuid4().hex
    put_attrs(TBL_EVENTS, [("tenant", tenant), ("event_id", eid)],
              {"call_id": call_id, "ts": _now_ms(),
               "payload": json.dumps(event, ensure_ascii=False)})
    return eid


def list_events(tenant: str, limit: int = 200) -> list[dict]:
    out = []
    for d in _scan(TBL_EVENTS, tenant, "event_id", limit):
        try:
            d["payload"] = json.loads(d.get("payload", "{}"))
        except (json.JSONDecodeError, TypeError):
            pass
        out.append(d)
    out.sort(key=lambda d: d.get("ts", 0))
    return out


# ── Bookings ─────────────────────────────────────────────────────────────────

def put_booking(tenant: str, booking: dict) -> str:
    bid = uuid.uuid4().hex
    put_attrs(TBL_BOOKINGS, [("tenant", tenant), ("booking_id", bid)],
              {"ts": _now_ms(), "data": json.dumps(booking, ensure_ascii=False)})
    return bid


# ── Reminders (T-24h / T-1h appointment nudges) ──────────────────────────────

def put_reminder(tenant: str, reminder: dict) -> str:
    rid = reminder.get("id") or uuid.uuid4().hex
    reminder = {**reminder, "id": rid}
    put_attrs(TBL_REMINDERS, [("tenant", tenant), ("reminder_id", rid)],
              {"data": json.dumps(reminder, ensure_ascii=False)})
    return rid


def list_reminders(tenant: str, limit: int = 200) -> list[dict]:
    out = []
    for d in _scan(TBL_REMINDERS, tenant, "reminder_id", limit):
        try:
            out.append(json.loads(d.get("data", "{}")))
        except (json.JSONDecodeError, TypeError):
            continue
    out.sort(key=lambda r: r.get("send_at", 0))
    return out


def save_reminder(tenant: str, reminder: dict) -> None:
    """Overwrite a reminder row (used to persist sent=True after firing)."""
    put_attrs(TBL_REMINDERS, [("tenant", tenant), ("reminder_id", reminder["id"])],
              {"data": json.dumps(reminder, ensure_ascii=False)})
