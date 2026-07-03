"""Regression tests for the adversarial-review fixes."""
import json
import types

import evaluation
import qwen_brain
import reminders
import restaurant
import integrations.tablestore_store as store


# ── Judge robustness: fenced / prose-wrapped JSON must still parse ───────────

class _Msg:
    def __init__(self, content):
        self.content = content
class _Resp:
    def __init__(self, content):
        self.choices = [types.SimpleNamespace(message=_Msg(content))]
class _FencedJudge:
    def __init__(self, content):
        self._content = content
        self.chat = types.SimpleNamespace(completions=types.SimpleNamespace(
            create=lambda **kw: _Resp(self._content)))


def test_judge_parses_fenced_json():
    fenced = "```json\n{\"task_completion\": 95, \"tool_accuracy\": 88, " \
             "\"hallucination\": false, \"notes\": \"solid\"}\n```"
    out = evaluation.score_call("user: hola", [], client=_FencedJudge(fenced))
    assert out["task_completion"] == 95 and out["tool_accuracy"] == 88


def test_judge_parses_json_with_prose():
    wrapped = "Here is my verdict: {\"task_completion\": 70, \"tool_accuracy\": 60, " \
              "\"hallucination\": true, \"notes\": \"x\"} — done."
    out = evaluation.score_call("user: hola", [], client=_FencedJudge(wrapped))
    assert out["task_completion"] == 70 and out["hallucination"] is True


# ── Text mode threads tenant/call_id into every tool call ────────────────────

def test_run_turn_injects_extra_args(monkeypatch):
    captured = {}

    def fake_handle(vertical, name, args):
        captured.update(args)
        return {"ok": True}

    monkeypatch.setattr(qwen_brain, "handle_function", fake_handle)

    class _Call:
        def __init__(self):
            self.id = "c1"
            self.function = types.SimpleNamespace(
                name="check_availability", arguments=json.dumps({"requested_datetime": "2026-07-08T10:00"}))

    class _ToolMsg:
        content = ""
        tool_calls = [_Call()]

    class _TextMsg:
        content = "Listo."
        tool_calls = []

    class _Client:
        def __init__(self):
            self._step = 0
            self.chat = types.SimpleNamespace(completions=types.SimpleNamespace(create=self._create))
        def _create(self, **kw):
            self._step += 1
            msg = _ToolMsg() if self._step == 1 else _TextMsg()
            return types.SimpleNamespace(choices=[types.SimpleNamespace(message=msg)])

    out = qwen_brain.run_turn([{"role": "user", "content": "hola"}], [], "dental",
                              client=_Client(), extra_args={"tenant": "dental", "call_id": "call-42"})
    assert out["reply"] == "Listo."
    assert captured["tenant"] == "dental" and captured["call_id"] == "call-42"


# ── Failed SMS delivery must NOT mark a reminder sent ─────────────────────────

def _fresh_memory(monkeypatch):
    for k in ("TABLESTORE_ENDPOINT", "TABLESTORE_ACCESS_KEY_ID",
              "TABLESTORE_ACCESS_KEY_SECRET", "TABLESTORE_INSTANCE"):
        monkeypatch.delenv(k, raising=False)
    store.get_client.cache_clear()


def test_failed_send_retries_next_tick(monkeypatch):
    _fresh_memory(monkeypatch)
    store.put_reminder("t1", {"send_at": 10, "sent": False, "phone": "+1", "body": "hi"})

    def failing(r):
        raise RuntimeError("provider down")
    assert reminders.run_due_from_store("t1", 999, send=failing) == []
    assert store.list_reminders("t1")[0]["sent"] is False  # still pending

    sent = []
    fired = reminders.run_due_from_store("t1", 999, send=lambda r: sent.append(r["id"]))
    assert len(fired) == 1 and store.list_reminders("t1")[0]["sent"] is True


# ── Restaurant reservations count on the dashboard like dental bookings ──────

def test_book_reservation_records_metric(monkeypatch):
    recorded = []
    import metrics
    monkeypatch.setattr(metrics, "record", lambda *a, **k: recorded.append((a, k)) or "id")
    import memory
    monkeypatch.setattr(memory, "append_interaction", lambda *a, **k: None)
    monkeypatch.setattr(reminders, "schedule_for_booking", lambda *a, **k: [])
    r = restaurant.book_reservation(caller_name="Ana", phone="+1", party_size=4,
                                    reservation_datetime="2026-07-10T19:00",
                                    tenant="restaurant", call_id="c9")
    assert r["status"] == "confirmed"
    assert recorded and recorded[0][0][:3] == ("restaurant", "c9", "booking_made")


# ── Tablestore pagination: _scan follows the continuation key ─────────────────

def test_scan_follows_next_start_primary_key(monkeypatch):
    from tablestore import Row

    class PagedOTS:
        def __init__(self):
            self.calls = 0
        def get_range(self, table, direction, start, end, *a, limit=200, **k):
            self.calls += 1
            if self.calls == 1:
                rows = [Row([("tenant", "t1"), ("event_id", "a")], [("payload", "{}"), ("ts", 1)])]
                return None, [("tenant", "t1"), ("event_id", "a")], rows, None
            rows = [Row([("tenant", "t1"), ("event_id", "b")], [("payload", "{}"), ("ts", 2)])]
            return None, None, rows, None

    paged = PagedOTS()
    monkeypatch.setattr(store, "get_client", lambda: paged)
    events = store.list_events("t1")
    assert len(events) == 2 and paged.calls == 2
