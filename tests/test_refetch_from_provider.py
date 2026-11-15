"""Tests for scripts/refetch_from_provider.py. No network, no BigQuery."""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from ingestion.api_football import http_client
from ingestion.api_football import quota as errors_quota
from scripts import refetch_from_provider as refetch

HOME, AWAY = 10, 20


def _lineup(starters: int = 11, team: int = HOME) -> dict:
    return {"team": {"id": team}, "startXI": [{"player": {"id": i}} for i in range(starters)], "substitutes": []}


def _player(conceded=None) -> dict:
    return {"player": {"id": 1}, "statistics": [{"goals": {"conceded": conceded}}]}


def _fixture(
    fid: int = 1,
    events: int = 5,
    players: tuple[int, int] = (15, 15),
    statistics: tuple[int, int] = (8, 8),
    conceded=0,
    lineups=None,
) -> dict:
    return {
        "fixture": {"id": fid},
        "events": [{}] * events,
        "players": [
            {"team": {"id": HOME}, "players": [_player(conceded)] * players[0]},
            {"team": {"id": AWAY}, "players": [_player(conceded)] * players[1]},
        ],
        "statistics": [
            {"team": {"id": HOME}, "statistics": [{}] * statistics[0]},
            {"team": {"id": AWAY}, "statistics": [{}] * statistics[1]},
        ],
        "lineups": lineups if lineups is not None else [_lineup(team=HOME), _lineup(team=AWAY)],
    }


def _stored(
    events: int = 5,
    players: tuple[int, int] = (15, 15),
    statistics: tuple[int, int] = (8, 8),
    complete: bool = True,
    starters: tuple[int, int] | None = None,
) -> dict:
    return {
        "events": events,
        "players_by_team": {HOME: players[0], AWAY: players[1]},
        "statistics_by_team": {HOME: statistics[0], AWAY: statistics[1]},
        "starters_by_team": {} if starters is None else {HOME: starters[0], AWAY: starters[1]},
        "players_complete": complete,
    }


@pytest.fixture(autouse=True)
def _reset_quota_flag(monkeypatch):
    monkeypatch.setattr(errors_quota, "_http_quota_exhausted", False)


class TestPayloadCounts:
    def test_counts_every_section_per_team(self):
        lineups = [_lineup(team=HOME), _lineup(10, team=AWAY)]
        counts = refetch.payload_counts(
            _fixture(events=7, players=(16, 15), statistics=(17, 16), lineups=lineups)
        )
        assert counts == {
            "events": 7,
            "players_by_team": {HOME: 16, AWAY: 15},
            "players_complete": True,
            "statistics_by_team": {HOME: 17, AWAY: 16},
            "starters_by_team": {HOME: 11, AWAY: 10},
        }

    def test_incomplete_player_format(self):
        assert not refetch.payload_counts(_fixture(conceded=None))["players_complete"]

    def test_empty_payload(self):
        counts = refetch.payload_counts({})
        assert counts["events"] == 0
        assert counts["players_by_team"] == counts["statistics_by_team"] == counts["starters_by_team"] == {}


def _empty_stored() -> dict:
    return {
        "events": 0,
        "players_by_team": {},
        "statistics_by_team": {},
        "starters_by_team": {},
        "players_complete": False,
    }


