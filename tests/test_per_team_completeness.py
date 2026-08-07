"""Per-team endpoints get a completeness check (#898 cause 3).

`FANOUT_ENTITIES` covers fixture-level data only, so `coaches`, `players`, `player_squads` and
`transfers` had NO completeness check at all. #896 is why that matters: the table GREW while data
was destroyed, so row-count, freshness and not-null tests all passed.

Measured before building: transfers 0 teams missing, squads 0, players 0, coaches 29 of 2,058 and
stable across five days. The data is complete, so this is regression insurance, and a gate
introduced at 0 can only ever fire on a regression.

Two expected-set designs were tried against production and BOTH were wrong. These tests pin the
third, so neither is reintroduced:
  1. Deriving the season as the calendar year reported ACN as 24/24 missing. ACN is on 2027.
  2. Deriving the league set from RAW_APIF_TEAMS judged 45 leagues and reported 33 league/entity
     pairs missing, including FAC/PLAYERS 749 — competitions that are SELECTED but run in POLL mode
     and never fetch per-team data at all.
"""

from __future__ import annotations

import types

from ingestion.api_football.completeness import (
    PER_TEAM_ENTITIES,
    PER_TEAM_GATED,
    detect_stagnant_per_team_gaps,
    evaluate_completeness_outcome,
    per_team_expectations_from_results,
    per_team_missing_by_league_entity,
    read_per_team_coverage,
)


class _Result:
    def __init__(self, rows):
        self._rows = rows

    def result(self):
        return self._rows


class _FakeClient:
    """Answers the maxima queries and the single coverage query, with no network.

    ``missing_tables`` names raw entities that do not exist yet, so the first-run path can actually
    be exercised per table. The first version of this fake had a single has_tables flag and could
    not express "RAW_APIF_PLAYERS specifically is absent", which is the one path that was unguarded.
    """

    def __init__(self, covered_rows, missing_tables=()):
        self._covered = covered_rows
        self._missing = set(missing_tables)
        self.queries: list[str] = []

    def get_table(self, table_id):
        if any(f"RAW_APIF_{m}" in table_id for m in self._missing):
            from google.cloud.exceptions import NotFound

            raise NotFound(table_id)
        return object()

    def query(self, q):
        self.queries.append(q)
        if "MAX(ingested_at)" in q:
            return _Result(
                [
                    types.SimpleNamespace(league_code="BL1", mx=_TS),
                    types.SimpleNamespace(league_code="ACN", mx=_TS),
                ]
            )
        return _Result(self._covered)

    @property
    def coverage_queries(self) -> list[str]:
        return [q for q in self.queries if "MAX(ingested_at)" not in q]


class _TSObj:
    def isoformat(self):
        return "2026-08-03T04:00:00+00:00"


_TS = _TSObj()


def _row(entity, league_code, team_id):
    return types.SimpleNamespace(entity=entity, league_code=league_code, team_id=team_id)


def _run_result(league_code, team_ids, seasons_list):
    """The fields per_team_expectations_from_results reads off a CompetitionRunResult."""
    return types.SimpleNamespace(
        league_code=league_code, team_ids=set(team_ids), seasons_list=list(seasons_list)
    )


