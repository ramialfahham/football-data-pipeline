"""Current-player universe for the global per-player pulls (profiles + teams).

The per-player endpoints (/players/profiles, /players/teams) are keyed by player, not team,
so they need the set of players we currently care about. That set is derived from the roster
we already ingest — RAW_APIF_PLAYERS — entirely within the raw layer (no dbt dependency):
distinct players rostered in season >= MIN_SEASON, each assigned a deterministic provenance
league_code (MIN over the leagues that surfaced them — league_code is ingest provenance, not
identity; mirrors the transfers rule).

To keep the daily run cheap (bio/career are static/slow-moving) the universe is filtered to
players NOT already present in the target raw table — first run fetches everyone (the backfill,
quota-guarded across days), later runs fetch only newly-rostered players.
"""

from __future__ import annotations

import os

from google.cloud import bigquery
from google.api_core.exceptions import NotFound

from ..settings import DATASET_ID, GCP_PROJECT_ID, raw_table


def _min_season() -> int:
    raw = os.getenv("API_FOOTBALL_PLAYER_UNIVERSE_MIN_SEASON", "").strip()
    if raw:
        try:
            return int(raw)
        except ValueError:
            pass
    return 2025


def _fq(entity: str) -> str:
    return f"`{GCP_PROJECT_ID}.{DATASET_ID}.{raw_table(entity)}`"


def _query_universe(client: bigquery.Client, min_season: int) -> list[tuple[int, str]]:
    """(player_id, provenance_league_code) for players rostered in season >= min_season."""
    sql = f"""
    with latest as (
        -- A players snapshot may span MULTIPLE rows (chunked when it would exceed BigQuery's
        -- 100 MB per-row limit; all chunks share one ingested_at). Keep every row of the latest
        -- snapshot, not just one — mirrors stg_apif__players.sql. See loads/squads.py.
        select payload, league_code
        from {_fq('PLAYERS')}
        qualify ingested_at = max(ingested_at) over (partition by league_code)
    ),
    players as (
        select
            latest.league_code,
            safe_cast(json_value(team_block, '$.season') as int64) as season,
            safe_cast(json_value(player_el, '$.player.id') as int64) as player_id
        from latest,
            unnest(json_query_array(json_query(latest.payload, '$.response'), '$')) as team_block,
            unnest(json_query_array(json_query(team_block, '$.players_payload'), '$')) as player_el
    )
    select player_id, min(league_code) as provenance_league_code
    from players
    where season >= @min_season and player_id is not null
    group by player_id
    """
    job_config = bigquery.QueryJobConfig(
        query_parameters=[bigquery.ScalarQueryParameter("min_season", "INT64", min_season)]
    )
    return [
        (int(row["player_id"]), str(row["provenance_league_code"]))
        for row in client.query(sql, job_config=job_config).result()
    ]


def _existing_player_ids(client: bigquery.Client, target_entity: str) -> set[int]:
    """player_ids already landed in the target raw table (any snapshot). Empty if it does
    not exist yet (first run)."""
    sql = f"""
    select distinct safe_cast(json_value(item, '$.player_id') as int64) as player_id
    from {_fq(target_entity)},
        unnest(json_query_array(json_query(payload, '$.response'), '$')) as item
    where safe_cast(json_value(item, '$.player_id') as int64) is not null
    """
    try:
        return {int(row["player_id"]) for row in client.query(sql).result()}
    except NotFound:
        return set()


def players_needing(
    client: bigquery.Client,
    target_entity: str,
    min_season: int | None = None,
) -> dict[str, list[int]]:
    """Players to fetch for `target_entity`, grouped by provenance league_code.

    = current universe (rostered season >= min_season) minus players already in the target.
    """
    ms = _min_season() if min_season is None else min_season
    already = _existing_player_ids(client, target_entity)
    by_league: dict[str, list[int]] = {}
    for player_id, league_code in _query_universe(client, ms):
        if player_id in already:
            continue
        by_league.setdefault(league_code, []).append(player_id)
    for league_code in by_league:
        by_league[league_code].sort()
    return by_league
