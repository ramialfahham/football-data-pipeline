-- Unified per-team fixture statistics across all onboarded competitions.
-- League list driven by var('active_competition_league_codes') — no league codes
-- appear in this file. To add a competition: update docs/competition_registry.yml
-- and run scripts/sync_dbt_vars.py. This is the standard pattern for any base model
-- that unions across leagues.
-- Output grain: (league_code, fixture_id, team_id).
{% set league_codes = var('active_competition_league_codes') %}

with src as (

{% for lc in league_codes %}
    {% if not loop.first %}

    union all

    {% endif %}
    select
        league_code,
        fixture_id,
        team_id,
        shots_on_goal,
        shots_off_goal,
        shots_total,
        shots_blocked,
        shots_inside_box,
        shots_outside_box,
        fouls,
        corner_kicks,
        offsides,
        ball_possession_percent,
        yellow_cards,
        red_cards,
        goalkeeper_saves,
        passes_total,
        passes_accurate,
        passes_accuracy_percent,
        raw_ingested_at
    from {{ ref('stg_apif__' ~ lc | lower ~ '_fixture_statistics') }}
    where
        fixture_id is not null
        and team_id is not null

{% endfor %}

),

deduped_fixture_statistics as (
    select *
    from src
    qualify row_number() over (
        partition by league_code, fixture_id, team_id
        order by raw_ingested_at desc
    ) = 1
)

select
    league_code,
    fixture_id,
    team_id,
    shots_on_goal,
    shots_off_goal,
    shots_total,
    shots_blocked,
    shots_inside_box,
    shots_outside_box,
    fouls,
    corner_kicks,
    offsides,
    ball_possession_percent,
    yellow_cards,
    red_cards,
    goalkeeper_saves,
    passes_total,
    passes_accurate,
    passes_accuracy_percent,
    raw_ingested_at
from deduped_fixture_statistics
