"""Fetch /players/teams per player → RAW_APIF_PLAYER_TEAMS (global per-player phase).

Career club/national history per player ({team, seasons[]} list), one call per player over the
current universe (see loads/player_universe.py). Players are grouped by provenance league_code
and landed one snapshot row per league, mirroring the team-keyed loaders. Already-ingested
players are skipped; the first run is the backfill, bounded by the daily quota guard and
resumed on later runs.
"""

from __future__ import annotations

import os

from .. import quota as errors_quota
from ..bigquery import load_json_to_bq
from ..settings import raw_table
from ..fixture_scheduling import player_teams_response_for_player
from .context import PipelineContext
from .player_universe import players_needing


def load_player_teams_global(
    ctx: PipelineContext,
    universe: list[tuple[int, str]] | None,
) -> None:
    """`universe` is the run's shared `_query_universe()` result — the same answer
    load_player_profiles_global just used, and nothing writes RAW_APIF_PLAYERS between the
    two phases, so re-running that full UNNEST bought nothing (#33 item 1).

    REQUIRED (it may be None, but it must be PASSED) — see load_player_profiles_global for
    why a default would make the hoist silently revertible.
    """
    if os.getenv("API_FOOTBALL_SKIP_PLAYER_TEAMS", "").strip().lower() in ("1", "true", "yes"):
        ctx.errors.append(
            "player_teams: skipped (API_FOOTBALL_SKIP_PLAYER_TEAMS set — use on low-quota archive runs)"
        )
        return
    try:
        by_league = players_needing(ctx.client, "PLAYER_TEAMS", universe=universe)
    except Exception as e:
        ctx.errors.append(f"player_teams universe: {e}")
        return
    for league_code in sorted(by_league):
        if errors_quota._http_quota_exhausted:
            break
        teams_payload = {"league_code": league_code, "response": []}
        for player_id in by_league[league_code]:
            if errors_quota._http_quota_exhausted:
                break
            try:
                team_rows, complete = player_teams_response_for_player(
                    ctx.headers,
                    player_id,
                    ctx.errors,
                    error_context=f"player_teams {league_code} player_id={player_id}",
                )
                # #896 applied to the CAPTURE side, same reader and same permanence as
                # player_profiles: `_existing_player_ids` keys on `$.player_id` presence, so an
                # empty career stored from a rate-limited call is never re-fetched.
                if not complete:
                    ctx.errors.append(
                        f"player_teams {league_code} player {player_id}: INCOMPLETE fetch — "
                        f"player SKIPPED, not marked ingested; retries next run"
                    )
                    continue
                teams_payload["response"].append(
                    {
                        "player_id": player_id,
                        "teams_payload": team_rows,
                    }
                )
            except Exception as e:
                ctx.errors.append(f"player_teams {league_code} player {player_id}: {e}")
        if not teams_payload["response"]:
            continue
        try:
            load_json_to_bq(
                ctx.client,
                raw_table("PLAYER_TEAMS"),
                teams_payload,
                as_json_payload=True,
                append=True,
                league_code=league_code,
            )
            ctx.add_loaded(1)
        except Exception as e:
            ctx.errors.append(f"player_teams BQ {league_code}: {e}")
