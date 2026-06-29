import reminders

def test_reminder_times_are_24h_and_1h_before():
    start = 1_000_000_000_000  # arbitrary epoch ms
    t = reminders.reminder_times(start)
    assert t == [start - 24*3600*1000, start - 3600*1000]
    assert t[0] < t[1] < start

def test_run_due_fires_due_unsent_only_and_is_idempotent():
    now = 1_000_000_000
    rems = [
        {"id": "a", "send_at": now - 1, "sent": False},
        {"id": "b", "send_at": now + 10_000, "sent": False},
        {"id": "c", "send_at": now - 5, "sent": True},
    ]
    fired = []
    out = reminders.run_due(rems, now, send=lambda r: fired.append(r["id"]))
    assert out == ["a"] and fired == ["a"]
    assert rems[0]["sent"] is True
    # second run: nothing re-fires
    fired2 = []
    out2 = reminders.run_due(rems, now, send=lambda r: fired2.append(r["id"]))
    assert out2 == [] and fired2 == []
