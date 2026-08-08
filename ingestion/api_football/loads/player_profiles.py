"""Fetch /players/profiles per player → RAW_APIF_PLAYER_PROFILES (global per-player phase).

Rich bio (name, DOB, birthplace, nationality, height, weight, number, position, photo), one
call per player over the current universe (see loads/player_universe.py). Players are grouped
by provenance league_code and landed one snapshot row per league, mirroring the team-keyed
loaders. Already-ingested players are skipped (bio is static), so the daily run stays cheap;
the first run is the backfill, bounded by the daily quota guard and resumed on later runs.
"""

from __future__ import annotations

import os

from .. import quota as errors_quota
from ..bigquery import load_json_to_bq
from ..settings import raw_table
from ..fixture_scheduling import profiles_response_for_player
from .context import PipelineContext
from .player_universe import players_needing


def load_player_profiles_global(
    ctx: PipelineContext,
    universe: list[tuple[int, str]] | None,
) -> None:
    """`universe` is the run's shared `_query_universe()` result — see load_player_teams_global,
    which needs the identical answer, and loads/player_universe.players_needing (#33 item 1).

    REQUIRED (it may be None, but it must be PASSED). The orchestrator is the only caller, so
    a default would let the shared universe be dropped at that one call site without any test
    noticing, silently restoring the duplicate full UNNEST of RAW_APIF_PLAYERS.
    """
    if os.getenv("API_FOOTBALL_SKIP_PLAYER_PROFILES", "").strip().lower() in ("1", "true", "yes"):
        ctx.errors.append(
            "player_profiles: skipped (API_FOOTBALL_SKIP_PLAYER_PROFILES set — use on low-quota archive runs)"
        )
        return
    try:
        by_league = players_needing(ctx.client, "PLAYER_PROFILES", universe=universe)
    except Exception as e:
        ctx.errors.append(f"player_profiles universe: {e}")
        return
    for league_code in sorted(by_league):
        if errors_quota._http_quota_exhausted:
            break
        profiles_payload = {"league_code": league_code, "response": []}
        for player_id in by_league[league_code]:
            if errors_quota._http_quota_exhausted:
                break
            try:
                profile_rows = profiles_response_for_player(
                    ctx.headers,
                    player_id,
                    ctx.errors,
                    error_context=f"player_profiles {league_code} player_id={player_id}",
                )
                profiles_payload["response"].append(
                    {
                        "player_id": player_id,
                        "profile_payload": profile_rows,
                    }
                )
            except Exception as e:
                ctx.errors.append(f"player_profiles {league_code} player {player_id}: {e}")
        if not profiles_payload["response"]:
            continue
        try:
            load_json_to_bq(
                ctx.client,
                raw_table("PLAYER_PROFILES"),
                profiles_payload,
                as_json_payload=True,
                append=True,
                league_code=league_code,
            )
            ctx.add_loaded(1)
        except Exception as e:
            ctx.errors.append(f"player_profiles BQ {league_code}: {e}")
