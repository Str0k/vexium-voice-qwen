"""Reminders end-to-end on the store: booking schedules T-24h/T-1h, the
/run-due-reminders path fires exactly what is due, idempotently."""
import time
from datetime import datetime

import reminders
import integrations.tablestore_store as store


def _fresh_memory(monkeypatch):
    for k in ("TABLESTORE_ENDPOINT", "TABLESTORE_ACCESS_KEY_ID",
              "TABLESTORE_ACCESS_KEY_SECRET", "TABLESTORE_INSTANCE"):
        monkeypatch.delenv(k, raising=False)
    store.get_client.cache_clear()


def test_schedule_then_fire_due_only_once(monkeypatch):
    _fresh_memory(monkeypatch)
    now = int(time.time() * 1000)
    start_ms = now + 30 * 3600 * 1000  # appointment 30h out -> both reminders future
    start_iso = datetime.fromtimestamp(start_ms / 1000).strftime("%Y-%m-%dT%H:%M")

    stored = reminders.schedule_for_booking("t1", "+17135550182", "Limpieza", start_iso)
    assert len(stored) == 2 and all(not r["sent"] for r in stored)
    assert "Limpieza" in stored[0]["body"]

    sent = []
    # 7h later: the T-24h reminder (due at ~+6h) fires; the T-1h one doesn't.
    fired = reminders.run_due_from_store("t1", now + 7 * 3600 * 1000,
                                         send=lambda r: sent.append(r["phone"]))
    assert len(fired) == 1 and sent == ["+17135550182"]

    # Same moment again: idempotent, nothing re-fires.
    fired2 = reminders.run_due_from_store("t1", now + 7 * 3600 * 1000,
                                          send=lambda r: sent.append(r["phone"]))
    assert fired2 == [] and len(sent) == 1


def test_unparseable_datetime_or_no_phone_stores_nothing(monkeypatch):
    _fresh_memory(monkeypatch)
    assert reminders.schedule_for_booking("t1", "+1", "X", "next tuesday-ish") == []
    assert reminders.schedule_for_booking("t1", "", "X", "2030-01-01T10:00") == []
    assert store.list_reminders("t1") == []