class TestRefusalReasons:
    def test_not_worse_and_gaining_line_ups_is_written(self):
        assert refetch.refusal_reasons(refetch.payload_counts(_fixture()), _stored()) == []

    def test_an_answer_equal_to_the_stored_data_is_not_written(self):
        new = refetch.payload_counts(_fixture(lineups=[]))
        assert refetch.refusal_reasons(new, _stored()) == ["adds nothing a stored fetch lacks"]

    def test_team_stats_without_line_ups_are_written(self):
        new = refetch.payload_counts(_fixture(events=1, players=(0, 0), statistics=(16, 16), lineups=[]))
        stored = {**_empty_stored(), "events": 1}
        assert refetch.refusal_reasons(new, stored) == []

    def test_player_rows_without_line_ups_are_written(self):
        new = refetch.payload_counts(_fixture(players=(20, 20), lineups=[]))
        assert refetch.refusal_reasons(new, _stored(players=(0, 0), complete=False)) == []

    def test_gaining_the_complete_player_format_is_written(self):
        new = refetch.payload_counts(_fixture(lineups=[]))
        assert refetch.refusal_reasons(new, _stored(complete=False)) == []

    def test_an_empty_answer_for_an_empty_match_is_not_written(self):
        new = refetch.payload_counts(_fixture(events=0, players=(0, 0), statistics=(0, 0), lineups=[]))
        assert refetch.refusal_reasons(new, _empty_stored()) == ["adds nothing a stored fetch lacks"]

    def test_a_match_never_stored_is_written(self):
        assert refetch.refusal_reasons(refetch.payload_counts(_fixture(lineups=[])), None) == []

    @pytest.mark.parametrize(
        "fixture_kwargs, stored_kwargs, reason",
        [
            ({"events": 4}, {"events": 5}, "fewer events (4 < 5)"),
            ({"players": (14, 15)}, {}, f"fewer player rows for team {HOME} (14 < 15)"),
            ({"statistics": (8, 7)}, {}, f"fewer statistics lines for team {AWAY} (7 < 8)"),
            ({"conceded": None}, {"complete": True}, "loses the complete player format"),
            (
                {"lineups": [_lineup(10, team=HOME), _lineup(team=AWAY)]},
                {"starters": (11, 11)},
                f"fewer starters for team {HOME} (10 < 11)",
            ),
        ],
    )
    def test_a_worse_fetch_is_refused(self, fixture_kwargs, stored_kwargs, reason):
        new = refetch.payload_counts(_fixture(**fixture_kwargs))
        assert refetch.refusal_reasons(new, _stored(**stored_kwargs)) == [reason]

    def test_losing_the_stored_line_ups_is_refused(self):
        new = refetch.payload_counts(_fixture(statistics=(20, 20), lineups=[]))
        assert refetch.refusal_reasons(new, _stored(starters=(11, 11))) == [
            f"fewer starters for team {HOME} (0 < 11)",
            f"fewer starters for team {AWAY} (0 < 11)",
        ]

    def test_one_team_gaining_does_not_cover_the_other_losing(self):
        new = refetch.payload_counts(_fixture(statistics=(0, 20)))
        assert refetch.refusal_reasons(new, _stored()) == [f"fewer statistics lines for team {HOME} (0 < 8)"]

    def test_more_of_everything_is_written(self):
        new = refetch.payload_counts(_fixture(events=9, players=(20, 20), statistics=(17, 17)))
        assert refetch.refusal_reasons(new, _stored()) == []


_SAMPLE_PATH = Path(__file__).parent / "fixtures" / "apif" / "fixture_details_sample.json"


def _sample(fixture_id: int) -> dict:
    response = json.loads(_SAMPLE_PATH.read_text(encoding="utf-8"))["response"]
    return next(fx for fx in response if fx["fixture"]["id"] == fixture_id)


class TestProviderSample:
    def test_a_match_with_every_section(self):
        counts = refetch.payload_counts(_sample(1507045))
        assert counts == {
            "events": 3,
            "players_by_team": {2746: 2, 2759: 2},
            "players_complete": False,
            "statistics_by_team": {2746: 3, 2759: 3},
            "starters_by_team": {2746: 3, 2759: 3},
        }

    def test_a_line_up_block_without_starters_counts_none(self):
        counts = refetch.payload_counts(_sample(1619071))
        assert counts["starters_by_team"] == {1040: 0}
        assert counts["players_by_team"] == {}
        assert counts["statistics_by_team"] == {26759: 3, 1040: 3}

    def test_team_stats_for_a_match_without_line_ups_are_written(self):
        stored = {**_empty_stored(), "events": 3}
        assert refetch.refusal_reasons(refetch.payload_counts(_sample(1619071)), stored) == []

    def test_team_stats_for_a_match_without_player_rows_are_written(self):
        stored = {**_empty_stored(), "events": 3, "starters_by_team": {1334: 3, 1370: 3}}
        assert refetch.refusal_reasons(refetch.payload_counts(_sample(1646794)), stored) == []

    def test_the_same_answer_again_is_not_written(self):
        counts = refetch.payload_counts(_sample(1507045))
        stored = {key: counts[key] for key in _empty_stored()}
        assert refetch.refusal_reasons(counts, stored) == ["adds nothing a stored fetch lacks"]


