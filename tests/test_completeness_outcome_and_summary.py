"""Tests for completeness outcome tiering and markdown summary rendering.

Pure functions, no BigQuery / no IO. Covers:

- ``evaluate_completeness_outcome`` correctly hard-fails for ``active`` gaps
  but stays green when only ``in_progress`` competitions are partial
- ``completeness_markdown_summary`` renders the expected GitHub-flavoured
  table for both fully-green and mixed-state reports
"""

from __future__ import annotations

from datetime import datetime, timezone

from ingestion.api_football.completeness import (
    completeness_markdown_summary,
    detect_stagnant_statistics_backfill,
    evaluate_completeness_outcome,
)


def _league_block(
    *,
    status: str,
    finished: int,
    total: int,
    missing_per_endpoint: dict[str, int] | None = None,
    gate: str | None = None,
) -> dict:
    """Build a per-league block in the shape the report uses."""
    missing_per_endpoint = missing_per_endpoint or {}
    if gate is None:
        gate = "hard" if status == "active" else "soft"
    fanout = {}
    for entity in ("LINEUPS", "FIXTURE_EVENTS", "FIXTURE_STATISTICS",
                   "FIXTURE_PLAYERS"):
        miss = missing_per_endpoint.get(entity, 0)
        fanout[entity] = {
            "covered_count": finished - miss,
            "expected_count": finished,
            "missing_count": miss,
            "missing_fixture_ids_sample": [],
            "complete": miss == 0,
        }
    all_complete = all(info["complete"] for info in fanout.values())
    return {
        "registry_status": status,
        "ingest_completeness_gate": gate,
        "fixture_total_count": total,
        "fixture_expected_count": finished,
        "fixture_unplayed_count": total - finished,
        "fanout": fanout,
        "all_fanout_complete": all_complete,
        "match_level_tables_cover_all_fixtures": all_complete,
    }


class TestEvaluateCompletenessOutcome:
    def test_all_complete_no_failures(self):
        report = {
            "skipped": False,
            "leagues": {
                "BL1": _league_block(status="active", finished=100, total=100),
                "WCQAF": _league_block(status="in_progress", finished=50, total=50),
            },
        }
        outcome = evaluate_completeness_outcome(report)
        assert outcome["hard_fail"] is False
        assert outcome["active_failures"] == []
        assert outcome["in_progress_partial"] == []

    def test_active_competition_partial_triggers_hard_fail(self):
        report = {
            "skipped": False,
            "leagues": {
                "BL1": _league_block(
                    status="active", finished=100, total=100,
                    missing_per_endpoint={"FIXTURE_STATISTICS": 5},
                ),
            },
        }
        outcome = evaluate_completeness_outcome(report)
        assert outcome["hard_fail"] is True
        assert len(outcome["active_failures"]) == 1
        f = outcome["active_failures"][0]
        assert f["league_code"] == "BL1"
        assert f["total_missing"] == 5
        assert f["missing_endpoints"][0]["endpoint"] == "FIXTURE_STATISTICS"
        assert f["missing_endpoints"][0]["missing_count"] == 5

    def test_in_progress_soft_gate_does_not_hard_fail(self):
        report = {
            "skipped": False,
            "leagues": {
                "BL1": _league_block(status="active", finished=100, total=100),
                "WCQOC": _league_block(
                    status="in_progress", finished=18, total=18,
                    missing_per_endpoint={"FIXTURE_STATISTICS": 18},
                    gate="soft",
                ),
            },
        }
        outcome = evaluate_completeness_outcome(report)
        assert outcome["hard_fail"] is False
        assert outcome["hard_gated_failures"] == []
        assert len(outcome["soft_partial"]) == 1

    def test_in_progress_hard_gate_triggers_hard_fail(self):
        report = {
            "skipped": False,
            "leagues": {
                "WCQAF": _league_block(
                    status="in_progress", finished=540, total=557,
                    missing_per_endpoint={"FIXTURE_STATISTICS": 434},
                    gate="hard",
                ),
            },
        }
        outcome = evaluate_completeness_outcome(report)
        assert outcome["hard_fail"] is True
        assert len(outcome["hard_gated_failures"]) == 1
        assert outcome["hard_gated_failures"][0]["league_code"] == "WCQAF"

    def test_stagnant_statistics_triggers_hard_fail(self):
        report = {
            "skipped": False,
            "leagues": {
                "WCQAF": _league_block(
                    status="in_progress", finished=540, total=557,
                    missing_per_endpoint={"FIXTURE_STATISTICS": 434},
                    gate="hard",
                ),
            },
        }
        prior = {"WCQAF": 434}
        stagnant = detect_stagnant_statistics_backfill(report, prior)
        assert len(stagnant) == 1
        outcome = evaluate_completeness_outcome(report, prior_fixture_statistics_missing=prior)
        assert outcome["hard_fail"] is True
        assert len(outcome["stagnant_statistics"]) == 1

    def test_mixed_active_and_in_progress_failures(self):
        # Active failure should hard-fail the run; in_progress partials still
        # get reported but don't drive hard_fail by themselves.
        report = {
            "skipped": False,
            "leagues": {
                "BL1": _league_block(
                    status="active", finished=100, total=100,
                    missing_per_endpoint={"LINEUPS": 1},
                ),
                "WCQAF": _league_block(
                    status="in_progress", finished=540, total=557,
                    missing_per_endpoint={"FIXTURE_STATISTICS": 434},
                    gate="soft",
                ),
            },
        }
        outcome = evaluate_completeness_outcome(report)
        assert outcome["hard_fail"] is True
        assert [f["league_code"] for f in outcome["active_failures"]] == ["BL1"]
        assert [p["league_code"] for p in outcome["soft_partial"]] == ["WCQAF"]

    def test_skipped_report_returns_no_failures(self):
        report = {"skipped": True}
        outcome = evaluate_completeness_outcome(report)
        assert outcome == {
            "hard_fail": False,
            "hard_gated_failures": [],
            "active_failures": [],
            "in_progress_partial": [],
            "soft_partial": [],
            "stagnant_statistics": [],
            # #898: dropped-call stagnation is evaluated inside this function precisely so that
            # SKIP_COMPLETENESS_CHECK suppresses it too, like every other completeness failure.
            # Kept inside the exact-equality assertion rather than relaxed to a subset, so a
            # future signal still cannot be added here unnoticed.
            "stagnant_dropped_calls": [],
            # #898 cause 3: per-team gaps are evaluated inside this function so that
            # SKIP_COMPLETENESS_CHECK suppresses them too. Extended in place, never relaxed to a
            # subset, so a future signal still cannot be added here unnoticed.
            "stagnant_per_team_gaps": [],
            # Pairs the re-fetch cadence deliberately skipped this run, which the gate exempts
            # from stagnation. Reported so an exemption is never silent. Added here
            # consciously, which is the point of the exact-equality assertion above — this key
            # could not slip in unnoticed, and it did not.
            "skipped_per_team_exempt": [],
        }


