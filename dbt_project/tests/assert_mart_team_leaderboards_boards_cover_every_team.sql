-- A team board of a competition-season is served only when every team that played has a value for
-- its metric (the ranking_rules doc block). Returns a row (= fails) for each served board whose
-- metric has no value for some team that played, counted from int_team_season__metrics with the
-- zero rule not applied.
{{ config(store_failures = true) }}
{% set keys = dbt_utils.get_column_values(ref('mart_team_leaderboards'), 'metric_key') if execute else [] %}

with served as (
    select distinct
        league_code,
        season_api_year,
        metric_key
    from {{ ref('mart_team_leaderboards') }}
),

coverage as (
    {% for key in keys %}
    select
        league_code,
        season_api_year,
        '{{ key }}' as metric_key,
        count(*) as teams_played,
        countif({{ key }} is not null) as teams_with_value
    from {{ ref('int_team_season__metrics') }}
    where season_games_played >= 1
    group by league_code, season_api_year
    {% if not loop.last %}
    union all
    {% endif %}
    {% else %}
    select
        cast(null as string) as league_code,
        cast(null as int64) as season_api_year,
        cast(null as string) as metric_key,
        0 as teams_played,
        0 as teams_with_value
    where false
    {% endfor %}
)

select
    served.league_code,
    served.season_api_year,
    served.metric_key,
    coverage.teams_played,
    coverage.teams_with_value
from served
left join coverage
    on
        served.league_code = coverage.league_code
        and served.season_api_year = coverage.season_api_year
        and served.metric_key = coverage.metric_key
where coverage.teams_with_value is distinct from coverage.teams_played
