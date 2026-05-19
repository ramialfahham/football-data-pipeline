-- Play-off fixtures configured in dbt vars must not appear in the unified domestic mart.
select
    f.fixture_sk,
    f.league_code,
    f.round_name
from {{ ref('int_matchday__upcoming_round_fixtures') }} as f
where
    (
        f.league_code = 'BL1'
        and f.round_name in {{ bl1_relegation_round_names_in_clause() }}
    )
    or (
        f.league_code = 'BL2'
        and f.round_name in {{ bl2_playoff_round_names_in_clause() }}
    )
    or (
        f.league_code = 'L1'
        and f.round_name in {{ l1_relegation_round_names_in_clause() }}
    )
intersect distinct
select
    m.fixture_sk,
    m.league_code,
    m.round_name
from {{ ref('mart_matchday_insights') }} as m
