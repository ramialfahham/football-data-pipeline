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
    select leg.team_sk, leg.fixture_sk, leg.league_code, leg.shots_on_goal is not null as has_stats
    from `football-data-pipeline-gcp.intermediate.int_matchday__finished_fixture_team_leg` leg
    inner join supporting s on leg.league_code = s.league_code
    inner join wc_teams wt on leg.team_sk = wt.team_sk
),
per_team as (
    select team_sk, count(*) as legs, countif(has_stats) as with_stats
    from qualifier_legs
    group by team_sk
),
tiered as (
    select
        team_sk,
        case
            when legs = 0 then 'no_qualifier_legs'
            when with_stats = legs then 'complete'
            when with_stats = 0 then 'no_stats'
            else 'partial'
        end as tier
    from per_team
),
team_primary_confed as (
    select
        ql.team_sk,
        array_agg(ql.league_code order by count(*) desc limit 1)[offset(0)] as primary_qualifier
    from qualifier_legs ql
    group by ql.team_sk
)
select
    t.primary_qualifier,
    tier.tier,
    count(*) as teams
from tiered tier
inner join team_primary_confed t on tier.team_sk = t.team_sk
group by 1, 2
order by 1, 2
