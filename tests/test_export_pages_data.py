from __future__ import annotations

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
