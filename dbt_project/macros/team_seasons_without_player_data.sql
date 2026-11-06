{#
  The team competition-seasons holding a played match with no player row at all: not the provider's
  statistics, not a usable team sheet. Awarded results are no match played.
  Grain: (team_sk, season_sk).
#}
{% macro team_seasons_without_player_data() %}
    select distinct
        tm.team_sk,
        tm.season_sk
    from {{ ref('int_legs__team_match') }} as tm
    left join {{ ref('int_legs__player_match') }} as tp
        on tm.fixture_sk = tp.fixture_sk and tm.team_sk = tp.team_sk
    where not tm.is_awarded_result and tp.fixture_sk is null
{% endmacro %}
