-- Audit WC team counts: fixtures vs standings vs dim_team

with fixture_teams as (
    select distinct team_sk
    from (
        select home_team_sk as team_sk
        from `football-data-pipeline-gcp.core.fct_fixture`
        where league_code = 'WC'
        union distinct
        select away_team_sk
        from `football-data-pipeline-gcp.core.fct_fixture`
        where league_code = 'WC'
    )
),

standings_teams as (
    select distinct team_sk
    from `football-data-pipeline-gcp.core.fct_standings`
    where league_code = 'WC'
),

dim_wc_teams as (
    select distinct team_sk
    from `football-data-pipeline-gcp.core.dim_team`
    where league_code = 'WC'
),

counts as (
    select 'fct_fixture (WC)' as source, count(*) as n from fixture_teams
    union all
    select 'fct_standings (WC)', count(*) from standings_teams
    union all
    select 'dim_team (WC)', count(*) from dim_wc_teams
    union all
    select 'standings ∩ fixtures', count(*)
    from fixture_teams f
    inner join standings_teams s using (team_sk)
    union all
    select 'fixtures not in standings', count(*)
    from fixture_teams f
    left join standings_teams s using (team_sk)
    where s.team_sk is null
    union all
    select 'standings not in fixtures', count(*)
    from standings_teams s
    left join fixture_teams f using (team_sk)
    where f.team_sk is null
)

select * from counts order by source
