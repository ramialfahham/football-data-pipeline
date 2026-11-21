{#
    One row per team per fixture, whatever the match's status: the match from each side, with the
    team's own stat values, the opponent's same values (`*_against`), the scoreline from the team's
    side, the result and the match's status columns. Grain: (fixture_sk, team_sk). A fixture whose
    two teams are not both known has no rows.

    The scoreline is the header's: goals_for is the team's goals_home or goals_away, so the two
    rows of a match mirror each other. A forfeit keeps its scoreline and its blank stat columns;
    what a forfeit counts in is rule R3 in models/docs/metric_rules.md, applied by the readers
    through is_awarded_result.
#}

{% set stat_columns = [
    'shots_on_target', 'shots_off_target', 'shots', 'shots_blocked', 'shots_inside_box',
    'shots_outside_box', 'fouls', 'corners', 'offsides', 'free_kicks', 'possession_pct',
    'cards_yellow', 'cards_red', 'saves', 'passes', 'passes_accurate', 'goals_penalty', 'goals_own'
] %}

with fixtures as (
    select * from {{ ref('fct_fixture') }}
    where home_team_sk is not null and away_team_sk is not null
),

sides as (
    select
        fixture_sk,
        fixture_api_id,
        league_code,
        is_finished,
        is_played,
        is_awarded_result,
        'home' as home_away,
        home_team_sk as team_sk,
        home_team_api_id as team_api_id,
        away_team_sk as opponent_team_sk,
        away_team_api_id as opponent_team_api_id,
        goals_home as goals_for,
        goals_away as goals_against,
        awarded_to_team_sk,
        winner_team_sk,
        is_table_shootout
    from fixtures
    union all
    select
        fixture_sk,
        fixture_api_id,
        league_code,
        is_finished,
        is_played,
        is_awarded_result,
        'away' as home_away,
        away_team_sk as team_sk,
        away_team_api_id as team_api_id,
        home_team_sk as opponent_team_sk,
        home_team_api_id as opponent_team_api_id,
        goals_away as goals_for,
        goals_home as goals_against,
        awarded_to_team_sk,
        winner_team_sk,
        is_table_shootout
    from fixtures
),

stats as (
    select * from {{ ref('base_apif__fixture_statistics') }}
)

select
    {{ dbt_utils.generate_surrogate_key(['s.fixture_api_id', 's.league_code', 's.team_api_id']) }}
        as fixture_team_stat_sk,
    s.fixture_sk,
    s.team_sk,
    s.opponent_team_sk,
    s.league_code,
    s.fixture_api_id,
    s.team_api_id,
    s.home_away,
    s.is_finished,
    s.is_played,
    s.is_awarded_result,
    s.goals_for,
    s.goals_against,
    case
        when s.goals_for is null or s.goals_against is null then null
        when s.awarded_to_team_sk is not null then if(s.awarded_to_team_sk = s.team_sk, 'W', 'L')
        when s.goals_for > s.goals_against then 'W'
        when s.goals_for < s.goals_against then 'L'
        else 'D'
    end as result,
    coalesce(s.is_table_shootout and s.winner_team_sk = s.team_sk, false) as is_table_shootout_win,
    coalesce(own.has_stat_line, false) as has_stat_line,
    {%- for column in stat_columns %}
    own.{{ column }},
    {%- endfor %}
    {%- for column in stat_columns %}
    opp.{{ column }} as {{ column }}_against,
    {%- endfor %}
    own.raw_ingested_at
from sides as s
left join stats as own
    on s.fixture_api_id = own.fixture_id and s.team_api_id = own.team_id
left join stats as opp
    on s.fixture_api_id = opp.fixture_id and s.opponent_team_api_id = opp.team_id
