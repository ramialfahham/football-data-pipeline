with detail as (
    select stats_coverage_tier
    from (
        with supporting as (
            select league_code from unnest(['WCQEU','WCQAF','WCQCA','WCQSA','WCQAS','WCQIP','WCQOC']) as league_code
        ),
        wc_2026_teams as (
            select distinct team_sk from (
                select home_team_sk as team_sk from `football-data-pipeline-gcp.core.fct_fixture`
                where league_code = 'WC' and season_api_year = 2026
                union distinct
                select away_team_sk from `football-data-pipeline-gcp.core.fct_fixture`
                where league_code = 'WC' and season_api_year = 2026
            )
        ),
        qualifier_legs as (
            select leg.team_sk, leg.shots_on_goal is not null as has_stats
            from `football-data-pipeline-gcp.intermediate.int_matchday__finished_fixture_team_leg` leg
            inner join supporting s on leg.league_code = s.league_code
            inner join wc_2026_teams wt on leg.team_sk = wt.team_sk
        ),
        per_team as (
            select wt.team_sk, count(*) as legs, countif(has_stats) as with_stats
            from wc_2026_teams wt
            left join qualifier_legs ql on wt.team_sk = ql.team_sk
            group by wt.team_sk
        )
        select
            case
                when legs = 0 then 'no_qualifier_legs'
                when with_stats = legs then 'complete'
                when with_stats = 0 then 'no_stats'
                else 'partial'
            end as stats_coverage_tier
        from per_team
    )
)
select stats_coverage_tier, count(*) as team_count
from detail
group by 1
order by 1
