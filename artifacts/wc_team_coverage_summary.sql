-- Summary counts by coverage tier (companion to wc_team_qualifier_stats_coverage.sql)

with detail as (
    select * from (
        -- inline: run same logic as main query via EXECUTE IMMEDIATE not available; duplicate CTEs minimal
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
            select leg.team_sk, leg.fixture_sk, leg.shots_on_goal is not null as has_shots_on_goal
            from `football-data-pipeline-gcp.intermediate.int_matchday__finished_fixture_team_leg` leg
            inner join supporting s on leg.league_code = s.league_code
            inner join wc_teams wt on leg.team_sk = wt.team_sk
        ),
        per_team as (
            select wt.team_sk, count(ql.fixture_sk) as qualifier_legs, countif(ql.has_shots_on_goal) as legs_with_shots_on_goal
            from wc_teams wt
            left join qualifier_legs ql on wt.team_sk = ql.team_sk
            group by wt.team_sk
        )
        select
            case
                when qualifier_legs = 0 then 'no_qualifier_legs'
                when legs_with_shots_on_goal = qualifier_legs then 'complete'
                when legs_with_shots_on_goal = 0 then 'no_stats'
                else 'partial'
            end as stats_coverage_tier
        from per_team
    )
)
select stats_coverage_tier, count(*) as team_count
from detail
group by stats_coverage_tier
order by stats_coverage_tier