class TestCompletenessMarkdownSummary:
    _FROZEN_TIME = datetime(2026, 5, 8, 6, 4, tzinfo=timezone.utc)

    def test_renders_header_and_table(self):
        report = {
            "skipped": False,
            "leagues": {
                "BL1": _league_block(status="active", finished=3056, total=3074),
            },
        }
        md = completeness_markdown_summary(report, now=self._FROZEN_TIME)
        assert "## Ingestion completeness — 2026-05-08 06:04 UTC" in md
        assert "| Competition | Status | Finished / Total | Coverage | Backfill remaining |" in md
        assert "| BL1 | active (hard gate) | 3056 / 3074 |" in md
        assert "all 4 endpoints 100%" in md
        assert "| — |" in md.splitlines()[-1]  # backfill cell empty for complete

    def test_partial_coverage_shows_per_endpoint_percentage(self):
        report = {
            "skipped": False,
            "leagues": {
                "WCQAF": _league_block(
                    status="in_progress", finished=540, total=557,
                    missing_per_endpoint={"FIXTURE_STATISTICS": 434},
                ),
            },
        }
        md = completeness_markdown_summary(report, now=self._FROZEN_TIME)
        # 540 - 434 = 106 covered out of 540 → 19.6%
        assert "FIXTURE_STATISTICS 19.6%" in md
        # Other endpoints are 100% so they appear without the warning marker
        assert "LINEUPS 100.0%" in md
        # The total backfill remaining is 434 fixture-endpoint pairs
        assert "434 fixture-endpoint pairs" in md

    def test_includes_run_notes_when_provided(self):
        report = {
            "skipped": False,
            "leagues": {
                "BL1": _league_block(status="active", finished=100, total=100),
            },
        }
        md = completeness_markdown_summary(
            report,
            notes=["Loaded 42 API-Football tables.", "API daily request limit reached."],
            now=self._FROZEN_TIME,
        )
        assert "### Run notes" in md
        assert "- Loaded 42 API-Football tables." in md
        assert "- API daily request limit reached." in md

    def test_skipped_report(self):
        md = completeness_markdown_summary({"skipped": True}, now=self._FROZEN_TIME)
        assert "Completeness check was skipped" in md

    def test_competitions_sorted_alphabetically(self):
        report = {
            "skipped": False,
            "leagues": {
                "WCQAF": _league_block(status="in_progress", finished=10, total=10),
                "BL1":   _league_block(status="active", finished=10, total=10),
                "WC":    _league_block(status="active", finished=10, total=10),
            },
        }
        md = completeness_markdown_summary(report, now=self._FROZEN_TIME)
        bl1_idx = md.find("| BL1 |")
        wc_idx = md.find("| WC |")
        wcqaf_idx = md.find("| WCQAF |")
        assert 0 < bl1_idx < wc_idx < wcqaf_idx
