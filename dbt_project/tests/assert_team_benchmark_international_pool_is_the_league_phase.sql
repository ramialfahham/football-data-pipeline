{#
  An international club competition with a league or group phase is benchmarked over that phase
  alone. Recomputed here from the match legs, apart from the model: for each such competition-season
  the teams with at least var team_min_matches matches in a table round, and their goals per match
  over those matches. Returns a benchmarked team outside that pool, a pool team with no benchmark,
  and a goals-per-match value that differs from the phase's.
#}
{{ config(store_failures = true, severity = 'error') }}

with competitions as (
    select league_code
    from {{ ref('dim_league') }}
    where
        entity_type = 'club'
        and competition_type not in ('domestic_league', 'domestic_cup')
),

table_rounds as (
    select
        league_code,
        season_api_year,
        round_name
    from {{ ref('int_round_names') }}
    where round_stage_kind = 'table'
),

phase as (
    select
        legs.team_sk,
        legs.season_sk,
        count(*) as matches,
        safe_divide(
            sum(if(legs.is_awarded_result, null, legs.goals)),
            countif(not legs.is_awarded_result)
        ) as goals_per_match
    from {{ ref('int_legs__team_match') }} as legs
    inner join competitions as c
        on legs.league_code = c.league_code
    inner join table_rounds as r
        on
            legs.league_code = r.league_code
            and legs.season_api_year = r.season_api_year
            and legs.round_name = r.round_name
    group by legs.team_sk, legs.season_sk
),

pool as (
    select * from phase
    where matches >= {{ var('team_min_matches') }}
),

phase_seasons as (
    select distinct season_sk from phase
),

benchmarked as (
    select
        b.team_sk,
        b.season_sk,
        b.metric_value
    from {{ ref('mart_team_competition_benchmarks') }} as b
    inner join phase_seasons as s
        on b.season_sk = s.season_sk
    where b.metric_key = 'goals_per_match'
)

select
    b.metric_value as benchmarked_goals_per_match,
    p.goals_per_match as phase_goals_per_match,
    coalesce(b.team_sk, p.team_sk) as team_sk,
    coalesce(b.season_sk, p.season_sk) as season_sk,
    case
        when p.team_sk is null then 'benchmarked outside the league phase pool'
        when b.team_sk is null then 'league phase team with no benchmark'
        else 'goals per match differs from the league phase'
    end as failure
from benchmarked as b
full outer join pool as p
    on b.team_sk = p.team_sk and b.season_sk = p.season_sk
where
    p.team_sk is null
    or b.team_sk is null
    or abs(b.metric_value - p.goals_per_match) > 1e-9
