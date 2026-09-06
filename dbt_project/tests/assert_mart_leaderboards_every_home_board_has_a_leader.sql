-- Every Home board must have a rank-1 player in every elite league's current season.
--
-- ⛔ THE PAGE DELIBERATELY WILL NOT TELL US. #40 rules that a board with no data is not rendered —
-- no placeholder, no empty state — because *"if a board is missing, the user may not even notice,
-- so don't show."* That is right for the reader and blind for us: a board that silently stops
-- being produced looks identical to a board that was never meant to appear. #40 names the
-- consequence and asks for this test by name:
--   "A silently omitted board is invisible to the visitor by design — and therefore invisible to
--    us too. A DQ check has to catch a board that vanished, because the page deliberately will
--    not."
--
-- Mirrors assert_mart_team_leaderboards_every_board_has_a_leader, which exists because dropping
-- metric_key from that mart's rank partition was caught by NOTHING — the grain stayed unique, the
-- board set stayed complete, and only a missing rank-1 exposed it.
--
-- Scoped to the ELITE group and the current season because that is what the block renders. A board
-- with no data in a league the block never shows is not a defect; asserting it would fail on
-- competitions that legitimately carry no player stats.

{% set home_boards = [
    'goals_player',
    'assists_player',
    'passes_player',
    'passes_key_player',
] %}

with import_mart_leaderboards as (
    select * from {{ ref('mart_leaderboards') }}
),

import_competition_registry as (
    select * from {{ ref('competition_registry') }}
),

elite_leagues as (
    select league_code
    from import_competition_registry
    where competition_group = 'elite'
),

expected as (
    select
        e.league_code,
        metric_key
    from elite_leagues as e
    cross join unnest([
        {% for key in home_boards %}
        '{{ key }}'{% if not loop.last %},{% endif %}
        {% endfor %}
    ]) as metric_key
),

actual as (
    select distinct
        league_code,
        metric_key
    from import_mart_leaderboards
    where
        is_current_season
        and rank = 1
        and metric_key in (
            {% for key in home_boards %}
            '{{ key }}'{% if not loop.last %},{% endif %}
            {% endfor %}
        )
)

select
    expected.league_code,
    expected.metric_key
from expected
left join actual
    on
        expected.league_code = actual.league_code
        and expected.metric_key = actual.metric_key
where actual.league_code is null
