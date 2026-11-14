{#
  A season midfield_role is assumed only for a player no counted match gives a role, in any season.
  A match counts when its team sheet is confirmed or researched, or for a starter whose sheet failed
  only the substitutions or squad_lists checks. Returns the assumed player-seasons that have one.
#}

with evidence as (
    select distinct legs.player_sk
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
)

select
    s.player_sk,
    s.season_sk,
    s.midfield_role,
    s.midfield_role_from
from {{ ref('int_player_season__metrics') }} as s
inner join evidence
    on s.player_sk = evidence.player_sk
where s.midfield_role_from = 'assumed'
