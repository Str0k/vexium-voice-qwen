import os, json, time, uuid, functools
import tablestore
from tablestore import OTSClient, Row, Direction

TBL_EVENTS, TBL_BOOKINGS, TBL_CALLERS, TBL_TENANTS = "vx_events", "vx_bookings", "vx_callers", "vx_tenants"

@functools.lru_cache(maxsize=1)
def get_client() -> OTSClient:
    return OTSClient(
        os.environ["TABLESTORE_ENDPOINT"],
        os.environ["TABLESTORE_ACCESS_KEY_ID"],
        os.environ["TABLESTORE_ACCESS_KEY_SECRET"],
        os.environ["TABLESTORE_INSTANCE"],
    )

def _now_ms() -> int:
    return int(time.time() * 1000)

def put_event(tenant: str, call_id: str, event: dict) -> str:
    eid = uuid.uuid4().hex
    pk = [("tenant", tenant), ("event_id", eid)]
    attrs = [("call_id", call_id), ("ts", _now_ms()), ("payload", json.dumps(event, ensure_ascii=False))]
    get_client().put_row(TBL_EVENTS, Row(pk, attrs))
    return eid

def put_booking(tenant: str, booking: dict) -> str:
    bid = uuid.uuid4().hex
    pk = [("tenant", tenant), ("booking_id", bid)]
    attrs = [("ts", _now_ms()), ("data", json.dumps(booking, ensure_ascii=False))]
    get_client().put_row(TBL_BOOKINGS, Row(pk, attrs))
    return bid

def list_events(tenant: str, limit: int = 200) -> list[dict]:
    start = [("tenant", tenant), ("event_id", tablestore.INF_MIN)]
    end = [("tenant", tenant), ("event_id", tablestore.INF_MAX)]
    result = get_client().get_range(TBL_EVENTS, Direction.FORWARD, start, end, limit=limit)
    # tablestore get_range returns a tuple; the row list is the element that is a list.
    rows = next((x for x in result if isinstance(x, list)), []) if isinstance(result, tuple) else []
    out = []
    for r in rows or []:
        d = {k: v for k, v in r.attribute_columns}
        try:
            d["payload"] = json.loads(d.get("payload", "{}"))
        except (json.JSONDecodeError, TypeError):
            pass
        out.append(d)
    return out
