{#
  A match with a fetch in the provider's complete format takes its player stats from such a fetch,
  so a stat its newest complete fetch delivers is not blank for every player who played. Returns one
  row per model, match and stat (goals conceded, dribbled past) blank for every player with minutes
  in base_apif__fixture_players or fct_fixture_player_stats while that fetch has it for one of them.
#}
{{ config(store_failures = true, severity = 'error') }}

with fetches as (
    select
        league_code,
        fixture_id,
        raw_ingested_at,
        logical_or(goals_against is not null) as is_complete,
        logical_or(minutes_played > 0 and goals_against is not null) as has_goals_against,
        logical_or(minutes_played > 0 and dribbles_past is not null) as has_dribbles_against
    from {{ ref('stg_apif__fixture_players') }}
    where fixture_id is not null
    group by league_code, fixture_id, raw_ingested_at
),

newest_complete as (
    select
        league_code,
        fixture_id,
        array_agg(
            struct(has_goals_against, has_dribbles_against) order by raw_ingested_at desc limit 1
        )[offset(0)] as newest
    from fetches
    where is_complete
    group by league_code, fixture_id
),

held as (
    select
        'base_apif__fixture_players' as model_name,
        league_code,
        fixture_id,
        logical_or(goals_against is not null) as has_goals_against,
        logical_or(dribbles_against is not null) as has_dribbles_against
    from {{ ref('base_apif__fixture_players') }}
    where minutes > 0
    group by league_code, fixture_id
    union all
    select
        'fct_fixture_player_stats' as model_name,
        league_code,
        fixture_api_id as fixture_id,
        logical_or(goals_against is not null) as has_goals_against,
        logical_or(dribbles_against is not null) as has_dribbles_against
    from {{ ref('fct_fixture_player_stats') }}
    where minutes > 0
    group by league_code, fixture_api_id
)

select
    held.model_name,
    held.league_code,
    held.fixture_id,
    stat.stat_name as stat
from held
inner join newest_complete
    on
        held.league_code = newest_complete.league_code
        and held.fixture_id = newest_complete.fixture_id
cross join
    unnest([
        struct(
            'goals_against' as stat_name,
            newest_complete.newest.has_goals_against as in_fetch,
            held.has_goals_against as in_model
        ),
        struct(
            'dribbles_against' as stat_name,
            newest_complete.newest.has_dribbles_against as in_fetch,
            held.has_dribbles_against as in_model
        )
    ]) as stat
where stat.in_fetch and not stat.in_model
