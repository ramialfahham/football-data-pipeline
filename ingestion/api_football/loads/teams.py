"""Fetch /teams for all configured seasons into RAW_*_TEAMS and extend the team_ids set.

Each run appends a complete snapshot and deletes nothing; staging reads the newest per league.
"""

from __future__ import annotations

from .. import quota as errors_quota
from ..bigquery import load_json_to_bq
from ..settings import raw_table
from ..quota import append_api_errors
from ..fixture_scheduling import team_ids_for_league
from ..http_client import fetch_merged_paged, result_is_complete
from .context import PipelineContext


def load_teams_merge_and_extend_ids(
    ctx: PipelineContext,
    league_code: str,
    league_id: int,
    seasons_list: list[int],
    reference_season: int,
    team_ids: set[int],
) -> None:
    # The row covers all configured seasons and staging reads latest-per-league, so a partial
    # snapshot must be discarded rather than written.
    complete = True
    teams_merged_envelope: dict | None = None
    try:
        for season in seasons_list:
            if errors_quota._http_quota_exhausted:
                complete = False
                break
            teams_part = fetch_merged_paged(
                "/teams",
                ctx.headers,
                {"league": league_id, "season": season},
                paginate=False,
            )
            # Before the next fetch: the quota flag latches for the rest of the run.
            if not result_is_complete(teams_part):
                complete = False
            append_api_errors(teams_part, f"teams {league_code} season={season}", ctx.errors)
            if teams_merged_envelope is None:
                teams_merged_envelope = {
                    k: v
                    for k, v in teams_part.items()
                    if k not in ("response", "errors", "results", "paging")
                }
                teams_merged_envelope["errors"] = []
                teams_merged_envelope["response"] = []
            teams_merged_envelope["errors"].extend(list(teams_part.get("errors") or []))
            # /teams items carry no league block; staging reads $.league.season per row.
            enriched_items = [
                {**item, "league": {"id": league_id, "season": season}}
                for item in (teams_part.get("response") or [])
            ]
            teams_merged_envelope["response"].extend(enriched_items)
        if teams_merged_envelope is not None:
            teams_merged_envelope["results"] = len(teams_merged_envelope["response"])
            teams_merged_envelope["paging"] = {"current": 1, "total": 1}
            if complete:
                load_json_to_bq(
                    ctx.client,
                    raw_table("TEAMS"),
                    teams_merged_envelope,
                    as_json_payload=True,
                    append=True,
                    league_code=league_code,
                )
                ctx.add_loaded(1)
            else:
                ctx.errors.append(
                    f"teams {league_code}: INCOMPLETE fetch — partial snapshot DISCARDED, prior "
                    f"snapshot kept (#896); retries next run"
                )
            # Runs even when the snapshot is discarded: later phases still need these team_ids.
            for item in teams_merged_envelope["response"]:
                team = item.get("team") or {}
                tid = team.get("id")
                if tid:
                    team_ids.add(int(tid))
    except Exception as e:
        ctx.errors.append(f"teams {league_code}: {e}")
        if not team_ids:
            try:
                extra = team_ids_for_league(
                    ctx.headers, league_id, reference_season, ctx.errors
                )
                team_ids.update(extra)
            except Exception as e2:
                ctx.errors.append(f"teams fallback {league_code}: {e2}")
