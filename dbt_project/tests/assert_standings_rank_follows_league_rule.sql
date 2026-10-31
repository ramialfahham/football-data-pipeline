{#
  The served league table follows the league's own tie-break rule wherever the rule decides. A
  section is compared when every team's matches played and points equal the league table rebuilt
  at the section's latest kick-off (int_team_season__table_by_time). There, a team the rules place
  must be served at that place, and the section's served places must run 1 to n without a gap or
  a repeat. A section that is not compared keeps the provider's rank.

  Returns one row per failing team or section.
#}
{{ config(store_failures = true, severity = 'error') }}

with served as (
    select
        league_code,
        season_api_year,
        group_name,
        team_sk,
        played,
        points,
        standing_rank
    from {{ ref('mart_standings') }}
),

rebuilt as (
    select
        league_code,
        season_api_year,
        group_name,
        team_sk,
        played,
        table_points,
        table_position
    from {{ ref('int_team_season__table_by_time') }}
    qualify table_at = max(table_at) over (partition by league_code, season_api_year, group_name)
),

compared as (
    select
        s.league_code,
        s.season_api_year,
        s.group_name,
        s.team_sk,
        s.standing_rank,
        r.table_position,
        logical_and(coalesce(r.played = s.played and r.table_points = s.points, false)) over (
            partition by s.league_code, s.season_api_year, s.group_name
        ) as is_section_compared
    from served as s
    left join rebuilt as r
        on
            s.league_code = r.league_code
            and s.season_api_year = r.season_api_year
            and s.group_name = r.group_name
            and s.team_sk = r.team_sk
),

off_rule as (
    select
        league_code,
        season_api_year,
        group_name,
        team_sk,
        standing_rank,
        table_position,
        'served place differs from the rule' as failure
    from compared
    where
        is_section_compared
        and table_position is not null
        and standing_rank != table_position
),

section_runs as (
    select
        league_code,
        season_api_year,
        group_name,
        count(*) as teams,
        count(distinct standing_rank) as distinct_places,
        min(standing_rank) as first_place,
        max(standing_rank) as last_place
    from compared
    where is_section_compared
    group by league_code, season_api_year, group_name
),

broken_runs as (
    select
        league_code,
        season_api_year,
        group_name,
        cast(null as int64) as team_sk,
        cast(null as int64) as standing_rank,
        cast(null as int64) as table_position,
        'served places do not run 1 to n' as failure
    from section_runs
    where not (first_place = 1 and last_place = teams and distinct_places = teams)
)

select * from off_rule
union all
select * from broken_runs
