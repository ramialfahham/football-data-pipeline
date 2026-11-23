{#
  A team-season's values are blank exactly when its results disagree with the provider's standings.
  The disagreement is derived here from the legs and fct_standings (team_seasons_off_standings),
  never from the flag. Returns a row for:
    - a team-season withheld (counts_withheld) with no disagreement;
    - a disagreeing team-season that is not withheld;
    - a withheld team-season of int_team_season__metrics holding a value in any column but its keys,
      entity_type and the flag (the columns are read from the model, so a column added later is held
      to the same rule);
    - a team-season not withheld whose season_games_played is blank;
    - a team-season of mart_team_season or mart_team_season_insights or mart_team_season_record
      whose played, wins, draws, losses, goals, goals against, goal difference, points or clean
      sheets (season_games_played in the insights, games_played in the season record) are not blank
      where it is withheld, or blank where it is not.
    - a match listed on mart_competition_research_list as team_season_off_standings whose team-season
      does not disagree, and a finished match of a disagreeing team-season that is not listed.#}
{{ config(store_failures = true, severity = 'error') }}
-- depends_on: {{ ref('int_team_season__metrics') }}

{% set kept = [
    'team_season_sk', 'team_sk', 'league_sk', 'season_sk', 'league_code', 'season_api_year',
    'entity_type', 'counts_withheld'
] %}
{% set values = [] %}
{% if execute %}
    {% for c in adapter.get_columns_in_relation(ref('int_team_season__metrics')) %}
        {% if c.name | lower not in kept %}
            {% do values.append(c.name | lower) %}
        {% endif %}
    {% endfor %}
    {% if values | length == 0 %}
        {{ exceptions.raise_compiler_error("int_team_season__metrics has no value column: the blank check would compare nothing") }}
    {% endif %}
{% endif %}

with leg_counts as (
    {{ team_season_counts_from_legs(ref('int_legs__team_match')) }}
),

disagreeing as (
    select distinct
        team_sk,
        season_sk
    from (
        {{ team_seasons_off_standings('leg_counts', ref('fct_standings'), ref('standings_points_adjustments')) }}
    )
),

season as (
    select
        m.*,
        d.team_sk is not null as disagrees
    from {{ ref('int_team_season__metrics') }} as m
    left join disagreeing as d
        on m.team_sk = d.team_sk and m.season_sk = d.season_sk
)

select
    'int_team_season__metrics' as model,
    team_sk,
    season_sk,
    'withheld without a disagreement' as failure
from season
where counts_withheld and not disagrees

union all

select
    'int_team_season__metrics' as model,
    team_sk,
    season_sk,
    'disagrees with the standings and is not withheld' as failure
from season
where disagrees and not counts_withheld

union all

select
    'int_team_season__metrics' as model,
    team_sk,
    season_sk,
    'withheld and holds a value' as failure
from season
where
    counts_withheld
    and (
        {% for column in values %}
        {{ column }} is not null{% if not loop.last %} or{% endif %}
        {% endfor %}
    )

union all

select
    'int_team_season__metrics' as model,
    team_sk,
    season_sk,
    'not withheld and holds no games count' as failure
from season
where not counts_withheld and season_games_played is null

union all

select
    'mart_team_season' as model,
    s.team_sk,
    s.season_sk,
    'values do not follow the flag' as failure
from {{ ref('mart_team_season') }} as t
inner join season as s
    on t.team_season_sk = s.team_season_sk
where
    s.counts_withheld
    != (
        t.played is null
        and t.wins is null
        and t.draws is null
        and t.losses is null
        and t.goals_for is null
        and t.goals_against is null
        and t.goal_diff is null
        and t.points is null
        and t.clean_sheets is null
    )
    or (
        not s.counts_withheld
        and (
            t.played is null
            or t.wins is null
            or t.draws is null
            or t.losses is null
            or t.goals_for is null
            or t.goals_against is null
            or t.goal_diff is null
            or t.points is null
            or t.clean_sheets is null
        )
    )

union all

select
    'mart_team_season_insights' as model,
    s.team_sk,
    s.season_sk,
    'values do not follow the flag' as failure
from {{ ref('mart_team_season_insights') }} as i
inner join season as s
    on i.team_season_sk = s.team_season_sk
where (s.counts_withheld and i.season_games_played is not null)
    or (not s.counts_withheld and i.season_games_played is null)

union all

select
    'mart_team_season_record' as model,
    s.team_sk,
    s.season_sk,
    'values do not follow the flag' as failure
from {{ ref('mart_team_season_record') }} as r
inner join season as s
    on
        r.team_sk = s.team_sk
        and r.league_code = s.league_code
        and r.season_api_year = s.season_api_year
where (s.counts_withheld and r.games_played is not null)
    or (not s.counts_withheld and r.games_played is null)

union all

select
    'mart_competition_research_list' as model,
    l.team_sk,
    g.season_sk,
    'listed without a disagreement' as failure
from {{ ref('mart_competition_research_list') }} as l
left join {{ ref('int_legs__team_match') }} as g
    on l.fixture_sk = g.fixture_sk and l.team_sk = g.team_sk
left join disagreeing as d
    on g.team_sk = d.team_sk and g.season_sk = d.season_sk
where l.check_name = 'team_season_off_standings' and d.team_sk is null

union all

select
    'mart_competition_research_list' as model,
    g.team_sk,
    g.season_sk,
    'match of a disagreeing team-season not listed' as failure
from {{ ref('int_legs__team_match') }} as g
inner join disagreeing as d
    on g.team_sk = d.team_sk and g.season_sk = d.season_sk
left join {{ ref('mart_competition_research_list') }} as l
    on
        g.fixture_sk = l.fixture_sk
        and g.team_sk = l.team_sk
        and l.check_name = 'team_season_off_standings'
where l.fixture_sk is null
