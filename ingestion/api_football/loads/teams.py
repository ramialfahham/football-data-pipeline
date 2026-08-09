"""Fetch /teams for all configured seasons → RAW_*_TEAMS; extends team_ids set.

Each run fetches all seasons and writes a fresh complete snapshot row; the API returns
the full team list on every call.

MERGE-ON-WRITE since #33 item 8b: the run appends its snapshot, then deletes this
league's older rows. The row covers ALL configured seasons, so nothing is lost —
staging already read only the latest row per league_code.
"""

from __future__ import annotations

from datetime import datetime, timezone

from .. import quota as errors_quota
from ..bigquery import delete_superseded_league_rows, load_json_to_bq
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
    # #896: one row per league covering ALL configured seasons, read latest-per-league in
    # staging, so losing a season to a quota cut silently shortens history and supersedes the
    # full snapshot. Complete or discard — same guard as loads/standings.py.
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
            # API-Football /teams response items contain only {team, venue} — no league
            # block. Inject (league.id, league.season) per item so downstream consumers
            # carry the season identity: staging views read $.league.season per row, and
            # merge_teams_envelope dedups on (team_id, season) via _team_row_key.
            # Without this, every team row is silently dropped by the merge and results=0.
            enriched_items = [
                {**item, "league": {"id": league_id, "season": season}}
                for item in (teams_part.get("response") or [])
            ]
            teams_merged_envelope["response"].extend(enriched_items)
        if teams_merged_envelope is not None:
            teams_merged_envelope["results"] = len(teams_merged_envelope["response"])
            teams_merged_envelope["paging"] = {"current": 1, "total": 1}
            if complete:
                ts = datetime.now(timezone.utc)
                load_json_to_bq(
                    ctx.client,
                    raw_table("TEAMS"),
                    teams_merged_envelope,
                    as_json_payload=True,
                    append=True,
                    league_code=league_code,
                    ingested_at=ts.isoformat(),
                )
                # #33 item 8b — see loads/transfers.py for why this is safe and why it
                # runs only past the completeness guard above.
                #
                # Caught HERE rather than by the outer `except`, unlike transfers and
                # standings. That handler has side effects this failure must not trigger:
                # it would skip the id extension below — which the comment there says runs
                # EITHER WAY, deliberately — and then spend an extra /teams call on the
                # `team_ids_for_league` fallback. A failed space reclaim must not cost the
                # run its team ids or an API call.
                try:
                    delete_superseded_league_rows(
                        ctx.client, raw_table("TEAMS"), league_code, ts
                    )
                except Exception as e:
                    ctx.errors.append(f"teams merge-delete {league_code}: {e}")
                ctx.add_loaded(1)
            else:
                ctx.errors.append(
                    f"teams {league_code}: INCOMPLETE fetch — partial snapshot DISCARDED, prior "
                    f"snapshot kept (#896); retries next run"
                )
            # The id extension runs EITHER WAY, deliberately. It is not a write to raw; it is
            # what feeds team_ids to the coaches / transfers / squads phases below. Withholding
            # it on a degraded run would starve them of teams they could still have fetched,
            # turning one short season into a run-wide outage. The discarded snapshot above is
            # about not superseding stored data — a different question from what this run may
            # still attempt.
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