class TestExpectationsComeFromTheRunNotBigQuery:
    """The function that makes the two proven-wrong expected-set designs un-reintroducible.

    Review FAILED an earlier round twice over this: the extraction happened, the tests did not, and
    the contract claimed otherwise. Without these, reverting to a `selected_competitions()` or
    RAW_APIF_TEAMS-derived expected set — the designs that reported 33 false-missing league/entity
    pairs including FAC/PLAYERS 749, and ACN as 24/24 missing — would ship undetected.
    """

    def test_reference_season_is_max_of_seasons_list(self):
        # Must equal what load_squad_players_batch is actually called with, which is
        # max(result.seasons_list). If these drift, every players count is judged against the
        # wrong season.
        out = per_team_expectations_from_results(
            [_run_result("BL1", {1, 2}, [2024, 2025, 2026])]
        )
        assert out == {"BL1": {"team_ids": {1, 2}, "reference_season": 2026}}

    def test_a_tournament_on_a_later_edition_is_carried_correctly(self):
        # ACN and J1 are on 2027 while everything else is on 2026. Taking the calendar year here
        # is what reported ACN as 24 of 24 teams missing.
        out = per_team_expectations_from_results(
            [_run_result("ACN", {9}, [2025, 2027]), _run_result("BL1", {1}, [2026])]
        )
        assert out["ACN"]["reference_season"] == 2027
        assert out["BL1"]["reference_season"] == 2026

    def test_poll_mode_competitions_cannot_appear(self):
        # THE REGRESSION THAT MATTERS. Poll-mode competitions never return a CompetitionRunResult,
        # because run_poll_phases fetches no teams, players, squads or transfers. They are absent by
        # construction, which is why nothing derived from BigQuery may be substituted here.
        out = per_team_expectations_from_results([_run_result("BL1", {1}, [2026])])
        assert set(out) == {"BL1"}
        for absent in ("FAC", "CDR", "EURO", "WCQEU"):
            assert absent not in out

    def test_empty_results_yield_no_expectations(self):
        assert per_team_expectations_from_results([]) == {}
        assert per_team_expectations_from_results(None) == {}

    def test_missing_seasons_list_gives_no_reference_season(self):
        # A competition whose season plan failed must not silently be judged against season None;
        # read_per_team_coverage skips the PLAYERS pairing for it.
        out = per_team_expectations_from_results([_run_result("BL1", {1}, [])])
        assert out["BL1"]["reference_season"] is None

    def test_team_ids_are_copied_not_aliased(self):
        # The loaders hold the same set object; mutating the expectation must not reach them.
        result = _run_result("BL1", {1, 2}, [2026])
        out = per_team_expectations_from_results([result])
        out["BL1"]["team_ids"].add(99)
        assert result.team_ids == {1, 2}

    def test_feeds_read_per_team_coverage_end_to_end(self):
        # The extraction is only worth anything if its output is the shape the consumer expects.
        client = _FakeClient([_row("SQUADS", "BL1", 1)])
        out = read_per_team_coverage(
            client, per_team_expectations_from_results([_run_result("BL1", {1, 2}, [2026])])
        )
        assert out["BL1"]["SQUADS"] == {"expected_count": 2, "missing_count": 1}
        assert out["BL1"]["reference_season"] == 2026


