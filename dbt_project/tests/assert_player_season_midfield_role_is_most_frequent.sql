{#
  A player's season midfield_role is his most frequent role over his matches on a checked team sheet
  that competition-season, then the role of his latest match, then the code; NULL with no role at
  all. Recomputed here from the line-ups and the player's matches. Returns the player-seasons that disagree.
#}

with role_counts as (
    select
        legs.player_sk,
        legs.season_sk,
        lineups.midfield_role,
        count(*) as starts_in_role,
        max(legs.kickoff_datetime) as last_start_in_role
    from {{ ref('int_legs__player_match') }} as legs
    inner join {{ ref('fct_fixture_lineup') }} as lineups
        on
            legs.fixture_sk = lineups.fixture_sk
            and legs.team_sk = lineups.team_sk
            and legs.player_sk = lineups.player_sk
    where lineups.midfield_role is not null and lineups.lineup_state in ('confirmed', 'researched')
    group by legs.player_sk, legs.season_sk, lineups.midfield_role
),

expected as (
    select
        player_sk,
        season_sk,
        array_agg(
            midfield_role order by starts_in_role desc, last_start_in_role desc, midfield_role asc limit 1
        )[offset(0)] as expected_role
    from role_counts
    group by player_sk, season_sk
)

select
    s.player_sk,
    s.season_sk,
    s.midfield_role,
    e.expected_role
from {{ ref('int_player_season__metrics') }} as s
left join expected as e
    on s.player_sk = e.player_sk and s.season_sk = e.season_sk
where s.midfield_role is distinct from e.expected_role
