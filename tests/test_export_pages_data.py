from datetime import datetime, timezone

from scripts.export_pages_data import next_fixture_kickoff_utc


def test_next_fixture_kickoff_utc_prefers_earliest_kickoff_datetime():
    rows = [
        {"kickoff_datetime": "2026-06-14T19:00:00+00:00"},
        {"kickoff_datetime": "2026-06-12T17:00:00+00:00"},
    ]
    assert next_fixture_kickoff_utc(rows) == "2026-06-12T17:00:00+00:00"


def test_next_fixture_kickoff_utc_falls_back_to_fixture_date():
    rows = [
        {"kickoff_datetime": None, "fixture_date": "2026-06-18"},
        {"kickoff_datetime": None, "fixture_date": "2026-06-10"},
    ]
    assert next_fixture_kickoff_utc(rows) == "2026-06-10T00:00:00+00:00"


def test_next_fixture_kickoff_utc_handles_datetime_objects():
    rows = [
        {"kickoff_datetime": datetime(2026, 6, 13, 20, 30, tzinfo=timezone.utc)},
        {"kickoff_datetime": datetime(2026, 6, 11, 18, 0, tzinfo=timezone.utc)},
    ]
    assert next_fixture_kickoff_utc(rows) == "2026-06-11T18:00:00+00:00"


def test_next_fixture_kickoff_utc_returns_none_when_no_parseable_dates():
    rows = [{"kickoff_datetime": "", "fixture_date": "not-a-date"}]
    assert next_fixture_kickoff_utc(rows) is None