class TestExpectedComesFromTheRun:
    def test_only_leagues_in_expectations_are_judged(self):
        # THE POLL-MODE REGRESSION TEST. Competitions that ran poll phases never fetch per-team
        # data, so they must not appear at all. Deriving the league set from BigQuery instead
        # reported FAC/PLAYERS as 749 teams missing when nothing had ever fetched them.
        covered = [_row(e, "BL1", 1) for e in PER_TEAM_ENTITIES]
        client = _FakeClient(covered)
        out = read_per_team_coverage(
            client, {"BL1": {"team_ids": {1}, "reference_season": 2026}}
        )
        assert set(out) == {"BL1"}

    def test_a_league_with_no_teams_is_not_judged(self):
        client = _FakeClient([])
        out = read_per_team_coverage(
            client, {"BL1": {"team_ids": set(), "reference_season": 2026}}
        )
        assert out == {}

    def test_empty_expectations_short_circuits_without_querying(self):
        client = _FakeClient([])
        assert read_per_team_coverage(client, {}) == {}
        assert client.queries == []

    def test_missing_count_is_expected_minus_covered(self):
        covered = [_row("SQUADS", "BL1", 1), _row("SQUADS", "BL1", 2)]
        client = _FakeClient(covered)
        out = read_per_team_coverage(
            client, {"BL1": {"team_ids": {1, 2, 3}, "reference_season": 2026}}
        )
        assert out["BL1"]["SQUADS"] == {"expected_count": 3, "missing_count": 1}
        # An entity with no covered rows at all is fully missing, not silently absent.
        assert out["BL1"]["TRANSFERS"] == {"expected_count": 3, "missing_count": 3}

    def test_reference_season_is_carried_per_league(self):
        # ACN is on 2027 while everything else is on 2026. The season comes from the run's
        # seasons_list, so it cannot disagree with what the loader was called with.
        client = _FakeClient([])
        out = read_per_team_coverage(
            client,
            {
                "BL1": {"team_ids": {1}, "reference_season": 2026},
                "ACN": {"team_ids": {9}, "reference_season": 2027},
            },
        )
        assert out["ACN"]["reference_season"] == 2027
        assert out["BL1"]["reference_season"] == 2026

    def test_snapshot_timestamp_is_paired_to_its_own_league(self):
        # A flat `ingested_at IN (...)` plus a flat `league_code IN (...)` are two INDEPENDENT
        # filters, so a row for one league carrying another league's latest timestamp counts as
        # coverage. Review caught this; it fails in the dangerous direction, making a real miss look
        # covered. Measured: pairing costs nothing, 383,545,007 bytes either way on RAW_APIF_TRANSFERS.
        client = _FakeClient([])
        read_per_team_coverage(
            client,
            {
                "BL1": {"team_ids": {1}, "reference_season": 2026},
                "ACN": {"team_ids": {9}, "reference_season": 2027},
            },
        )
        coverage_q = client.coverage_queries[0]
        assert "(s.league_code = 'BL1' AND s.ingested_at = TIMESTAMP(" in coverage_q
        assert "(s.league_code = 'ACN' AND s.ingested_at = TIMESTAMP(" in coverage_q
        # The unpaired form must not survive anywhere.
        assert "s.ingested_at IN (" not in coverage_q

    def test_players_season_is_matched_per_league_not_globally(self):
        # A shared season IN-list would let ACN's 2027 rows satisfy BL1's 2026 expectation.
        client = _FakeClient([])
        read_per_team_coverage(
            client,
            {
                "BL1": {"team_ids": {1}, "reference_season": 2026},
                "ACN": {"team_ids": {9}, "reference_season": 2027},
            },
        )
        coverage_q = [q for q in client.queries if "MAX(ingested_at)" not in q][0]
        assert "(p.league_code = 'ACN' AND" in coverage_q
        assert "= 2027)" in coverage_q
        assert "(p.league_code = 'BL1' AND" in coverage_q
        assert "= 2026)" in coverage_q

    def test_players_table_missing_does_not_raise(self):
        # REGRESSION TEST for the defect review caught. PLAYERS has no maxima step, so it does not
        # get the existence guard for free the way the three snapshot entities do. Without an
        # explicit check the query raised straight through the orchestrator's blanket handler and
        # hard-failed the run. Note reference_season IS supplied here: the earlier version of this
        # test could never reach the bug because the PLAYERS block was always present.
        client = _FakeClient([], missing_tables={"PLAYERS"})
        out = read_per_team_coverage(
            client, {"BL1": {"team_ids": {1, 2}, "reference_season": 2026}}
        )
        assert out["BL1"]["PLAYERS"]["missing_count"] == 2
        assert all("RAW_APIF_PLAYERS" not in q for q in client.coverage_queries)

    def test_all_tables_missing_issues_no_coverage_query(self):
        # The degenerate case: with no blocks the UNION rendered as `FROM ()`, invalid SQL that was
        # executed unguarded. Nothing should be queried, and everything reads as uncovered.
        client = _FakeClient([], missing_tables={"PLAYERS", "SQUADS", "TRANSFERS", "COACHES"})
        out = read_per_team_coverage(
            client, {"BL1": {"team_ids": {1, 2, 3}, "reference_season": 2026}}
        )
        assert client.coverage_queries == []
        for entity in PER_TEAM_ENTITIES:
            assert out["BL1"][entity] == {"expected_count": 3, "missing_count": 3}

    def test_one_snapshot_table_missing_degrades_only_that_entity(self):
        client = _FakeClient(
            [_row("SQUADS", "BL1", 1), _row("PLAYERS", "BL1", 1)],
            missing_tables={"TRANSFERS"},
        )
        out = read_per_team_coverage(
            client, {"BL1": {"team_ids": {1}, "reference_season": 2026}}
        )
        assert out["BL1"]["SQUADS"]["missing_count"] == 0
        assert out["BL1"]["TRANSFERS"]["missing_count"] == 1


