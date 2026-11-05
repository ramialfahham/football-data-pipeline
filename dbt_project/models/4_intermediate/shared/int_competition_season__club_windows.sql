{#
  The club competitions a player's season and the season before it are made of. For every club
  competition-season (the anchor): this_season is each club competition-season whose dates overlap
  it; last_season is each one overlapping the anchor's previous season, leaving out those already in
  this_season, so no match counts on both sides.

  A competition's dates run from its first fixture to its last. Grain: (anchor_season_sk,
  window_type, season_sk).
#}

with seasons as (
    select
        f.season_sk,
        f.league_code,
        f.season_api_year,
        min(f.kickoff_datetime) as first_match_at,
        max(f.kickoff_datetime) as last_match_at
    from {{ ref('fct_fixture') }} as f
    inner join {{ ref('competition_registry') }} as reg
        on f.league_code = reg.league_code
    inner join {{ ref('competition_types') }} as typ
        on reg.competition_type = typ.competition_type
    where typ.entity_type = 'club'
    group by f.season_sk, f.league_code, f.season_api_year
),

anchors as (
    select
        season_sk as anchor_season_sk,
        first_match_at,
        last_match_at,
        lag(season_sk) over (partition by league_code order by season_api_year) as previous_season_sk
    from seasons
),

this_season as (
    select
        a.anchor_season_sk,
        m.season_sk
    from anchors as a
    inner join seasons as m
        on a.last_match_at >= m.first_match_at and a.first_match_at <= m.last_match_at
),

last_season as (
    select distinct
        a.anchor_season_sk,
        m.season_sk
    from anchors as a
    inner join seasons as previous
        on a.previous_season_sk = previous.season_sk
    inner join seasons as m
        on previous.last_match_at >= m.first_match_at and previous.first_match_at <= m.last_match_at
    left join this_season as t
        on a.anchor_season_sk = t.anchor_season_sk and m.season_sk = t.season_sk
    where t.season_sk is null
)

select
    anchor_season_sk,
    'this_season' as window_type,
    season_sk
from this_season
union all
select
    anchor_season_sk,
    'last_season' as window_type,
    season_sk
from last_season
