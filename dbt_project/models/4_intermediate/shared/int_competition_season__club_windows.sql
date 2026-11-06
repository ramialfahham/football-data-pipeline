{#
  The club competitions a player's season and the season before it are made of. For every club
  competition-season (the anchor): this_season is each club edition belonging to the same season,
  read by the anchor's season_type from competition_season_map through dim_competition_season;
  last_season is the same for the anchor's previous season, leaving out those already in this_season,
  so no match counts on both sides.

  Grain: (anchor_season_sk, window_type, season_sk).
#}

with seasons as (
    select
        d.season_sk,
        d.previous_season_sk,
        d.season_type,
        d.split_year_season,
        d.calendar_year_season
    from {{ ref('dim_competition_season') }} as d
    inner join {{ ref('competition_registry') }} as reg
        on d.league_code = reg.league_code
    inner join {{ ref('competition_types') }} as typ
        on reg.competition_type = typ.competition_type
    where typ.entity_type = 'club' and d.season_type is not null
),

this_season as (
    select
        a.season_sk as anchor_season_sk,
        m.season_sk
    from seasons as a
    inner join seasons as m
        on
            if(a.season_type = 'split_year', a.split_year_season, a.calendar_year_season)
            = if(a.season_type = 'split_year', m.split_year_season, m.calendar_year_season)
),

last_season as (
    select
        a.season_sk as anchor_season_sk,
        m.season_sk
    from seasons as a
    inner join seasons as p
        on a.previous_season_sk = p.season_sk
    inner join seasons as m
        on
            if(p.season_type = 'split_year', p.split_year_season, p.calendar_year_season)
            = if(p.season_type = 'split_year', m.split_year_season, m.calendar_year_season)
    left join this_season as t
        on a.season_sk = t.anchor_season_sk and m.season_sk = t.season_sk
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
