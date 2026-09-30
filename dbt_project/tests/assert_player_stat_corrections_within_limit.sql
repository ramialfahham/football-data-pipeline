{#
  The share of player-match rows the cleaning corrected or left blank because of a contradiction
  or a disagreement between sources (a non-empty stat_corrections), per competition-season, stays
  within one limit for every competition-season, set just above the highest share measured on the
  built cleaning. It catches a provider feed that breaks badly before its numbers reach a page; a
  slow drift is what the comparison with prod before each merge shows.
  Returns each competition-season above the limit.
#}
{{ config(store_failures = true, severity = 'error') }}

{% set limit = 0.08 %}

with player_rows as (
    select
        p.league_code,
        f.season,
        array_length(p.stat_corrections) > 0 as is_corrected
    from {{ ref('base_apif__fixture_players') }} as p
    left join {{ ref('base_apif__fixtures_next') }} as f
        on p.fixture_id = f.fixture_id
)

select
    league_code,
    season,
    countif(is_corrected) as corrected_rows,
    count(*) as player_rows,
    safe_divide(countif(is_corrected), count(*)) as corrected_share
from player_rows
group by league_code, season
having safe_divide(countif(is_corrected), count(*)) > {{ limit }}
