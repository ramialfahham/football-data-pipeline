{#
    int_round_names — every distinct round text of a competition-season named the way the
    competition names it, from base_apif__fixture_rounds, with the competition's latest season
    marked.

    Grain: (league_code, season_api_year, round_name). is_latest_season marks the season the
    competition pages show; assert_every_round_text_resolves fails on a round of that season with
    no name.
#}

select
    league_code,
    season_api_year,
    round_name,
    round_label_i18n_key,
    round_stage_kind,
    round_number,
    round_letter,
    needs_number,
    needs_letter,
    season_api_year = max(season_api_year) over (partition by league_code) as is_latest_season
from {{ ref('base_apif__fixture_rounds') }}
