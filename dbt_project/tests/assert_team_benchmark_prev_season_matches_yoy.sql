-- A team benchmark's value at the same point last season equals int_team_profile__yoy's, for every
-- metric both serve, on the team's current domestic season: the two read rule R6 one way. Also
-- fails a value outside a domestic league, where rule R6 has none, and a benchmark metric the
-- catalogue does not hold, which the mart's rank would drop.

{{ config(store_failures = true) }}

with yoy as (
    select
        team_sk,
        league_code,
        season_api_year,
        metric_key,
        metric_value_prev_season
    from {{ ref('int_team_profile__yoy') }}
    unpivot include nulls (
        metric_value_prev_season for metric_key in (
            goals_per_match_prev_season as 'goals_per_match',
            goals_against_per_match_prev_season as 'goals_against_per_match',
            clean_sheets_pct_prev_season as 'clean_sheets_pct',
            shots_per_match_prev_season as 'shots_per_match',
            shots_inside_box_pct_prev_season as 'shots_inside_box_pct',
            shots_on_goal_per_match_prev_season as 'shots_on_goal_per_match',
            finishing_efficiency_pct_prev_season as 'finishing_efficiency_pct',
            duels_per_match_prev_season as 'duels_per_match',
            duels_won_pct_prev_season as 'duels_won_pct',
            defensive_actions_per_match_prev_season as 'defensive_actions_per_match',
            passes_per_match_prev_season as 'passes_per_match',
            passes_accuracy_pct_prev_season as 'passes_accuracy_pct',
            passes_key_per_match_prev_season as 'passes_key_per_match',
            corners_per_match_prev_season as 'corners_per_match',
            corners_against_per_match_prev_season as 'corners_against_per_match',
            saves_pct_prev_season as 'saves_pct'
        )
    )
),

benchmarks as (
    select
        team_sk,
        league_code,
        season_api_year,
        metric_key,
        metric_value_prev_season
    from {{ ref('mart_team_competition_benchmarks') }}
),

catalogue as (
    select metric_id
    from {{ ref('metric_catalogue') }}
    where entity = 'team'
),

mismatches as (
    select
        b.team_sk,
        b.league_code,
        b.season_api_year,
        b.metric_key,
        b.metric_value_prev_season as benchmark_prev,
        y.metric_value_prev_season as yoy_prev
    from benchmarks as b
    inner join yoy as y
        on
            b.team_sk = y.team_sk
            and b.league_code = y.league_code
            and b.season_api_year = y.season_api_year
            and b.metric_key = y.metric_key
    where
        (b.metric_value_prev_season is null) != (y.metric_value_prev_season is null)
        or abs(b.metric_value_prev_season - y.metric_value_prev_season) > 1e-9
),

registry as (
    select
        league_code,
        competition_type
    from {{ ref('competition_registry') }}
),

outside_domestic as (
    select
        b.team_sk,
        b.league_code,
        b.season_api_year,
        b.metric_key,
        b.metric_value_prev_season as benchmark_prev,
        cast(null as float64) as yoy_prev
    from benchmarks as b
    left join registry as r
        on b.league_code = r.league_code
    where
        b.metric_value_prev_season is not null
        and coalesce(r.competition_type, '') != 'domestic_league'
),

uncatalogued as (
    select distinct
        cast(null as int64) as team_sk,
        cast(null as string) as league_code,
        cast(null as int64) as season_api_year,
        l.metric_key,
        cast(null as float64) as benchmark_prev,
        cast(null as float64) as yoy_prev
    from {{ ref('int_team_competition_benchmark_metrics_long') }} as l
    left join catalogue as c
        on l.metric_key = c.metric_id
    where c.metric_id is null
)

select * from mismatches
union all
select * from outside_domestic
union all
select * from uncatalogued
