-- Dated player transfers, deduped. By-team fetching returns each move twice (once under
-- the team-in query, once under the team-out query), so we keep one row per distinct move
-- (player, team_in, team_out, transfer_date). Provider near-duplicates with DIFFERENT dates
-- (the same move recorded a few days apart under different `type`s) are kept as distinct
-- rows — a date-window merge would risk collapsing genuine repeat moves. transfer_type is
-- the raw provider string (no canonical taxonomy here).
-- league_code is INGEST PROVENANCE, not a semantic partition: a transfer is a global player
-- event and the same move can be fetched under more than one tracked league's team pull, so
-- the move is deduped ACROSS league_code (league_code is NOT in the partition); the surviving
-- league_code is pinned deterministically (latest ingest, then league_code asc).
-- Grain: (player_id, team_in_id, team_out_id, transfer_date).
with src as (
    select * from {{ ref('stg_apif__transfers') }}
    where
        player_id is not null
        and transfer_date is not null
        -- a move with neither side is meaningless (and would collide on the grain); a
        -- single missing side is legitimate (the provider omits team_in or team_out)
        and not (team_in_id is null and team_out_id is null)
)

select
    player_id,
    team_in_id,
    team_out_id,
    transfer_date,
    transfer_type,
    league_code,
    raw_ingested_at
from src
qualify row_number() over (
    partition by player_id, team_in_id, team_out_id, transfer_date
    order by raw_ingested_at desc, league_code asc
) = 1
