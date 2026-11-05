{#
  The team competition-seasons holding a played match with no player data at all: rule R4's second
  clause in models/docs/metric_rules.md. Awarded results are no match played.
  Grain: (team_sk, season_sk).
#}
{% macro team_seasons_without_player_data() %}
    select distinct
        tm.team_sk,
        tm.season_sk
    from {{ ref('int_legs__team_match') }} as tm
    left join {{ ref('int_legs__team_from_players') }} as tp
        on tm.fixture_sk = tp.fixture_sk and tm.team_sk = tp.team_sk
    where not tm.is_awarded_result and tp.fixture_sk is null
{% endmacro %}
