{#
  The team-per-fixture fact is the header seen from each side. One row per failing fixture and
  check: a fixture with both teams known that does not have exactly two rows (one home, one away),
  a row whose goals_for or goals_against is not the header's, a row whose opponent's row does not
  hold the mirrored goals, a status column that differs from fct_fixture's, or an opponent stat
  value that is not the opponent's own.
#}
{{ config(store_failures = true, severity = 'error') }}

{% set stat_columns = [
    'shots_on_target', 'shots_off_target', 'shots', 'shots_blocked', 'shots_inside_box',
    'shots_outside_box', 'fouls', 'corners', 'offsides', 'free_kicks', 'possession_pct',
    'cards_yellow', 'cards_red', 'saves', 'passes', 'passes_accurate', 'goals_penalty', 'goals_own'
] %}

with fixtures as (
    select * from {{ ref('fct_fixture') }}
    where home_team_sk is not null and away_team_sk is not null
),

team_rows as (
    select * from {{ ref('fct_fixture_team_stats') }}
),

row_counts as (
    select
        fixtures.fixture_sk,
        countif(team_rows.home_away = 'home') as home_rows,
        countif(team_rows.home_away = 'away') as away_rows
    from fixtures
    left join team_rows
        on fixtures.fixture_sk = team_rows.fixture_sk
    group by fixtures.fixture_sk
)

select
    fixture_sk,
    'not one home row and one away row' as failed_check
from row_counts
where home_rows != 1 or away_rows != 1

union all

select
    team_rows.fixture_sk,
    'a team row is not on a fixture with both teams' as failed_check
from team_rows
left join fixtures
    on team_rows.fixture_sk = fixtures.fixture_sk
where fixtures.fixture_sk is null

union all

select
    team_rows.fixture_sk,
    'goals_for or goals_against differs from the header' as failed_check
from team_rows
inner join fixtures
    on team_rows.fixture_sk = fixtures.fixture_sk
where
    (team_rows.home_away = 'home' and (
        team_rows.team_sk != fixtures.home_team_sk
        or team_rows.opponent_team_sk != fixtures.away_team_sk
        or team_rows.goals_for is distinct from fixtures.goals_home
        or team_rows.goals_against is distinct from fixtures.goals_away
    ))
    or (team_rows.home_away = 'away' and (
        team_rows.team_sk != fixtures.away_team_sk
        or team_rows.opponent_team_sk != fixtures.home_team_sk
        or team_rows.goals_for is distinct from fixtures.goals_away
        or team_rows.goals_against is distinct from fixtures.goals_home
    ))

union all

select
    team_rows.fixture_sk,
    'a status column differs from fct_fixture' as failed_check
from team_rows
inner join fixtures
    on team_rows.fixture_sk = fixtures.fixture_sk
where
    team_rows.is_finished != fixtures.is_finished
    or team_rows.is_played != fixtures.is_played
    or team_rows.is_awarded_result != fixtures.is_awarded_result

union all

select
    own.fixture_sk,
    'the opponent row is missing or does not mirror this row' as failed_check
from team_rows as own
left join team_rows as opp
    on own.fixture_sk = opp.fixture_sk and own.opponent_team_sk = opp.team_sk
where
    opp.fixture_sk is null
    or own.goals_for is distinct from opp.goals_against
    or own.goals_against is distinct from opp.goals_for
    {%- for column in stat_columns %}
    or own.{{ column }}_against is distinct from opp.{{ column }}
    {%- endfor %}
