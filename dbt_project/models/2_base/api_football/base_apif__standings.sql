with src as (
    select
        league_code,
        league_api_id,
        league_name,
        season,
        team_id,
        team_name,
        standing_rank,
        points,
        goals_diff,
        form,
        group_description,
        played_all,
        wins_all,
        draws_all,
        losses_all,
        raw_ingested_at
    from {{ ref('stg_apif__standings') }}
    where
        team_id is not null
        and season is not null
),

deduped_standings as (
    select *
    from src
    qualify row_number() over (
        partition by league_code, season, team_id
        order by raw_ingested_at desc
    ) = 1
)

select
    league_code,
    league_api_id,
    league_name,
    season,
    team_id,
    team_name,
    standing_rank,
    points,
    goals_diff,
    form,
    group_description,
    played_all,
    wins_all,
    draws_all,
    losses_all,
    raw_ingested_at
from deduped_standings
