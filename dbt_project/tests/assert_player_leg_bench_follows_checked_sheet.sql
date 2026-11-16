{#
  Wherever a confirmed or researched team sheet names a player, his match leg puts him on the bench
  exactly when the sheet does, and counts a start only with minutes on the pitch. Returns each leg
  that disagrees with its sheet.
#}
{{ config(store_failures = true, severity = 'error') }}

select
    legs.fixture_sk,
    legs.player_sk,
    legs.league_code,
    legs.season_api_year,
    legs.minutes,
    legs.is_starter,
    legs.is_substitute,
    sheet.is_starter as sheet_is_starter,
    sheet.lineup_state
from {{ ref('int_legs__player_match') }} as legs
inner join {{ ref('fct_fixture_lineup') }} as sheet
    on legs.fixture_sk = sheet.fixture_sk and legs.player_sk = sheet.player_sk
where
    sheet.lineup_state in ('confirmed', 'researched')
    and (
        legs.is_substitute is distinct from not sheet.is_starter
        or legs.is_starter is distinct from (sheet.is_starter and coalesce(legs.minutes, 0) > 0)
    )
