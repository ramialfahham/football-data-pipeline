{#
  mart_home_rotation — which league sits in which Home slot, in which season, and whether that
  slot is in season. Home's Top players and Top teams draw one slot per build by weight and read
  the leagues and the season to show from here.

  Two rows per league at most, told apart by board_role:
  - 'current': the league's latest season with a finished match. The league is in season when
    that season has at least home_rotation_min_finished_matches finished matches, so a league
    whose new season has started but has played less is out, never shown with last season's
    leaders. A slot is in season when one of its leagues is.
  - 'fallback': the league's latest season that has finished matches and is no longer the
    provider's current one, for the slot named as the fallback when no slot is in season.

  The slot and its weight come from the home_rotation_slots seed through the competition_group of
  the row's own season, so a league that changes group between seasons moves slot with it. A league
  whose season carries no group in the seed has no row. A finished match is a match of
  int_legs__team_match, the one definition. The in-season flags are NULL on 'fallback' rows.

  Grain: (league_code, board_role). league_code discriminates the competition and is not a
  BigQuery partition or cluster key.
#}

with legs as (
    select
        fixture_sk,
        league_code,
        season_api_year
    from {{ ref('int_legs__team_match') }}
    where home_away = 'home'
),

finished as (
    select
        league_code,
        season_api_year,
        count(*) as finished_matches
    from legs
    group by league_code, season_api_year
),

seasons as (
    select
        finished.league_code,
        finished.season_api_year,
        finished.finished_matches,
        dim.competition_group,
        dim.season_label,
        coalesce(dim.season_is_current, false) as season_is_current
    from finished
    inner join {{ ref('dim_competition_season') }} as dim
        on finished.league_code = dim.league_code and finished.season_api_year = dim.season_api_year
),

chosen as (
    select
        *,
        'current' as board_role
    from seasons
    qualify row_number() over (partition by league_code order by season_api_year desc) = 1

    union all

    select
        *,
        'fallback' as board_role
    from seasons
    where not season_is_current
    qualify row_number() over (partition by league_code order by season_api_year desc) = 1
),

slotted as (
    select
        chosen.league_code,
        chosen.board_role,
        slots.slot,
        chosen.competition_group,
        slots.slot_weight,
        slots.is_fallback_slot,
        chosen.season_api_year,
        chosen.season_label,
        chosen.finished_matches,
        if(
            chosen.board_role = 'current',
            chosen.finished_matches >= {{ var('home_rotation_min_finished_matches') }},
            null
        ) as is_in_season
    from chosen
    inner join {{ ref('home_rotation_slots') }} as slots
        on chosen.competition_group = slots.competition_group
)

select
    league_code,
    board_role,
    slot,
    competition_group,
    slot_weight,
    is_fallback_slot,
    season_api_year,
    season_label,
    finished_matches,
    is_in_season,
    if(
        board_role = 'current',
        max(if(is_in_season, 1, 0)) over (partition by board_role, slot) = 1,
        null
    ) as slot_is_in_season
from slotted
