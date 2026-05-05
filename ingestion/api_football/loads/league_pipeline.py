"""Ingestion pipeline for a single competition: catalog → fixtures → standings → rounds → teams → injuries → transfers → fanout → squads.

ingest_league() is called once per competition per run. It is intentionally sequential:
each phase depends on data from the previous one (e.g. team_ids from fixtures feed the
squad players fetch). All errors are caught per-competition so a failure in one does not
abort the others.

This is the single place to add or reorder ingestion phases. Every competition —
domestic league, international tournament, qualifier — goes through the same steps.
"""

from __future__ import annotations

from .context import PipelineContext
from .fixture_fanout_load import run_fixture_fanout_and_persist
from .fixtures_load import fetch_merge_and_persist_fixtures
from .injuries_load import load_injuries_if_enabled
from .league_catalog import fetch_catalog_persist_and_plan
from .rounds_load import load_rounds_merged
from .squad_players_load import load_squad_players_batch
from .standings_load import load_standings_if_enabled
from .teams_load import load_teams_merge_and_extend_ids
from .transfers_load import load_transfers_if_enabled


def _ingestion_phase(league_code: str, step: str) -> None:
    print(f"[api-football] league={league_code} phase={step}", flush=True)


def ingest_league(
    ctx: PipelineContext,
    league_code: str,
    league_id: int,
    form_source: str = "league_only",
    supporting_leagues: tuple = (),
    current_season: int | None = None,
) -> None:
    try:
        _ingestion_phase(league_code, "catalog (leagues + season plan)")
        seasons_list, reference_season, cov = fetch_catalog_persist_and_plan(
            ctx, league_code, league_id, current_season=current_season
        )
        _ingestion_phase(league_code, "fixtures (/fixtures merge -> BQ)")
        fixtures_merged, team_ids, fixture_ids = fetch_merge_and_persist_fixtures(
            ctx, league_code, league_id, seasons_list
        )
        _ingestion_phase(league_code, "standings")
        load_standings_if_enabled(
            ctx, league_code, league_id, seasons_list, cov
        )
        _ingestion_phase(league_code, "rounds")
        load_rounds_merged(ctx, league_code, league_id, seasons_list)
        _ingestion_phase(league_code, "teams")
        load_teams_merge_and_extend_ids(
            ctx, league_code, league_id, seasons_list, reference_season, team_ids
        )
        _ingestion_phase(league_code, "injuries")
        load_injuries_if_enabled(
            ctx, league_code, league_id, seasons_list, cov
        )
        _ingestion_phase(league_code, "transfers")
        load_transfers_if_enabled(ctx, league_code, team_ids)
        _ingestion_phase(league_code, "fixture_fanout (lineups/events/stats/predictions/...)")
        run_fixture_fanout_and_persist(
            ctx, league_code, fixtures_merged, fixture_ids, team_ids, cov
        )
        _ingestion_phase(league_code, "squad /players batch")
        load_squad_players_batch(ctx, league_code, seasons_list, team_ids)
    except Exception as e:
        ctx.errors.append(f"league {league_code}: {e}")
