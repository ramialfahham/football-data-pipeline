"""Fetch /transfers per team (batched) → RAW_APIF_TRANSFERS.

Each run fetches the full transfer history for all teams and writes a fresh snapshot
row. Transfers are not season-scoped — one /transfers?team= call returns all of a
team's players' moves. Fetching by team returns each move twice (once per involved
team); the base model dedups.

APPEND ONLY since 2026-08-17 (CPO: raw appends and never deletes). The run appends its
snapshot and removes nothing, so every earlier snapshot survives. `stg_apif__transfers`
selects the newest row per league_code, so the older ones are simply not selected — they
are there for the case this rule exists for, a later answer that carries LESS than the one
it would have replaced. That case is sharpest in this loader: with an empty `team_ids` the
fetch loop never runs and the payload is empty while `complete` stays True, which under
merge-on-write would have wiped the league's entire transfer history. The merge-on-write of
#33 item 8b was removed here; see docs/data_contract.md, "Raw appends and never deletes".
"""

from __future__ import annotations

import os

from .. import quota as errors_quota
from ..bigquery import load_json_to_bq
from ..settings import raw_table
from ..fixture_scheduling import transfers_response_for_team
from .context import PipelineContext


def load_transfers_batch(
    ctx: PipelineContext,
    league_code: str,
    team_ids: set[int],
) -> None:
    # ⚠ THE GUARD `coaches.py:38` HAS AND THIS ONE DID NOT, until 2026-08-17. With an empty
    # `team_ids` the fetch loop below never runs, `complete` stays True, and an EMPTY whole-league
    # payload is written as fact. `stg_apif__transfers` reads the latest row per league, so that
    # empty snapshot hides the real transfer history from every model downstream. Under the
    # merge-on-write this loader carried until `!59` it also DELETED it outright.
    # Reachable: `fixtures.py` returns an empty team set on an empty fixtures response, and
    # `competition_runner.py` calls this unconditionally. Compounding it, `completeness.py` drops
    # leagues with no `team_ids` from the expected set, so the check that exists to catch this is
    # blind to exactly this case.
    if not team_ids:
        ctx.errors.append(
            f"transfers {league_code}: no team ids this run — SKIPPED, prior snapshot kept"
        )
        return
    transfers_payload = {"league_code": league_code, "response": []}
    if os.getenv("API_FOOTBALL_SKIP_TRANSFERS", "").strip().lower() in ("1", "true", "yes"):
        ctx.errors.append(
            f"transfers {league_code}: skipped (API_FOOTBALL_SKIP_TRANSFERS set — use on low-quota archive runs)"
        )
        return
    # #896: this payload is ONE row for the whole league, and staging reads the latest row per
    # league_code. So it is complete or it is worthless — there is no per-team key to withhold
    # the way squads.py can. Any team that could not be fetched cleanly makes the snapshot
    # partial, and a partial must not supersede the good one already stored.
    complete = True
    for team_id in sorted(team_ids):
        if errors_quota._http_quota_exhausted:
            complete = False
            break
        try:
            transfers_rows, team_complete = transfers_response_for_team(
                ctx.headers,
                team_id,
                ctx.errors,
                error_context=f"transfers {league_code} team_id={team_id}",
            )
            if not team_complete:
                complete = False
                continue
            transfers_payload["response"].append(
                {
                    "team_id": team_id,
                    "transfers_payload": transfers_rows,
                }
            )
        except Exception as e:
            complete = False
            ctx.errors.append(f"transfers {league_code} team {team_id}: {e}")
    if not complete:
        # Discard rather than supersede. Raw is append-only, so the stored snapshot survives
        # either way — but `stg_apif__transfers` reads the LATEST row per league, so writing a
        # partial here would still hide the good snapshot from every model downstream. Not
        # deleting it is what makes that recoverable rather than permanent.
        ctx.errors.append(
            f"transfers {league_code}: INCOMPLETE fetch — partial snapshot DISCARDED, prior "
            f"snapshot kept (#896); retries next run"
        )
        return
    try:
        # Append only. The delete that used to follow this write was removed 2026-08-17 (CPO:
        # raw appends and never deletes). `stg_apif__transfers` already selects the newest row
        # per league_code. This loader is the sharpest illustration of why the delete had to
        # go: with an empty `team_ids` the loop above never runs, `complete` stays True, and
        # the delete would wipe the league's entire transfer history behind an empty payload
        # with no error anywhere. (The missing empty-team_ids guard itself is MR2, not this
        # task — append-only already makes that case recoverable instead of fatal.)
        load_json_to_bq(
            ctx.client,
            raw_table("TRANSFERS"),
            transfers_payload,
            as_json_payload=True,
            append=True,
            league_code=league_code,
        )
        ctx.add_loaded(1)
    except Exception as e:
        ctx.errors.append(f"transfers BQ {league_code}: {e}")
