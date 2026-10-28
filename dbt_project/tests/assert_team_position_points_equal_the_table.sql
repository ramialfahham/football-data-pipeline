{#
  The points behind every position in int_team_season__position_by_match against the official
  table: at the table's matches played, a team's points must equal the table's points plus the
  points the league took, declared in seeds/standings_points_adjustments.csv. One row per team
  whose points differ. A deduction not yet declared is a known reason, so this warns and stores
  the rows.
#}
{{ config(store_failures = true, severity = 'warn') }}

with positions as (
    select
        team_sk,
        league_code,
        season_api_year,
        group_name,
        match_number,
        points_won
    from {{ ref('int_team_season__position_by_match') }}
),

league_table as (
    select
        team_sk,
        team_api_id,
        league_code,
        season_api_year,
        group_name,
        played,
        points
    from {{ ref('fct_standings') }}
),

adjustments as (
    select * from {{ ref('standings_points_adjustments') }}
)

select
    t.league_code,
    t.season_api_year,
    t.group_name,
    t.team_sk,
    t.played,
    t.points as table_points,
    a.points_taken,
    p.points_won
from league_table as t
inner join positions as p
    on
        t.team_sk = p.team_sk
        and t.league_code = p.league_code
        and t.season_api_year = p.season_api_year
        and t.group_name = p.group_name
        and t.played = p.match_number
left join adjustments as a
    on
        t.league_code = a.league_code
        and t.season_api_year = a.season
        and t.team_api_id = a.team_id
        and trim(t.group_name) = trim(a.group_name)
where p.points_won is distinct from t.points + coalesce(a.points_taken, 0)
