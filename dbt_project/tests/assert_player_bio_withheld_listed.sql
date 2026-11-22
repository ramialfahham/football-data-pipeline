{#
  The players whose birth date or nationality is withheld (birth_date_needs_research,
  nationality_needs_research) because their tied records hold two real values: the list to research.
  A player is no match, so he is not on mart_competition_research_list. The fix is a row in
  player_bio_corrections with its sources. Warn severity: the listing is the result, and the value
  is already withheld.
#}
{{ config(store_failures = true, severity = 'warn') }}

select
    player_api_id,
    birth_date_needs_research,
    nationality_needs_research
from {{ ref('base_apif__players') }}
where birth_date_needs_research or nationality_needs_research
