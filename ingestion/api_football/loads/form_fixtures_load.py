"""Per-team /fixtures?last=N form fetch → RAW_{league_code}_APIF_FORM_FIXTURES.

Used for competitions with form_source=all_internationals (e.g. WC26), where
pre-tournament form comes from fixtures across all competitions, not a single league.

Strategy: fetch last N fixtures for each participating team, merge into one
envelope keyed by team_id, and persist with WRITE_TRUNCATE (always latest state).
We don't merge with prior runs — each run is a fresh snapshot of current form.
"""

from __future__ import annotations

import os

from .. import errors_quota
from ..bq import load_json_to_bq
from ..config import raw_league_table, _env_int
from ..errors_quota import append_api_errors
from ..http_client import fetch_json
from .context import PipelineContext

_DEFAULT_LAST_N = 10


def load_form_fixtures(
    ctx: PipelineContext,
    league_code: str,
    team_ids: set[int],
) -> None:
    """Fetch last-N fixtures for each team and persist as a single batched envelope."""
    last_n = _env_int("API_FOOTBALL_FORM_FIXTURES_LAST_N", _DEFAULT_LAST_N)
    team_blocks: list[dict] = []

    for team_id in sorted(team_ids):
        if errors_quota._http_quota_exhausted:
            break
        try:
            result = fetch_json(
                "/fixtures",
                ctx.headers,
                {"team": team_id, "last": last_n},
            )
            append_api_errors(
                result,
                f"form_fixtures {league_code} team={team_id}",
                ctx.errors,
            )
            team_blocks.append({
                "team_id": team_id,
                "response": result.get("response") or [],
            })
            print(
                f"[api-football] form_fixtures league={league_code} team={team_id} "
                f"fixtures={len(result.get('response') or [])}",
                flush=True,
            )
        except Exception as e:
            ctx.errors.append(f"form_fixtures {league_code} team={team_id}: {e}")

    if not team_blocks:
        print(
            f"[api-football] form_fixtures league={league_code} no data fetched — skipping BQ write",
            flush=True,
        )
        return

    payload = {"league_code": league_code, "response": team_blocks}
    try:
        tbl = raw_league_table(league_code, "FORM_FIXTURES")
        load_json_to_bq(ctx.client, tbl, payload, as_json_payload=True)
        ctx.add_loaded(1)
        print(
            f"[api-football] form_fixtures league={league_code} "
            f"teams={len(team_blocks)} written to {tbl}",
            flush=True,
        )
    except Exception as e:
        ctx.errors.append(f"form_fixtures BQ {league_code}: {e}")
