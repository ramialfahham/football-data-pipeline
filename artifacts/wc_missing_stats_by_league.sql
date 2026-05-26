with supporting as (
    select league_code from unnest(['WCQEU','WCQAF','WCQCA','WCQSA','WCQAS','WCQIP','WCQOC']) as league_code
),
wc_teams as (
    select distinct team_sk from (
        select home_team_sk as team_sk from `football-data-pipeline-gcp.core.fct_fixture` where league_code = 'WC'
        union distinct
        select away_team_sk from `football-data-pipeline-gcp.core.fct_fixture` where league_code = 'WC'
    )
),
qualifier_legs as (
    select leg.league_code, leg.shots_on_goal is not null as has_stats
    from `football-data-pipeline-gcp.intermediate.int_matchday__finished_fixture_team_leg` leg
    inner join supporting s on leg.league_code = s.league_code
    inner join wc_teams wt on leg.team_sk = wt.team_sk
)
select
    league_code,
    count(*) as team_legs,
    countif(has_stats) as legs_with_stats,
    countif(not has_stats) as legs_missing_stats,
    round(100 * safe_divide(countif(has_stats), count(*)), 1) as pct_with_stats
from qualifier_legs
group by league_code
order by pct_with_stats desc
