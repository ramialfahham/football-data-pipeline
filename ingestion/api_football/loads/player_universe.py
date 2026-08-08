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
    with all_snapshots as (
        -- RAW_APIF_PLAYERS stores one row per (team, season); read ALL rows faithfully (no
        -- latest-snapshot qualify) — the universe is a player_id SET, deduped by the group by
        -- below, so reading every row only adds duplicates that collapse. Mirrors stg_apif__players.
        select payload, league_code
        from {_fq('PLAYERS')}
    ),
    players as (
        select
            all_snapshots.league_code,
            safe_cast(json_value(team_block, '$.season') as int64) as season,
            safe_cast(json_value(player_el, '$.player.id') as int64) as player_id
        from all_snapshots,
            unnest(json_query_array(json_query(all_snapshots.payload, '$.response'), '$')) as team_block,
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


def query_player_universe(
    client: bigquery.Client,
    min_season: int | None = None,
) -> list[tuple[int, str]]:
    """Public entry point for the run-level universe read (#33 item 1).

    Exists so the orchestrator can compute the universe ONCE and hand the same list to both
    per-player loaders, without reaching into `_query_universe`. Applies the same default
    `min_season` those loaders would, so the shared result is identical to what each would
    have computed alone.
    """
    return _query_universe(client, _min_season() if min_season is None else min_season)


def players_needing(
    client: bigquery.Client,
    target_entity: str,
    min_season: int | None = None,
    universe: list[tuple[int, str]] | None = None,
) -> dict[str, list[int]]:
    """Players to fetch for `target_entity`, grouped by provenance league_code.

    = current universe (rostered season >= min_season) minus players already in the target.

    `universe` lets the caller supply an already-computed `_query_universe()` result. That
    query UNNESTs all of RAW_APIF_PLAYERS twice per run — once for PLAYER_PROFILES, once
    for PLAYER_TEAMS — for an identical answer, because nothing writes RAW_APIF_PLAYERS
    between the two calls (#33 item 1).

    `_existing_player_ids` is deliberately NOT shareable: it reads the TARGET table, which
    differs per call and is written between them.
    """
    ms = _min_season() if min_season is None else min_season
    already = _existing_player_ids(client, target_entity)
    by_league: dict[str, list[int]] = {}
    for player_id, league_code in (
        _query_universe(client, ms) if universe is None else universe
    ):
        if player_id in already:
            continue
        by_league.setdefault(league_code, []).append(player_id)
    for league_code in by_league:
        by_league[league_code].sort()
    return by_league
