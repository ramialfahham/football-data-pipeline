-- A player whose tied records hold two real values needs a checked correction: a profile can be
-- wrong too, so it settles nothing here.
with corrections as (
    select
        player_api_id,
        corrected_field
    from {{ ref('player_bio_corrections') }}
)

select
    players.player_api_id,
    players.has_conflicting_birth_date,
    players.has_conflicting_nationality
from {{ ref('base_apif__players') }} as players
left join corrections as birth_date_fix
    on
        players.player_api_id = birth_date_fix.player_api_id
        and birth_date_fix.corrected_field = 'player_birth_date'
left join corrections as nationality_fix
    on
        players.player_api_id = nationality_fix.player_api_id
        and nationality_fix.corrected_field = 'player_nationality'
where
    (players.has_conflicting_birth_date and birth_date_fix.player_api_id is null)
    or (players.has_conflicting_nationality and nationality_fix.player_api_id is null)
