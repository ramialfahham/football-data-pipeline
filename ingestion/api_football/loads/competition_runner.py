"""Per-competition ingestion phases; an error in one competition does not abort the others."""

from __future__ import annotations

from datetime import datetime

from ..refetch import should_refetch, skip_reason, utcnow
from .context import CompetitionRunResult, PipelineContext
from .coaches import load_coaches
from .fixtures import fetch_merge_and_persist_fixtures
from .catalog import fetch_catalog_persist_and_plan
from .squads import load_squad_players_batch
from .player_squads import (
    captured_team_seasons,
    load_player_squads_batch,
    select_squad_catchup_team_ids,
)
from .transfers import load_transfers_batch
from .standings import load_standings_if_enabled
from .teams import load_teams_merge_and_extend_ids


def _ingestion_phase(league_code: str, step: str) -> None:
    print(f"[api-football] league={league_code} phase={step}", flush=True)


def _skipped_phase(league_code: str, step: str, reason: str) -> None:
    """Log a skipped phase so a skip is distinguishable from a broken phase."""
    print(f"[api-football] league={league_code} phase={step} SKIPPED ({reason})", flush=True)


def run_poll_phases(
    ctx: PipelineContext,
    league_code: str,
    league_id: int,
    current_season: int | None = None,
    history_seasons: int | None = None,
    season_type: str = "split_year",
) -> CompetitionRunResult | None:
    """Idle competition: catalog and latest-season fixtures only; None on unrecoverable error."""
    try:
        _ingestion_phase(league_code, "poll catalog (leagues + latest season plan)")
        seasons_list, _reference_season, cov = fetch_catalog_persist_and_plan(
            ctx,
            league_code,
            league_id,
            current_season=current_season,
            history_seasons=history_seasons,
            season_type=season_type,
            poll_mode=True,
        )
        _ingestion_phase(league_code, "poll fixtures (latest season only)")
        fixtures_merged, team_ids, fixture_ids = fetch_merge_and_persist_fixtures(
            ctx, league_code, league_id, seasons_list
        )
        return CompetitionRunResult(
            league_code=league_code,
            seasons_list=seasons_list,
            fixtures_merged=fixtures_merged,
            fixture_ids=fixture_ids,
            team_ids=team_ids,
            cov=cov,
        )
    except Exception as e:
        ctx.errors.append(f"league {league_code} poll phases: {e}")
        return None


def run_cheap_phases(
    ctx: PipelineContext,
    league_code: str,
    league_id: int,
    current_season: int | None = None,
    history_seasons: int | None = None,
    season_type: str = "split_year",
    coaches_last_ingest: dict[str, datetime] | None = None,
) -> CompetitionRunResult | None:
    """Run the non-fanout phases for one competition; None means it cannot join the global fanout.

    `coaches_last_ingest` None means "no cadence information", which makes every league due.
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
        # A skipped coaches phase writes nothing; raw is append-only, so stored snapshots stay.
        coaches_seen = (coaches_last_ingest or {}).get(league_code)
        if should_refetch(league_code, coaches_seen, utcnow()):
            _ingestion_phase(league_code, "coaches")
            load_coaches(ctx, league_code, team_ids)
        else:
            _skipped_phase(
                league_code, "coaches", skip_reason(league_code, coaches_seen, utcnow())
            )
            # Recorded so the completeness gate sees the skip if COACHES ever becomes gated.
            ctx.record_skipped(league_code, "COACHES")
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
    already_captured: set[tuple[int, int]],
) -> None:
    """Run the squad /players batch for one competition after the global fanout.

    `already_captured` is mutated as keys are written and has no default, so omitting it fails
    instead of silently restoring a per-competition scan.
    """
    try:
        _ingestion_phase(result.league_code, "squad /players batch")
        load_squad_players_batch(
            ctx,
            result.league_code,
            result.seasons_list,
            result.team_ids,
            reference_season=max(result.seasons_list) if result.seasons_list else None,
            already_captured=already_captured,
        )
    except Exception as e:
        ctx.errors.append(f"league {result.league_code} squads: {e}")


def run_transfers_for_competition(
    ctx: PipelineContext,
    result: CompetitionRunResult,
    transfers_last_ingest: dict[str, datetime] | None = None,
) -> None:
    """Run the /transfers batch for one competition; None `transfers_last_ingest` makes all due."""
    try:
        # Skipped entirely when not due: staging reads RAW_APIF_TRANSFERS latest-per-league, so a
        # partial write would hide the complete row from every model downstream.
        seen = (transfers_last_ingest or {}).get(result.league_code)
        if not should_refetch(result.league_code, seen, utcnow()):
            _skipped_phase(
                result.league_code,
                "transfers batch",
                skip_reason(result.league_code, seen, utcnow()),
            )
            # The completeness gate expects a gap to heal on the next fetch; a skipped league
            # never fetches, so it must be recorded or an old gap trips the gate.
            ctx.record_skipped(result.league_code, "TRANSFERS")
            return
        _ingestion_phase(result.league_code, "transfers batch")
        load_transfers_batch(ctx, result.league_code, result.team_ids)
    except Exception as e:
        ctx.errors.append(f"league {result.league_code} transfers: {e}")


def run_player_squads_for_competition(
    ctx: PipelineContext,
    result: CompetitionRunResult,
) -> None:
    """Run /players/squads batch for one competition's teams after global fanout."""
    try:
        _ingestion_phase(result.league_code, "player_squads batch")
        season = max(result.seasons_list) if result.seasons_list else None
        load_player_squads_batch(ctx, result.league_code, result.team_ids, season=season)
    except Exception as e:
        ctx.errors.append(f"league {result.league_code} player_squads: {e}")


def run_player_squads_catchup(
    ctx: PipelineContext,
    finished_comps: list[tuple[str, int, set[int]]],
    active_team_ids: set[int],
) -> None:
    """Capture /players/squads for teams of finished competitions not captured in-season."""
    if not finished_comps:
        return
    already = captured_team_seasons(ctx)
    plan = select_squad_catchup_team_ids(finished_comps, active_team_ids, already)
    for league_code, season, team_ids in plan:
        try:
            _ingestion_phase(league_code, "player_squads catch-up (finished comp)")
            load_player_squads_batch(
                ctx, league_code, team_ids, season=season, require_complete=True
            )
        except Exception as e:
            ctx.errors.append(f"league {league_code} player_squads catch-up: {e}")
