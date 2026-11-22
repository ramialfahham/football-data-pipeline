{#
  The national-team competition-seasons that count as this season or last. A national competition has
  no placing in competition_season_map, so an edition is placed by its last match: it counts when
  that match is on or after 1 July of last split-year season, and then every match of it counts,
  whatever its own date. A running edition counts.

  Grain: (season_sk).
#}

with current_seasons as (
    select extract(year from date_sub(current_date(), interval 6 month)) as split_year_season
)

select
    f.season_sk,
    f.league_code,
    f.season_api_year,
    max(date(f.kickoff_datetime)) as last_match_on
from {{ ref('fct_fixture') }} as f
inner join {{ ref('dim_league') }} as leagues
    on f.league_code = leagues.league_code
cross join current_seasons as c
where leagues.entity_type = 'national'
group by f.season_sk, f.league_code, f.season_api_year, c.split_year_season
having max(date(f.kickoff_datetime)) >= date(c.split_year_season - 1, 7, 1)
