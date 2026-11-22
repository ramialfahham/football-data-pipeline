{#
  A player whose newest delivery of a bio field holds two real values has that field withheld in
  base_apif__players, blank and flagged, until a row in player_bio_corrections settles it: a
  profile can be wrong too, so it settles nothing here. The conflict is read from the staged
  records (players_with_conflicting_bio), never from the flag. Returns a conflict without a
  correction whose value is shown or whose flag is false, and a flag with no conflict or with a
  correction.
#}
{{ config(store_failures = true, severity = 'error') }}

with birth_date_conflicts as (
    {{ players_with_conflicting_bio(possible_birth_date('birth_date', 'raw_ingested_at')) }}
),

nationality_conflicts as (
    {{ players_with_conflicting_bio("nullif(trim(nationality), '')") }}
),

corrections as (
    select
        player_api_id,
        corrected_field
    from {{ ref('player_bio_corrections') }}
),

players as (
    select
        p.player_api_id,
        p.player_birth_date,
        p.player_nationality,
        p.birth_date_needs_research,
        p.nationality_needs_research,
        bc.player_api_id is not null as birth_date_conflicts,
        nc.player_api_id is not null as nationality_conflicts,
        bk.player_api_id is not null as birth_date_corrected,
        nk.player_api_id is not null as nationality_corrected
    from {{ ref('base_apif__players') }} as p
    left join birth_date_conflicts as bc
        on p.player_api_id = bc.player_api_id
    left join nationality_conflicts as nc
        on p.player_api_id = nc.player_api_id
    left join corrections as bk
        on p.player_api_id = bk.player_api_id and bk.corrected_field = 'player_birth_date'
    left join corrections as nk
        on p.player_api_id = nk.player_api_id and nk.corrected_field = 'player_nationality'
)

select
    player_api_id,
    'birth date of a conflict is shown or not flagged' as failure
from players
where
    birth_date_conflicts and not birth_date_corrected
    and (player_birth_date is not null or not birth_date_needs_research)
union all
select
    player_api_id,
    'birth date flagged without a conflict, or despite a correction' as failure
from players
where birth_date_needs_research and not (birth_date_conflicts and not birth_date_corrected)
union all
select
    player_api_id,
    'nationality of a conflict is shown or not flagged' as failure
from players
where
    nationality_conflicts and not nationality_corrected
    and (player_nationality is not null or not nationality_needs_research)
union all
select
    player_api_id,
    'nationality flagged without a conflict, or despite a correction' as failure
from players
where nationality_needs_research and not (nationality_conflicts and not nationality_corrected)
