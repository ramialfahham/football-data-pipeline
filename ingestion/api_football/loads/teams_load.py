"""GET /teams (multi-season merge) → RAW_*_TEAMS; extends ``team_ids``."""

from __future__ import annotations

from .. import errors_quota
from ..bq import load_json_to_bq, read_latest_payload_json
from ..config import raw_league_table
from ..errors_quota import append_api_errors
from ..fanout import team_ids_for_league
from ..http_client import fetch_merged_paged
from .context import PipelineContext


def load_teams_merge_and_extend_ids(
    ctx: PipelineContext,
    league_code: str,
    league_id: int,
    seasons_list: list[int],
    reference_season: int,
    team_ids: set[int],
) -> None:
    teams_merged_envelope: dict | None = None
    try:
        for season in seasons_list:
            if errors_quota._http_quota_exhausted:
                break
            teams_part = fetch_merged_paged(
                "/teams",
                ctx.headers,
                {"league": league_id, "season": season},
                paginate=False,
            )
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
            # One row per (season, club); staging reads ``league.season`` on each row.
            teams_merged_envelope["response"].extend(teams_part.get("response") or [])
        if teams_merged_envelope is not None:
            teams_merged_envelope["results"] = len(teams_merged_envelope["response"])
            teams_merged_envelope["paging"] = {"current": 1, "total": 1}
            tm_tbl = raw_league_table(league_code, "TEAMS")
            prior = read_latest_payload_json(ctx.client, tm_tbl)
            teams_merged_envelope = merge_teams_envelope(prior, teams_merged_envelope)
            load_json_to_bq(
                ctx.client,
                tm_tbl,
                teams_merged_envelope,
                as_json_payload=True,
            )
            ctx.add_loaded(1)
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
