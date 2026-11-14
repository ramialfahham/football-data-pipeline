{#
  A player's season midfield_role is his most frequent role over that competition-season's matches
  whose sheet counts, then the role of his latest match, then the code. Without one, it is his most
  frequent role over his matches in every other season, a tie going to the nearest season, then the
  earlier. Without either, a player who played as a midfielder that season is CM, assumed.
  midfield_role_from names which. Recomputed here from the line-ups and the player's matches;
  returns the player-seasons that disagree.
#}

with counted as (
    select
        legs.player_sk,
        legs.season_sk,
        legs.season_api_year,
        legs.kickoff_datetime,
        lineups.midfield_role
    from {{ ref('int_legs__player_match') }} as legs
    inner join {{ ref('fct_fixture_lineup') }} as lineups
        on
            legs.fixture_sk = lineups.fixture_sk
            and legs.team_sk = lineups.team_sk
            and legs.player_sk = lineups.player_sk
    where
        lineups.midfield_role is not null
        and (
            lineups.lineup_state in ('confirmed', 'researched')
            or (
                lineups.is_starter
                and array_length(lineups.failed_checks) > 0
                and array_length(array(
                    select c from unnest(lineups.failed_checks) as c
                    where c in ('substitutions', 'squad_lists')
                )) = array_length(lineups.failed_checks)
            )
        )
),

own_counts as (
    select
        player_sk,
        season_sk,
        midfield_role,
        count(*) as matches_in_role,
        max(kickoff_datetime) as last_match_in_role
    from counted
    group by player_sk, season_sk, midfield_role
),

own as (
    select
        player_sk,
        season_sk,
        array_agg(
            midfield_role order by matches_in_role desc, last_match_in_role desc, midfield_role asc limit 1
        )[offset(0)] as role
    from own_counts
    group by player_sk, season_sk
),

seasons as (
    select distinct
        player_sk,
        season_sk,
        season_api_year
    from {{ ref('int_legs__player_match') }}
),

other_counts as (
    select
        s.player_sk,
        s.season_sk,
        c.midfield_role,
        count(*) as matches_in_role,
        min(abs(c.season_api_year - s.season_api_year)) as nearest
    from seasons as s
    inner join counted as c
        on s.player_sk = c.player_sk and s.season_sk != c.season_sk
    group by s.player_sk, s.season_sk, c.midfield_role
),

nearest_earlier as (
    select
        s.player_sk,
        s.season_sk,
        c.midfield_role,
        min(c.season_api_year - s.season_api_year) as signed_nearest
    from seasons as s
    inner join counted as c
        on s.player_sk = c.player_sk and s.season_sk != c.season_sk
    inner join other_counts as oc
        on
            s.player_sk = oc.player_sk
            and s.season_sk = oc.season_sk
            and c.midfield_role = oc.midfield_role
            and abs(c.season_api_year - s.season_api_year) = oc.nearest
    group by s.player_sk, s.season_sk, c.midfield_role
),

other as (
    select
        oc.player_sk,
        oc.season_sk,
        array_agg(
            oc.midfield_role
            order by oc.matches_in_role desc, oc.nearest asc, ne.signed_nearest < 0 desc, oc.midfield_role asc
            limit 1
        )[offset(0)] as role
    from other_counts as oc
    inner join nearest_earlier as ne
        on
            oc.player_sk = ne.player_sk
            and oc.season_sk = ne.season_sk
            and oc.midfield_role = ne.midfield_role
    group by oc.player_sk, oc.season_sk
),

played_midfield as (
    select distinct
        player_sk,
        season_sk
    from {{ ref('int_legs__player_match') }}
    where position_code = 'M' and minutes > 0
)

select
    s.player_sk,
    s.season_sk,
    s.midfield_role,
    s.midfield_role_from,
    own.role as own_role,
    other.role as other_role
from {{ ref('int_player_season__metrics') }} as s
left join own
    on s.player_sk = own.player_sk and s.season_sk = own.season_sk
left join other
    on s.player_sk = other.player_sk and s.season_sk = other.season_sk
left join played_midfield as pm
    on s.player_sk = pm.player_sk and s.season_sk = pm.season_sk
where
    s.midfield_role is distinct from coalesce(own.role, other.role, if(pm.player_sk is not null, 'CM', null))
    or s.midfield_role_from is distinct from case
        when own.role is not null then 'this_season'
        when other.role is not null then 'other_seasons'
        when pm.player_sk is not null then 'assumed'
    end
