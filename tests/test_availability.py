import clinic

def test_closed_sunday_returns_alternatives():
    # 2026-07-05 is a Sunday -> clinic closed
    r = clinic.check_availability("2026-07-05T10:00")
    assert r["available"] is False
    assert r["reason"] == "closed_day"
    assert len(r["alternatives"]) > 0

def test_free_weekday_slot_is_available():
    # 2026-07-07 Tuesday 14:00 is open and not in BUSY_WEEKLY[1]
    r = clinic.check_availability("2026-07-07T14:00")
    assert r["available"] is True
    assert "reason" not in r

def test_unparseable_datetime():
    r = clinic.check_availability("not-a-date")
    assert r["available"] is False
    assert r["reason"] == "unparseable_datetime"
