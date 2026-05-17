"""Tests for ingest_plan.decide_ingest_mode (full vs poll policy)."""

from __future__ import annotations

from ingestion.api_football.ingest_plan import decide_ingest_mode


def test_no_fixtures_payload_means_full():
    mode, reason = decide_ingest_mode(
        has_fixtures_payload=False,
        upcoming_count=0,
        fanout_gaps_on_finished=False,
    )
    assert mode == "full"
    assert reason == "no_merged_fixtures_in_bq"


def test_upcoming_fixtures_means_full():
    mode, reason = decide_ingest_mode(
        has_fixtures_payload=True,
        upcoming_count=3,
        fanout_gaps_on_finished=False,
    )
    assert mode == "full"
    assert "upcoming_fixtures=3" in reason


def test_fanout_gaps_means_full():
    mode, reason = decide_ingest_mode(
        has_fixtures_payload=True,
        upcoming_count=0,
        fanout_gaps_on_finished=True,
    )
    assert mode == "full"
    assert reason == "finished_fanout_gaps"


def test_idle_complete_means_poll():
    mode, reason = decide_ingest_mode(
        has_fixtures_payload=True,
        upcoming_count=0,
        fanout_gaps_on_finished=False,
    )
    assert mode == "poll"
    assert reason == "idle_complete"


def test_force_full_override():
    mode, reason = decide_ingest_mode(
        has_fixtures_payload=True,
        upcoming_count=5,
        fanout_gaps_on_finished=True,
        force_full=True,
    )
    assert mode == "full"
    assert reason == "API_FOOTBALL_INGEST_FORCE_FULL"
