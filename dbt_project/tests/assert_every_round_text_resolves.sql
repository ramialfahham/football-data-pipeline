-- Every round of a competition's latest season has a name: a round_names copy key, and the number
-- or group letter that name shows. A round without one shows no name on a page, never the
-- provider's English, so this warns rather than skipping the marts downstream; the stored rows
-- name each round a round_names row is missing for.
{{ config(store_failures = true, severity = 'warn') }}
select
    league_code,
    season_api_year,
    round_name,
    round_label_i18n_key,
    round_number,
    round_letter
from {{ ref('int_round_names') }}
where
    is_latest_season
    and (
        round_label_i18n_key is null
        or (needs_number and round_number is null)
        or (needs_letter and round_letter is null)
    )