class TestCoachesReportsButNeverGates:
    def test_coaches_is_reported(self):
        assert "COACHES" in PER_TEAM_ENTITIES

    def test_coaches_is_not_gated(self):
        # ~23 of 1,265 teams have no coach on EVERY run, measured stable over five days, because
        # the provider genuinely has none. Gating it would be permanently red, and a permanently-red
        # gate is how ten green runs came to mean nothing.
        assert "COACHES" not in PER_TEAM_GATED

    def test_coaches_gaps_never_reach_the_stagnation_snapshot(self):
        per_team = {
            "BL1": {
                "reference_season": 2026,
                "COACHES": {"expected_count": 30, "missing_count": 7},
                "PLAYERS": {"expected_count": 18, "missing_count": 0},
                "SQUADS": {"expected_count": 30, "missing_count": 0},
                "TRANSFERS": {"expected_count": 30, "missing_count": 0},
            }
        }
        assert per_team_missing_by_league_entity(per_team) == {}

    def test_gated_entity_gaps_do_reach_it(self):
        per_team = {
            "BL1": {
                "reference_season": 2026,
                "COACHES": {"expected_count": 30, "missing_count": 7},
                "PLAYERS": {"expected_count": 18, "missing_count": 3},
                "SQUADS": {"expected_count": 30, "missing_count": 0},
                "TRANSFERS": {"expected_count": 30, "missing_count": 0},
            }
        }
        assert per_team_missing_by_league_entity(per_team) == {"BL1/PLAYERS": 3}


class TestStagnationWindow:
    def test_one_run_does_not_fail(self):
        # A hard fail skips dbt build and costs daily freshness, and a brand-new team whose first
        # fetch fails would otherwise fail the run on the day it appears.
        assert detect_stagnant_per_team_gaps({"BL1/PLAYERS": 3}, {}) == []

    def test_two_runs_running_fails(self):
        out = detect_stagnant_per_team_gaps({"BL1/PLAYERS": 3}, {"BL1/PLAYERS": 5})
        assert out == [
            {"league_code": "BL1", "entity": "PLAYERS", "prior_count": 5, "count": 3}
        ]

    def test_healed_gap_does_not_fail(self):
        assert detect_stagnant_per_team_gaps({}, {"BL1/PLAYERS": 5}) == []

    def test_a_different_entity_is_not_stagnation(self):
        assert detect_stagnant_per_team_gaps({"BL1/PLAYERS": 3}, {"BL1/SQUADS": 3}) == []

    def test_no_prior_run_is_silent(self):
        assert detect_stagnant_per_team_gaps({"BL1/PLAYERS": 3}, None) == []


class TestGateRespectsTheOperatorKillSwitches:
    """The same defect review caught in the previous task, pinned up front here."""

    _REPORT = {"leagues": {}}
    _CUR = {"BL1/PLAYERS": 3}
    _PRIOR = {"BL1/PLAYERS": 5}

    def test_hard_fails_by_default(self, monkeypatch):
        monkeypatch.delenv("API_FOOTBALL_FAIL_ON_INCOMPLETE", raising=False)
        out = evaluate_completeness_outcome(
            self._REPORT, per_team_missing=self._CUR, prior_per_team_missing=self._PRIOR
        )
        assert out["stagnant_per_team_gaps"]
        assert out["hard_fail"] is True

    def test_fail_on_incomplete_override_suppresses_the_fail(self, monkeypatch):
        monkeypatch.setenv("API_FOOTBALL_FAIL_ON_INCOMPLETE", "0")
        out = evaluate_completeness_outcome(
            self._REPORT, per_team_missing=self._CUR, prior_per_team_missing=self._PRIOR
        )
        assert out["stagnant_per_team_gaps"], "still reported, so it stays visible"
        assert out["hard_fail"] is False

    def test_skipped_report_suppresses_the_fail(self, monkeypatch):
        monkeypatch.delenv("API_FOOTBALL_FAIL_ON_INCOMPLETE", raising=False)
        out = evaluate_completeness_outcome(
            {"skipped": True},
            per_team_missing=self._CUR,
            prior_per_team_missing=self._PRIOR,
        )
        assert out["stagnant_per_team_gaps"] == []
        assert out["hard_fail"] is False

    def test_absent_args_change_nothing(self, monkeypatch):
        monkeypatch.delenv("API_FOOTBALL_FAIL_ON_INCOMPLETE", raising=False)
        out = evaluate_completeness_outcome(self._REPORT)
        assert out["stagnant_per_team_gaps"] == []
        assert out["hard_fail"] is False