class TestPlan:
    def test_fixture_calls_are_twenty_a_call_per_competition(self):
        assert refetch.fixture_calls({"BL1": list(range(21)), "PL": list(range(20))}) == 3

    def test_squad_calls_are_pages_per_team_season(self):
        assert refetch.squad_calls({("BL1", 2016): {1, 2}, ("PL", 2026): {3}}, 3) == 9

    def test_reads_and_groups_the_lists(self, tmp_path):
        ids = tmp_path / "ids.csv"
        ids.write_text("league_code,fixture_id\nPL,3\nBL1,2\nPL,1\nPL,3\n", encoding="utf-8")
        assert refetch.read_fixture_list(str(ids)) == {"BL1": [2], "PL": [1, 3]}
        pairs = tmp_path / "pairs.csv"
        pairs.write_text("league_code,team_id,season\nBL1,5,2016\nBL1,6,2016\nPL,7,2026\n", encoding="utf-8")
        assert refetch.read_pair_list(str(pairs)) == {("BL1", 2016): {5, 6}, ("PL", 2026): {7}}

    def test_plan_mode_makes_no_call(self, tmp_path, capsys):
        ids = tmp_path / "ids.csv"
        ids.write_text("league_code,fixture_id\nPL,1\nPL,2\n", encoding="utf-8")
        with patch.object(refetch.http_client.requests, "get") as get, patch.object(refetch.bigquery, "Client") as client:
            assert refetch.main(["fixtures", "--ids-file", str(ids)]) == 0
        get.assert_not_called()
        client.assert_not_called()
        assert "plan: 2 matches in 1 competitions, 1 calls" in capsys.readouterr().out

    def test_run_needs_a_call_cap(self, tmp_path):
        ids = tmp_path / "ids.csv"
        ids.write_text("league_code,fixture_id\nPL,1\n", encoding="utf-8")
        with pytest.raises(SystemExit):
            refetch.main(["fixtures", "--ids-file", str(ids), "--run"])


class TestNightlyWindow:
    @pytest.mark.parametrize("hour, refused", [(1, False), (2, True), (3, True), (4, False), (23, False)])
    def test_refuses_two_hours_before_the_nightly(self, hour, refused):
        assert refetch.too_close_to_nightly(datetime(2026, 10, 12, hour, 30, tzinfo=timezone.utc)) is refused

    def test_the_lease_ends_before_the_nightly(self):
        latest_start = datetime(2026, 10, 12, 1, 59, tzinfo=timezone.utc)
        assert latest_start + timedelta(minutes=refetch.LEASE_MINUTES) < datetime(2026, 10, 12, 4, 0, tzinfo=timezone.utc)
        assert refetch.CALL_WINDOW_MINUTES < refetch.LEASE_MINUTES


class TestCallCounter:
    def test_makes_no_call_past_the_cap(self, monkeypatch):
        real_get = MagicMock(return_value="response")
        monkeypatch.setattr(refetch.http_client.requests, "get", real_get)
        counter = refetch.CallCounter(2)
        assert counter.get("a") == "response"
        assert counter.get("b") == "response"
        capped = counter.get("c")
        assert real_get.call_count == 2
        assert counter.calls == 2
        assert errors_quota._http_quota_exhausted
        assert capped.json()["response"] == []
        assert capped.json()["errors"]

    def test_makes_no_call_past_the_deadline(self, monkeypatch):
        real_get = MagicMock(return_value="response")
        monkeypatch.setattr(refetch.http_client.requests, "get", real_get)
        counter = refetch.CallCounter(100, datetime.now(timezone.utc) - timedelta(seconds=1))
        counter.get("a")
        real_get.assert_not_called()
        assert errors_quota._http_quota_exhausted

    def test_through_fetch_json_a_retry_counts_and_the_capped_answer_is_incomplete(self, monkeypatch):
        monkeypatch.setattr(http_client, "_throttle", lambda: None)
        monkeypatch.setattr(http_client.time, "sleep", lambda s: None)
        rate_limited = MagicMock(status_code=429, headers={"Retry-After": "0"})
        ok = MagicMock(status_code=200, headers={})
        ok.json.return_value = {"errors": [], "response": [{"fixture": {"id": 1}}]}
        real_get = MagicMock(side_effect=[rate_limited, ok])
        monkeypatch.setattr(http_client.requests, "get", real_get)
        counter = refetch.CallCounter(2)
        monkeypatch.setattr(http_client.requests, "get", counter.get)
        first = http_client.fetch_json("/fixtures", headers={}, params={"ids": "1"})
        assert counter.calls == 2
        assert http_client.result_is_complete(first)
        capped = http_client.fetch_json("/fixtures", headers={}, params={"ids": "2"})
        assert real_get.call_count == 2
        assert not http_client.result_is_complete(capped)


def _ctx() -> MagicMock:
    ctx = MagicMock()
    ctx.headers = {}
    ctx.errors = []
    return ctx


