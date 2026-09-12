"""Fetch /coachs per team → RAW_*_COACHES.

The /coachs endpoint does not accept league or season parameters — it must be
queried per team ID. We reuse the team_ids set already collected from the
fixtures and teams fetch phases.

Each response[i] contains the coach's biography, current club, and full career
history (all previous management stints with start/end dates).

Response structure (response[i]):
    id / name / firstname / lastname / nationality / age
    birth.date / birth.place / birth.country
    photo
    team.id / team.name          (current club, if active)
    career[j].team.id / .start / .end
"""

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
    """Fetch /coachs for every team ID and append to RAW_*_COACHES.

    One API call per team (no pagination). All teams' coach records are merged
    into one payload row appended per run, mirroring the squads pattern.
    """
    if not team_ids:
        return

    payload: dict = {"league_code": league_code, "response": []}

    # #896: one row per league, latest-per-league in staging, so a partial supersedes a good
    # snapshot. Complete or discard — see the same guard in loads/transfers.py.
    # NOTE the empty-response subtlety this must NOT get wrong: ~23 of 1,265 teams genuinely
    # have no coach on every run (measured over five nightlies, which is why COACHES never gates
    # completeness). An empty response with NO error is a COMPLETE answer and must stay one;
    # only `result_is_complete` — body error or latched quota flag — marks the run partial.
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
            # Before the next fetch: the quota flag latches for the rest of the run.
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
