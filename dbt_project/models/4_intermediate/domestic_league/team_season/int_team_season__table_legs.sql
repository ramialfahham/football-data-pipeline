{#
  Every leg a domestic league season holds, for its official table at every kick-off: each team's
  league match legs with their round kind, and each result the official table held for a time and
  that was later annulled (standings_temporary_results), as one leg per team. A leg counts in the
  table from counts_from, until counts_until where it is set: a played table match from its
  kick-off, a temporary result between its dates.

  Grain: (league_code, season_api_year, team_sk, leg_key).
#}

with registry as (
    select league_code
    from {{ ref('competition_registry') }}
    where competition_type = 'domestic_league'
),

round_kinds as (
    select
        league_code,
        season_api_year,
        round_name,
        round_stage_kind
    from {{ ref('int_round_names') }}
),

league_legs as (
    select
        l.league_code,
        l.season_api_year,
        l.fixture_sk,
        l.kickoff_datetime,
        l.team_sk,
        l.opponent_team_sk,
        l.home_away,
        l.goals,
        l.goals_against,
        l.result,
        rk.round_stage_kind,
        case l.result when 'W' then 3 when 'D' then 1 else 0 end + if(l.is_table_shootout_win, 1, 0) as points
    from {{ ref('int_legs__team_match') }} as l
    inner join registry as r
        on l.league_code = r.league_code
    left join round_kinds as rk
        on
            l.league_code = rk.league_code
            and l.season_api_year = rk.season_api_year
            and l.round_name = rk.round_name
),

temporary_results as (
    select * from {{ ref('standings_temporary_results') }}
),

-- a result the official table held for a time, as one leg per team
temporary_legs as (
    select
        league_code,
        season as season_api_year,
        home_team_id as team_sk,
        away_team_id as opponent_team_sk,
        'home' as home_away,
        home_goals as goals,
        away_goals as goals_against,
        from_date,
        to_date
    from temporary_results
    union all
    select
        league_code,
        season as season_api_year,
        away_team_id as team_sk,
        home_team_id as opponent_team_sk,
        'away' as home_away,
        away_goals as goals,
        home_goals as goals_against,
        from_date,
        to_date
    from temporary_results
)

select
    league_code,
    season_api_year,
    cast(fixture_sk as string) as leg_key,
    fixture_sk,
    kickoff_datetime,
    team_sk,
    opponent_team_sk,
    home_away,
    goals,
    goals_against,
    result,
    points,
    round_stage_kind,
    kickoff_datetime as counts_from,
    cast(null as timestamp) as counts_until,
    false as is_temporary
from league_legs
union all
select
    league_code,
    season_api_year,
    concat('temporary-', from_date) as leg_key,
    cast(null as int64) as fixture_sk,
    cast(null as timestamp) as kickoff_datetime,
    team_sk,
    opponent_team_sk,
    home_away,
    goals,
    goals_against,
    case when goals > goals_against then 'W' when goals < goals_against then 'L' else 'D' end as result,
    case when goals > goals_against then 3 when goals < goals_against then 0 else 1 end as points,
    'table' as round_stage_kind,
    timestamp(from_date) as counts_from,
    timestamp(date_add(to_date, interval 1 day)) as counts_until,
    true as is_temporary
from temporary_legs
