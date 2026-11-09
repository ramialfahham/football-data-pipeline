"""Fetch /coachs per team (the endpoint takes no league or season) into RAW_*_COACHES."""

from __future__ import annotations

from .. import quota as errors_quota
from ..bigquery import load_json_to_bq
from ..http_client import fetch_merged_paged, result_is_complete
from ..quota import append_api_errors
from ..settings import raw_table
from .context import PipelineContext


def load_coaches(
    ctx: PipelineContext,
    league_code: str,
    team_ids: set[int],
) -> None:
    """Append one payload row holding every team's coach records, one API call per team."""
    if not team_ids:
        return

    payload: dict = {"league_code": league_code, "response": []}

    # Staging keeps the latest row per league, so a partial snapshot would supersede a good one:
    # write complete or discard. An empty error-free response is complete; only
    # `result_is_complete` (body error or latched quota flag) marks the run partial.
    complete = True
    for team_id in sorted(team_ids):
        if errors_quota._http_quota_exhausted:
            complete = False
            break
        try:
            data = fetch_merged_paged(
                "/coachs",
                ctx.headers,
                {"team": team_id},
                paginate=False,
            )
            # Checked before the next fetch because the quota flag latches for the rest of the run.
            if not result_is_complete(data):
                complete = False
            append_api_errors(
                data, f"coaches {league_code} team_id={team_id}", ctx.errors
            )
            for coach in data.get("response") or []:
                payload["response"].append(
                    {"team_id": team_id, "coach": coach}
                )
        except Exception as e:
            complete = False
            ctx.errors.append(f"coaches {league_code} team_id={team_id}: {e}")

    if not complete:
        ctx.errors.append(
            f"coaches {league_code}: INCOMPLETE fetch — partial snapshot DISCARDED, prior "
            f"snapshot kept (#896); retries next run"
        )
        return

    try:
        load_json_to_bq(ctx.client, raw_table("COACHES"), payload, as_json_payload=True, append=True, league_code=league_code)
        ctx.add_loaded(1)
    except Exception as e:
        ctx.errors.append(f"coaches BQ {league_code}: {e}")
