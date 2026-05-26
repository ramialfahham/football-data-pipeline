{{ config(materialized='table') }}

{#
  Earliest not-started round per (league_code, season_api_year) with fixture count.
  Grain: one row per upcoming fixture on that round.
#}

with import_int_matchday__fixture_denormalized as (
    select * from {{ ref('int_matchday__fixture_denormalized') }}
),

upcoming_candidates as (
    select
        fixture_sk,
        fixture_api_id,
        league_sk,
        season_sk,
        home_team_sk,
        away_team_sk,
        league_code,
        season_api_year,
        fixture_date,
        kickoff_datetime,
        round_name,
        home_team_name,
        away_team_name,
        league_name,
        status_short
    from import_int_matchday__fixture_denormalized
    where
        status_short in ('NS', 'TBD')
        and fixture_date >= current_date()
),

next_round as (
    select
        league_code,
        season_api_year,
        round_name
    from upcoming_candidates
    qualify row_number() over (
        partition by league_code, season_api_year
        order by fixture_date asc, kickoff_datetime asc
    ) = 1
),

upcoming_matchday as (
    select
        uc.*,
        safe_cast(regexp_extract(uc.round_name, r'(\d+)$') as int64) as upcoming_round_order
    from upcoming_candidates as uc
    inner join next_round as nr
        on
            uc.league_code = nr.league_code
            and uc.season_api_year = nr.season_api_year
            and uc.round_name = nr.round_name
),

matchday_fixture_count as (
    select
        league_code,
        season_api_year,
        round_name,
        count(*) as upcoming_matchday_fixture_count
    from upcoming_matchday
    group by league_code, season_api_year, round_name
)

select
    um.*,
    mfc.upcoming_matchday_fixture_count
from upcoming_matchday as um
inner join matchday_fixture_count as mfc
    on
        um.league_code = mfc.league_code
        and um.season_api_year = mfc.season_api_year
        and um.round_name = mfc.round_name