class TestStoredReads:
    def test_stored_counts_puts_each_section_where_the_guard_reads_it(self):
        rows = [
            {"section": "events", "fixture_id": 1, "team_id": None, "n": 12, "complete": False},
            {"section": "players", "fixture_id": 1, "team_id": HOME, "n": 16, "complete": False},
            {"section": "players", "fixture_id": 1, "team_id": AWAY, "n": 15, "complete": True},
            {"section": "statistics", "fixture_id": 1, "team_id": HOME, "n": 17, "complete": False},
            {"section": "statistics", "fixture_id": 1, "team_id": AWAY, "n": 18, "complete": False},
            {"section": "starters", "fixture_id": 1, "team_id": HOME, "n": 11, "complete": False},
        ]
        client = MagicMock()
        client.query.return_value.result.return_value = rows
        client.query.return_value.total_bytes_billed = 0
        stored = refetch.stored_counts(client, [1, 2])
        assert stored[1] == {
            "events": 12,
            "players_by_team": {HOME: 16, AWAY: 15},
            "statistics_by_team": {HOME: 17, AWAY: 18},
            "starters_by_team": {HOME: 11},
            "players_complete": True,
        }
        assert stored[2] == _empty_stored()
        assert "stg_apif__lineups" in client.query.call_args.args[0]

    def test_unread_raw_rows_compares_with_the_oldest_staging_table(self):
        older = datetime(2026, 10, 12, 4, 10, tzinfo=timezone.utc)
        newer = datetime(2026, 10, 12, 4, 30, tzinfo=timezone.utc)
        client = MagicMock()
        client.get_table.side_effect = [
            MagicMock(modified=newer), MagicMock(modified=older), MagicMock(modified=newer), MagicMock(modified=newer),
        ]
        client.query.return_value.result.return_value = iter([{"n": 4}])
        assert refetch.unread_raw_rows(client, [1, 2]) == 4
        params = {p.name: p for p in client.query.call_args.kwargs["job_config"].query_parameters}
        assert params["built"].value == older
        assert params["ids"].values == [1, 2]
        assert "RAW_APIF_FIXTURE_DETAILS" in client.query.call_args.args[0]


class TestRunFixtures:
    def _run(self, monkeypatch, answers, stored):
        fetch = MagicMock(side_effect=answers)
        insert = MagicMock()
        monkeypatch.setattr(refetch, "fetch_json", fetch)
        monkeypatch.setattr(refetch, "_insert_fixture_rows", insert)
        monkeypatch.setattr(refetch, "ensure_unified_raw_table", MagicMock())
        groups = {"PL": sorted(stored)}
        return refetch.run_fixtures(_ctx(), groups, stored), fetch, insert

    def test_writes_only_the_matches_the_guard_keeps(self, monkeypatch):
        answer = {"errors": [], "response": [_fixture(fid=1), _fixture(fid=2, events=1)]}
        report, _, insert = self._run(monkeypatch, [answer], {1: _stored(), 2: _stored()})
        written = insert.call_args.args[2]
        assert [fx["fixture"]["id"] for fx in written] == [1]
        assert insert.call_args.args[4] == "PL"
        assert report["written"] == 1
        assert report["refused"] == {"fewer events": 1}

    def test_an_incomplete_batch_is_not_written(self, monkeypatch):
        answer = {"errors": {"rateLimit": "Too many requests"}, "response": [_fixture(fid=1)]}
        report, _, insert = self._run(monkeypatch, [answer], {1: _stored()})
        insert.assert_not_called()
        assert report["batches_discarded"] == 1

    def test_stops_at_the_latched_flag(self, monkeypatch):
        errors_quota._http_quota_exhausted = True
        report, fetch, insert = self._run(monkeypatch, [], {1: _stored()})
        fetch.assert_not_called()
        insert.assert_not_called()
        assert report["written"] == 0

    def test_counts_matches_the_provider_did_not_return(self, monkeypatch):
        answer = {"errors": [], "response": [_fixture(fid=1)]}
        report, _, _ = self._run(monkeypatch, [answer], {1: _stored(), 2: _stored()})
        assert report["not_returned"] == 1


class TestRunSquads:
    def test_fetches_exactly_the_listed_pairs(self, monkeypatch):
        load = MagicMock()
        monkeypatch.setattr(refetch, "load_squad_players_batch", load)
        ctx = _ctx()
        refetch.run_squads(ctx, {("BL1", 2016): {5, 6}, ("PL", 2026): {7}})
        assert load.call_count == 2
        first = load.call_args_list[0]
        assert first.args == (ctx, "BL1", [2016], {5, 6})
        assert first.kwargs == {"reference_season": 2016, "already_captured": set()}


