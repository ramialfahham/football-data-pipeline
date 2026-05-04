"""One competition: catalog → core tables → fanout → squads."""

from __future__ import annotations

from .context import PipelineContext
from .fixture_fanout_load import run_fixture_fanout_and_persist
from .fixtures_load import fetch_merge_and_persist_fixtures
from .form_fixtures_load import load_form_fixtures
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
) -> None:
    try:
        _ingestion_phase(league_code, "catalog (leagues + season plan)")
        seasons_list, reference_season, cov = fetch_catalog_persist_and_plan(
            ctx, league_code, league_id
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
        if form_source == "supporting_leagues" and supporting_leagues:
            _ingestion_phase(league_code, "form fixtures (/fixtures?league={id}&season={year} per supporting league)")
            load_form_fixtures(ctx, league_code, supporting_leagues)
    except Exception as e:
        ctx.errors.append(f"league {league_code}: {e}")
