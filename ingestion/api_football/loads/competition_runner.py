"""Ingestion pipeline for a single competition.

Two entry points:
- run_cheap_phases(): catalog → fixtures → standings → teams → coaches.
  Returns CompetitionRunResult so the orchestrator can collect all competitions' state before
  running the global fanout pass.
- run_squads_for_competition(): squad /players batch, run after global fanout.

Every competition — domestic league, international tournament, qualifier — goes through
the same steps. All errors are caught per-competition so a failure in one does not abort
the others.
"""

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
    """A skip must be as visible as a run (#33 item 14).

    A phase that quietly stops doing anything is indistinguishable from a phase that broke —
    which is the failure class that cost this pipeline six silent days. The line carries the
    age and the next due date so "should this have run tonight?" is answerable from the log
    alone, without querying anything.
    """
    print(f"[api-football] league={league_code} phase={step} SKIPPED ({reason})", flush=True)


def run_poll_phases(
    ctx: PipelineContext,
    league_code: str,
    league_id: int,
    current_season: int | None = None,
    history_seasons: int | None = None,
    season_type: str = "split_year",
) -> tuple[set[int], int | None] | None:
    """Idle competition: catalog + latest-season fixtures only (detect new season / matches).

    Returns ``(team_ids, last_recorded_season)`` so the orchestrator can run the squad catch-up
    for finished competitions (the squad phases are otherwise full-mode only). None on
    unrecoverable error.
    """
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
        _fixtures_merged, team_ids, _fixture_ids = fetch_merge_and_persist_fixtures(
            ctx, league_code, league_id, seasons_list
        )
        last_season = max(seasons_list) if seasons_list else None
        return team_ids, last_season
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
    """Run all cheap (non-fanout) ingestion phases for one competition.

    Returns CompetitionRunResult on success, None on unrecoverable error.
    Errors are appended to ctx.errors; a None return means the competition
    cannot participate in the global fanout (e.g. catalog fetch failed).

    `coaches_last_ingest` is the run's single `latest_ingest_per_league(...COACHES)` result,
    read ONCE by the orchestrator before the per-competition loop (#33 item 14). Passing None
    means "no cadence information", which makes every league due — the safe default, and what
    keeps existing callers behaving exactly as before.
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
        # #33 item 14 — coaches change rarely; re-fetch on a 7-day cadence per league.
        # When not due the phase is skipped ENTIRELY: no fetch, and therefore no write.
        #
        # RAW_APIF_COACHES is APPEND-ONLY, and so is every other raw table (raw appends and
        # never deletes). `stg_apif__coaches` additionally reads ALL snapshots to preserve every
        # coach ever seen. So skipping loses nothing: the stored snapshots stay and base still
        # dedups to the latest.
        coaches_seen = (coaches_last_ingest or {}).get(league_code)
        if should_refetch(league_code, coaches_seen, utcnow()):
            _ingestion_phase(league_code, "coaches")
            load_coaches(ctx, league_code, team_ids)
        else:
            _skipped_phase(
                league_code, "coaches", skip_reason(league_code, coaches_seen, utcnow())
            )
            # COACHES is not in PER_TEAM_GATED today, so this changes nothing right now. Recorded
            # anyway: if it is ever promoted to a gating entity, the skip must already be visible
            # to the gate — otherwise it repeats the transfers failure with a fresh cause.
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
    """Run squad /players batch for one competition after global fanout.

    `already_captured` is the run's single `captured_player_team_seasons()` result, read
    once by the orchestrator before the loop and MUTATED as keys are written (#33 item 1).

    REQUIRED, with no default, and that is the guard. The orchestrator is this function's
    only caller, so a default would mean dropping the argument at the one call site
    silently restores the per-competition scan with every test still green. Omitting it is a
    TypeError instead.
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
    """Run /transfers batch for one competition's teams after global fanout.

    `transfers_last_ingest` is the run's single `latest_ingest_per_league(...TRANSFERS)` result
    (#33 item 14). None means "no cadence information" and every league is due — the safe
    default, and existing behaviour.
    """
    try:
        # #33 item 14 — transfers move in bursts (January, summer), not nightly. This was the
        # single most expensive phase in the run at 26.7 min. Skipped ENTIRELY when not due:
        # RAW_APIF_TRANSFERS is one row per league read latest-per-league in staging, so a
        # partial write would HIDE the complete row from every model downstream. It no longer
        # DELETES it (raw appends and never deletes), so this is recoverable now —
        # but a hidden snapshot is still a wrong warehouse until the next good run.
        seen = (transfers_last_ingest or {}).get(result.league_code)
        if not should_refetch(result.league_code, seen, utcnow()):
            _skipped_phase(
                result.league_code,
                "transfers batch",
                skip_reason(result.league_code, seen, utcnow()),
            )
            # The completeness gate fails a run when a per-team gap persists across TWO runs, on
            # the reasoning that one bad run heals on the next night's fetch. A skipped league
            # cannot heal — there is no fetch — so it must be told, or a pre-existing gap trips a
            # gate built for nightly fetches. That is exactly how one nightly died on
            # UCL/TRANSFERS.
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
    """Squad catch-up for finished (poll-mode) competitions.

    Captures /players/squads for teams whose competitions have all finished and that were not
    captured in-season — keyed by team, deduped across comps and against squads already stored
    for that season (club and national teams alike). Quota-guarded inside
    ``load_player_squads_batch``; any remainder resumes on the next run via the same dedup.
    """
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


