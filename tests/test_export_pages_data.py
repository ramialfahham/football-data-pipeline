from __future__ import annotations

from datetime import datetime, timezone

from scripts import export_pages_data


class _FakeQueryJob:
    def __init__(self, rows):
        self._rows = rows

    def result(self):
        return self._rows


class _FakeClient:
    def __init__(self, rows):
        self.rows = rows
        self.sql = None
        self.job_config = None

    def query(self, sql, job_config=None):
        self.sql = sql
        self.job_config = job_config
        return _FakeQueryJob(self.rows)


def test_fetch_team_season_rows_filters_invalid_ranks() -> None:
    client = _FakeClient(
        [
            {"league_code": "L1", "team_name": "A", "latest_rank": 1},
            {"league_code": "L1", "team_name": "B", "latest_rank": 2},
        ]
    )

    rows = export_pages_data.fetch_team_season_rows(client, "L1")

    assert rows == [
        {"league_code": "L1", "team_name": "A", "latest_rank": 1},
        {"league_code": "L1", "team_name": "B", "latest_rank": 2},
    ]
    assert client.sql is not None
    assert "and latest_rank is not null" in client.sql.lower()
    assert "and latest_rank > 0" in client.sql.lower()
    assert "order by latest_rank asc, team_name asc" in client.sql.lower()


def test_next_fixture_kickoff_utc_prefers_earliest_kickoff_datetime() -> None:
    rows = [
        {"kickoff_datetime": "2026-06-14T19:00:00+00:00"},
        {"kickoff_datetime": "2026-06-12T17:00:00+00:00"},
    ]
    assert (
        export_pages_data.next_fixture_kickoff_utc(rows)
        == "2026-06-12T17:00:00+00:00"
    )


def test_next_fixture_kickoff_utc_falls_back_to_fixture_date() -> None:
    rows = [
        {"kickoff_datetime": None, "fixture_date": "2026-06-18"},
        {"kickoff_datetime": None, "fixture_date": "2026-06-10"},
    ]
    assert (
        export_pages_data.next_fixture_kickoff_utc(rows)
        == "2026-06-10T00:00:00+00:00"
    )


def test_next_fixture_kickoff_utc_handles_datetime_objects() -> None:
    rows = [
        {"kickoff_datetime": datetime(2026, 6, 13, 20, 30, tzinfo=timezone.utc)},
        {"kickoff_datetime": datetime(2026, 6, 11, 18, 0, tzinfo=timezone.utc)},
    ]
    assert (
        export_pages_data.next_fixture_kickoff_utc(rows)
        == "2026-06-11T18:00:00+00:00"
    )


def test_next_fixture_kickoff_utc_returns_none_when_no_parseable_dates() -> None:
    rows = [{"kickoff_datetime": "", "fixture_date": "not-a-date"}]
    assert export_pages_data.next_fixture_kickoff_utc(rows) is None
