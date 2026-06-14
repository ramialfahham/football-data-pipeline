"""Ingestion pipeline for a single competition.

Two entry points:
- run_cheap_phases(): catalog → fixtures → standings → teams → injuries → coaches.
  Returns CompetitionRunResult so the orchestrator can collect all competitions' state before
  running the global fanout pass.
- run_squads_for_competition(): squad /players batch, run after global fanout.

Every competition — domestic league, international tournament, qualifier — goes through
the same steps. All errors are caught per-competition so a failure in one does not abort
the others.
"""

from __future__ import annotations

from .context import CompetitionRunResult, PipelineContext
from .coaches import load_coaches
from .fixtures import fetch_merge_and_persist_fixtures
from .catalog import fetch_catalog_persist_and_plan
from .injuries import load_injuries
from .squads import load_squad_players_batch
from .transfers import load_transfers_batch
from .standings import load_standings_if_enabled
from .teams import load_teams_merge_and_extend_ids


def _ingestion_phase(league_code: str, step: str) -> None:
    print(f"[api-football] league={league_code} phase={step}", flush=True)


def run_poll_phases(
    ctx: PipelineContext,
    league_code: str,
    league_id: int,
    current_season: int | None = None,
    history_seasons: int | None = None,
    season_type: str = "split_year",
) -> None:
    """Idle competition: catalog + latest-season fixtures only (detect new season / matches)."""
    try:
        _ingestion_phase(league_code, "poll catalog (leagues + latest season plan)")
        seasons_list, _reference_season, _cov = fetch_catalog_persist_and_plan(
            ctx,
            league_code,
            league_id,
            current_season=current_season,
            history_seasons=history_seasons,
            season_type=season_type,
            poll_mode=True,
        )
        _ingestion_phase(league_code, "poll fixtures (latest season only)")
        fetch_merge_and_persist_fixtures(ctx, league_code, league_id, seasons_list)
    except Exception as e:
        ctx.errors.append(f"league {league_code} poll phases: {e}")


def run_cheap_phases(
    ctx: PipelineContext,
    league_code: str,
    league_id: int,
    current_season: int | None = None,
    history_seasons: int | None = None,
    season_type: str = "split_year",
) -> CompetitionRunResult | None:
    """Run all cheap (non-fanout) ingestion phases for one competition.

    Returns CompetitionRunResult on success, None on unrecoverable error.
    Errors are appended to ctx.errors; a None return means the competition
    cannot participate in the global fanout (e.g. catalog fetch failed).
    """
    try:
        _ingestion_phase(league_code, "catalog (leagues + season plan)")
        seasons_list, reference_season, cov = fetch_catalog_persist_and_plan(
            ctx,
            league_code,
            league_id,
            current_season=current_season,
            history_seasons=history_seasons,
            season_type=season_type,
        )
        _ingestion_phase(league_code, "fixtures (/fixtures merge -> BQ)")
        fixtures_merged, team_ids, fixture_ids = fetch_merge_and_persist_fixtures(
            ctx, league_code, league_id, seasons_list
        )
        _ingestion_phase(league_code, "standings")
        load_standings_if_enabled(ctx, league_code, league_id, seasons_list, cov)
        _ingestion_phase(league_code, "teams")
        load_teams_merge_and_extend_ids(
            ctx, league_code, league_id, seasons_list, reference_season, team_ids
        )
        _ingestion_phase(league_code, "injuries")
        load_injuries(ctx, league_code, league_id, seasons_list)
        _ingestion_phase(league_code, "coaches")
        load_coaches(ctx, league_code, team_ids)
        return CompetitionRunResult(
            league_code=league_code,
            seasons_list=seasons_list,
            fixtures_merged=fixtures_merged,
            fixture_ids=fixture_ids,
            team_ids=team_ids,
            cov=cov,
        )
    except Exception as e:
        ctx.errors.append(f"league {league_code} cheap phases: {e}")
        return None


def run_squads_for_competition(
    ctx: PipelineContext,
    result: CompetitionRunResult,
) -> None:
    """Run squad /players batch for one competition after global fanout."""
    try:
        _ingestion_phase(result.league_code, "squad /players batch")
        load_squad_players_batch(ctx, result.league_code, result.seasons_list, result.team_ids)
    except Exception as e:
        ctx.errors.append(f"league {result.league_code} squads: {e}")


def run_transfers_for_competition(
    ctx: PipelineContext,
    result: CompetitionRunResult,
) -> None:
    """Run /transfers batch for one competition's teams after global fanout."""
    try:
        _ingestion_phase(result.league_code, "transfers batch")
        load_transfers_batch(ctx, result.league_code, result.team_ids)
    except Exception as e:
        ctx.errors.append(f"league {result.league_code} transfers: {e}")


