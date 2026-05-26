-- WC national teams: qualifier leg stat coverage for pre-tournament insights mart.

with supporting as (
    select league_code
    from unnest([
        'WCQEU', 'WCQAF', 'WCQCA', 'WCQSA', 'WCQAS', 'WCQIP', 'WCQOC'
    ]) as league_code
),

wc_teams as (
    select distinct team_sk
    from (
        select home_team_sk as team_sk
        from `football-data-pipeline-gcp.core.fct_fixture`
        where league_code = 'WC'
        union distinct
        select away_team_sk as team_sk
        from `football-data-pipeline-gcp.core.fct_fixture`
        where league_code = 'WC'
    )
),

team_names as (
    select
        team_sk,
        any_value(team_name) as team_name,
        any_value(team_country) as team_country
    from `football-data-pipeline-gcp.core.dim_team`
    group by team_sk
),

qualifier_legs as (
    select
        leg.team_sk,
        leg.fixture_sk,
        leg.league_code as qualifier_league_code,
        leg.shots_on_goal is not null as has_shots_on_goal
    from `football-data-pipeline-gcp.intermediate.int_matchday__finished_fixture_team_leg` as leg
    inner join supporting as s on leg.league_code = s.league_code
    inner join wc_teams as wt on leg.team_sk = wt.team_sk
),

per_team as (
    select
        wt.team_sk,
        tn.team_name,
        tn.team_country,
        count(ql.fixture_sk) as qualifier_legs,
        countif(ql.has_shots_on_goal) as legs_with_shots_on_goal,
        string_agg(distinct ql.qualifier_league_code, ', ' order by ql.qualifier_league_code) as qualifier_leagues
    from wc_teams as wt
    left join team_names as tn on wt.team_sk = tn.team_sk
    left join qualifier_legs as ql on wt.team_sk = ql.team_sk
    group by wt.team_sk, tn.team_name, tn.team_country
)

select
    team_sk,
    team_name,
    team_country,
    qualifier_legs,
    legs_with_shots_on_goal,
    qualifier_leagues,
    case
        when qualifier_legs = 0 then 'no_qualifier_legs'
        when legs_with_shots_on_goal = qualifier_legs then 'complete'
        when legs_with_shots_on_goal = 0 then 'no_stats'
        else 'partial'
    end as stats_coverage_tier,
    round(safe_divide(legs_with_shots_on_goal, qualifier_legs), 3) as shots_on_goal_coverage_ratio
from per_team
order by stats_coverage_tier, shots_on_goal_coverage_ratio desc, team_name
