{#
  The Player page position: the most frequent position code of the featured season, then the code of
  the latest match, then the code. A midfielder's position_role is that season's midfield_role.
  Recomputed here; returns the players that disagree.
#}

with page as (
    select
        player_sk,
        featured_season_sk,
        position_group,
        position_role
    from {{ ref('int_player__page_profile') }}
),

code_counts as (
    select
        legs.player_sk,
        legs.position_code,
        count(*) as matches_in_code,
        max(legs.kickoff_datetime) as last_match_in_code
    from {{ ref('int_legs__player_match') }} as legs
    inner join page
        on legs.player_sk = page.player_sk and legs.season_sk = page.featured_season_sk
    where legs.position_code in ('G', 'D', 'M', 'F')
    group by legs.player_sk, legs.position_code
),

expected as (
    select
        c.player_sk,
        array_agg(
            c.position_code order by c.matches_in_code desc, c.last_match_in_code desc, c.position_code asc
            limit 1
        )[offset(0)] as position_code
    from code_counts as c
    group by c.player_sk
)

select
    p.player_sk,
    p.position_group,
    e.position_code,
    p.position_role,
    r.midfield_role
from page as p
left join expected as e
    on p.player_sk = e.player_sk
left join {{ ref('int_player_season__metrics') }} as r
    on p.player_sk = r.player_sk and p.featured_season_sk = r.season_sk
where
    p.position_group is distinct from case e.position_code
        when 'G' then 'GK'
        when 'D' then 'DEF'
        when 'M' then 'MID'
        when 'F' then 'ATT'
    end
    or p.position_role is distinct from if(e.position_code = 'M', r.midfield_role, null)
