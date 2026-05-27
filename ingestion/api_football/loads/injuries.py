"""Fetch /injuries per league per season → RAW_*_INJURIES.

One call per competition per season returns all recorded injuries for that
league season (players missing fixtures or marked questionable). No pagination.

Data refreshes every 4 hours on the API side. Our daily run at 04:00 UTC
captures the overnight state — sufficient for match preview availability lists.

Response structure (response[i]):
    player.id / player.name / player.type / player.reason
    team.id / team.name
    fixture.id / fixture.date
    league.id / league.season
"""

from __future__ import annotations

from .. import quota as errors_quota
from ..bigquery import load_json_to_bq
from ..http_client import fetch_merged_paged
from ..quota import append_api_errors
from ..settings import raw_table
from .context import PipelineContext


def load_injuries(
    ctx: PipelineContext,
    league_code: str,
    league_id: int,
    seasons_list: list[int],
) -> None:
    """Fetch /injuries for all configured seasons and append to RAW_*_INJURIES.

    Each season is a separate API call. All seasons' results are merged into
    one payload row appended per run — consistent with how standings and rounds
    are stored.
    """
    merged: dict | None = None

    for season in seasons_list:
        if errors_quota._http_quota_exhausted:
            break
        try:
            part = fetch_merged_paged(
                "/injuries",
                ctx.headers,
                {"league": league_id, "season": season},
                paginate=False,
            )
            append_api_errors(part, f"injuries {league_code} season={season}", ctx.errors)

            if merged is None:
                merged = {
                    k: v
                    for k, v in part.items()
                    if k not in ("response", "errors", "results", "paging")
                }
                merged["errors"] = []
                merged["response"] = []

            merged["errors"].extend(list(part.get("errors") or []))
            merged["response"].extend(part.get("response") or [])

        except Exception as e:
            ctx.errors.append(f"injuries {league_code} season={season}: {e}")

    if not merged:
        return

    merged["results"] = len(merged["response"])
    merged["paging"] = {"current": 1, "total": 1}

    try:
        load_json_to_bq(ctx.client, raw_table("INJURIES"), merged, as_json_payload=True, append=True, league_code=league_code)
        ctx.add_loaded(1)
    except Exception as e:
        ctx.errors.append(f"injuries BQ {league_code}: {e}")
