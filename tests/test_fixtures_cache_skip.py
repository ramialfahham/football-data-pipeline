"""Tests for the historical-season skip in loads/fixtures.py (issue #283).

The fixtures loader reuses the cached BQ snapshot for a historical season whose
fixtures are all in a terminal state, instead of re-calling /fixtures. These
tests pin down the correctness guards around that optimization:

- the current (newest) season is never skipped,
- a non-terminal status (NS/PST/ABD) forces a re-fetch,
- an empty/cold cache forces a re-fetch,
- the skip only applies in full-season fixture mode,
- skipped seasons still flow through into the merged BQ snapshot.

All BigQuery and HTTP interactions are mocked — no live GCP connection required.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from ingestion.api_football.loads.fixtures import (
    _season_complete_in_cache,
    fetch_merge_and_persist_fixtures,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_ctx():
    ctx = MagicMock()
    ctx.errors = []
    ctx.headers = {"x-apisports-key": "test"}
    return ctx


def _fixture(fixture_id: int, season: int, status: str) -> dict:
    return {
        "fixture": {"id": fixture_id, "status": {"short": status}},
        "league": {"season": season},
        "teams": {"home": {"id": 10}, "away": {"id": 20}},
    }


def _envelope(items: list) -> dict:
    return {
        "response": items,
        "errors": [],
        "results": len(items),
        "paging": {"current": 1, "total": 1},
    }


# ---------------------------------------------------------------------------
# _season_complete_in_cache (pure logic)
# ---------------------------------------------------------------------------


class TestSeasonCompleteInCache:
    def test_all_finished_is_complete(self):
        cached = [_fixture(1, 2023, "FT"), _fixture(2, 2023, "AET")]
        assert _season_complete_in_cache(cached, 2023) is True

    def test_administratively_final_statuses_are_complete(self):
        cached = [_fixture(1, 2023, "FT"), _fixture(2, 2023, "CANC"), _fixture(3, 2023, "WO")]
        assert _season_complete_in_cache(cached, 2023) is True

    def test_not_started_fixture_is_incomplete(self):
        cached = [_fixture(1, 2023, "FT"), _fixture(2, 2023, "NS")]
        assert _season_complete_in_cache(cached, 2023) is False

    def test_postponed_fixture_is_incomplete(self):
        # PST can be rescheduled — must keep re-fetching.
        cached = [_fixture(1, 2023, "FT"), _fixture(2, 2023, "PST")]
        assert _season_complete_in_cache(cached, 2023) is False

    def test_abandoned_fixture_is_incomplete(self):
        # ABD can be replayed — must keep re-fetching.
        cached = [_fixture(1, 2023, "FT"), _fixture(2, 2023, "ABD")]
        assert _season_complete_in_cache(cached, 2023) is False

    def test_empty_season_is_incomplete(self):
        # A cold/partial cache with nothing for this season must not be treated as done.
        assert _season_complete_in_cache([], 2023) is False
        assert _season_complete_in_cache([_fixture(1, 2024, "FT")], 2023) is False


# ---------------------------------------------------------------------------
# fetch_merge_and_persist_fixtures skip behaviour
# ---------------------------------------------------------------------------


def _run(ctx, cached_items, api_side_effect, seasons, monkeyenv=None):
    """Drive the loader with a mocked cache read + mocked API, return the BQ write mock."""
    env = {"API_FOOTBALL_FIXTURES_MODE": "season"}
    if monkeyenv:
        env.update(monkeyenv)
    with patch.dict("os.environ", env, clear=False):
        with patch(
            "ingestion.api_football.loads.fixtures.read_latest_payload_json",
            return_value=_envelope(cached_items),
        ):
            with patch(
                "ingestion.api_football.loads.fixtures.fetch_merged_paged",
                side_effect=api_side_effect,
            ) as mock_fetch:
                with patch(
                    "ingestion.api_football.loads.fixtures.load_json_to_bq"
                ) as mock_bq:
                    fetch_merge_and_persist_fixtures(ctx, "BL1", 78, seasons)
    return mock_fetch, mock_bq


class TestFetchMergeSkip:
    def test_complete_historical_season_skips_api(self):
        ctx = _make_ctx()
        cached = [_fixture(1, 2023, "FT"), _fixture(2, 2024, "NS")]
        # Only the current season (2024) should hit the API.
        mock_fetch, _ = _run(
            ctx,
            cached,
            api_side_effect=[_envelope([_fixture(2, 2024, "NS")])],
            seasons=[2023, 2024],
        )
        assert mock_fetch.call_count == 1
        assert mock_fetch.call_args_list[0][0][2]["season"] == 2024

    def test_current_season_never_skipped_even_if_all_finished(self):
        ctx = _make_ctx()
        # 2024 is the newest season AND fully finished in cache — must still re-fetch.
        cached = [_fixture(1, 2024, "FT")]
        mock_fetch, _ = _run(
            ctx,
            cached,
            api_side_effect=[_envelope([_fixture(1, 2024, "FT")])],
            seasons=[2024],
        )
        assert mock_fetch.call_count == 1

    def test_incomplete_historical_season_refetched(self):
        ctx = _make_ctx()
        cached = [_fixture(1, 2023, "NS"), _fixture(2, 2024, "NS")]
        mock_fetch, _ = _run(
            ctx,
            cached,
            api_side_effect=[
                _envelope([_fixture(1, 2023, "NS")]),
                _envelope([_fixture(2, 2024, "NS")]),
            ],
            seasons=[2023, 2024],
        )
        assert mock_fetch.call_count == 2

    def test_cold_cache_fetches_all_seasons(self):
        ctx = _make_ctx()
        mock_fetch, _ = _run(
            ctx,
            cached_items=[],
            api_side_effect=[
                _envelope([_fixture(1, 2023, "FT")]),
                _envelope([_fixture(2, 2024, "NS")]),
            ],
            seasons=[2023, 2024],
        )
        assert mock_fetch.call_count == 2

    def test_non_season_mode_never_skips_and_skips_cache_read(self):
        ctx = _make_ctx()
        # No `cached` fixture list here, unlike its siblings: this test asserts
        # `mock_read.assert_not_called()`, so the cache is never consulted and its
        # contents cannot affect the result. One was copied in and left unused (F841).
        with patch.dict(
            "os.environ", {"API_FOOTBALL_FIXTURES_MODE": "from_to"}, clear=False
        ):
            with patch(
                "ingestion.api_football.loads.fixtures.read_latest_payload_json"
            ) as mock_read:
                with patch(
                    "ingestion.api_football.loads.fixtures.fetch_merged_paged",
                    side_effect=[
                        _envelope([_fixture(1, 2023, "FT")]),
                        _envelope([_fixture(2, 2024, "NS")]),
                    ],
                ) as mock_fetch:
                    with patch(
                        "ingestion.api_football.loads.fixtures.load_json_to_bq"
                    ):
                        fetch_merge_and_persist_fixtures(ctx, "BL1", 78, [2023, 2024])

        # Window mode: no cache read at all, and both seasons re-fetched.
        mock_read.assert_not_called()
        assert mock_fetch.call_count == 2

    def test_skipped_season_still_written_into_merged_snapshot(self):
        ctx = _make_ctx()
        cached = [_fixture(1, 2023, "FT"), _fixture(2, 2024, "NS")]
        _, mock_bq = _run(
            ctx,
            cached,
            api_side_effect=[_envelope([_fixture(2, 2024, "NS")])],
            seasons=[2023, 2024],
        )
        # One BQ write of the full merged snapshot containing both the cached 2023
        # fixture and the freshly fetched 2024 fixture.
        assert mock_bq.call_count == 1
        payload = mock_bq.call_args[0][2]
        seasons_written = {f["league"]["season"] for f in payload["response"]}
        assert seasons_written == {2023, 2024}