class TestMainRun:
    def _ids(self, tmp_path) -> str:
        ids = tmp_path / "ids.csv"
        ids.write_text("league_code,fixture_id\nPL,1\n", encoding="utf-8")
        return str(ids)

    def _patch(self, monkeypatch, *, hour=12, unread=0, acquired=True, run_fixtures=None):
        monkeypatch.setattr(refetch, "too_close_to_nightly", lambda now: 2 <= hour < 4)
        monkeypatch.setattr(refetch, "get_headers", dict)
        monkeypatch.setattr(refetch.bigquery, "Client", MagicMock())
        monkeypatch.setattr(refetch, "unread_raw_rows", MagicMock(return_value=unread))
        monkeypatch.setattr(refetch, "ensure_ingest_lock_table", MagicMock())
        monkeypatch.setattr(refetch, "acquire_ingest_lock", MagicMock(return_value=acquired))
        release = MagicMock()
        monkeypatch.setattr(refetch, "release_ingest_lock", release)
        monkeypatch.setattr(refetch, "stored_counts", MagicMock(return_value={1: _stored()}))
        monkeypatch.setattr(
            refetch,
            "run_fixtures",
            run_fixtures or MagicMock(return_value={"written": 0, "not_returned": 0, "batches_discarded": 0, "refused": {}}),
        )
        monkeypatch.setattr(refetch.CallCounter, "install", lambda self: None)
        return release

    def test_refused_in_the_nightly_window(self, monkeypatch, tmp_path):
        release = self._patch(monkeypatch, hour=3)
        assert refetch.main(["fixtures", "--ids-file", self._ids(tmp_path), "--run", "--max-calls", "5"]) == 2
        refetch.acquire_ingest_lock.assert_not_called()
        release.assert_not_called()

    def test_refused_while_raw_holds_rows_staging_has_not_read(self, monkeypatch, tmp_path):
        release = self._patch(monkeypatch, unread=3)
        assert refetch.main(["fixtures", "--ids-file", self._ids(tmp_path), "--run", "--max-calls", "5"]) == 2
        refetch.acquire_ingest_lock.assert_called_once()
        refetch.run_fixtures.assert_not_called()
        release.assert_called_once()

    def test_the_call_window_reaches_the_counter(self, monkeypatch, tmp_path):
        self._patch(monkeypatch)
        built = []

        class Recorder(refetch.CallCounter):
            def __init__(self, max_calls, deadline=None):
                built.append((max_calls, deadline))
                super().__init__(max_calls, deadline)

        monkeypatch.setattr(refetch, "CallCounter", Recorder)
        before = datetime.now(timezone.utc)
        assert refetch.main(["fixtures", "--ids-file", self._ids(tmp_path), "--run", "--max-calls", "5"]) == 0
        after = datetime.now(timezone.utc)
        (max_calls, deadline), = built
        assert max_calls == 5
        window = timedelta(minutes=refetch.CALL_WINDOW_MINUTES)
        assert before + window <= deadline <= after + window

    def test_refused_when_the_lock_is_held(self, monkeypatch, tmp_path):
        release = self._patch(monkeypatch, acquired=False)
        assert refetch.main(["fixtures", "--ids-file", self._ids(tmp_path), "--run", "--max-calls", "5"]) == 2
        release.assert_not_called()

    def test_takes_a_lease_sized_to_the_run(self, monkeypatch, tmp_path):
        self._patch(monkeypatch)
        assert refetch.main(["fixtures", "--ids-file", self._ids(tmp_path), "--run", "--max-calls", "5"]) == 0
        assert refetch.acquire_ingest_lock.call_args.kwargs == {"lease_minutes": refetch.LEASE_MINUTES}

    def test_paces_calls_at_250_ms_unless_set(self, monkeypatch, tmp_path):
        self._patch(monkeypatch)
        monkeypatch.delenv("API_FOOTBALL_REQUEST_PAUSE_MS", raising=False)
        refetch.main(["fixtures", "--ids-file", self._ids(tmp_path), "--run", "--max-calls", "5"])
        assert refetch.os.environ["API_FOOTBALL_REQUEST_PAUSE_MS"] == "250"

    def test_releases_the_lock_when_the_run_fails(self, monkeypatch, tmp_path):
        release = self._patch(monkeypatch, run_fixtures=MagicMock(side_effect=RuntimeError("boom")))
        with pytest.raises(RuntimeError):
            refetch.main(["fixtures", "--ids-file", self._ids(tmp_path), "--run", "--max-calls", "5"])
        release.assert_called_once()

    def test_a_missing_api_key_fails_before_the_lock(self, monkeypatch, tmp_path):
        self._patch(monkeypatch)
        monkeypatch.setattr(refetch, "get_headers", MagicMock(side_effect=ValueError("no key")))
        with pytest.raises(ValueError):
            refetch.main(["fixtures", "--ids-file", self._ids(tmp_path), "--run", "--max-calls", "5"])
        refetch.acquire_ingest_lock.assert_not_called()
