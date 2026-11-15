{#
  The share of player-match rows the cleaning corrected or left blank (a non-empty
  stat_corrections) per competition-season, over the matches whose player stats are final
  (base_apif__fixture_fetches). Past one limit, set just above the highest share measured on the
  built cleaning, the provider's feed broke badly, and stats_need_research withholds the
  competition-season's player and team boards.
  Grain: (league_code, season_api_year).
#}

{% set limit = 0.08 %}

with player_rows as (
    select
        p.league_code,
        f.season as season_api_year,
        array_length(p.stat_corrections) > 0 as is_corrected
    from {{ ref('base_apif__fixture_players') }} as p
    left join {{ ref('base_apif__fixtures_next') }} as f
        on p.fixture_id = f.fixture_id
    left join {{ ref('base_apif__fixture_fetches') }} as w
        on p.fixture_id = w.fixture_id
    where not coalesce(w.is_awaiting_second_fetch, false)
),

shares as (
    select
        league_code,
        season_api_year,
        countif(is_corrected) as corrected_rows,
        count(*) as player_rows,
        safe_divide(countif(is_corrected), count(*)) as corrected_share
    from player_rows
    group by league_code, season_api_year
)

select
    s.league_code,
    s.season_api_year,
    c.season_sk,
    s.corrected_rows,
    s.player_rows,
    s.corrected_share,
    coalesce(s.corrected_share > {{ limit }}, false) as stats_need_research
from shares as s
left join {{ ref('dim_competition_season') }} as c
    on s.league_code = c.league_code and s.season_api_year = c.season_api_year
