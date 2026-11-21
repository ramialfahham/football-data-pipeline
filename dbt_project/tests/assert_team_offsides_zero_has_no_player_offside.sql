-- A team's offsides count is not 0 while a player of it, by the cleaned team id, has an offside
-- above 0. The clause that cleans a blank offsides count to 0 (the cleaning_rules Blank rule) is
-- guarded by the players' offsides under the same team id, so this fails when a team id remap
-- leaves the guard looking at the wrong team. Not counted: a zero that follows the other team's
-- value above 0 (the opponent rule), and fixture 1149592, whose line has the provider's 0 for
-- both teams.
{{ config(store_failures = true) }}

with team_lines as (
    select
        fixture_sk,
        team_sk,
        offsides
    from {{ ref('fct_fixture_team_stats') }}
),

players_with_an_offside as (
    select
        fixture_sk,
        team_sk
    from {{ ref('fct_fixture_player_stats') }}
    where offsides > 0
    group by fixture_sk, team_sk
)

select
    t.fixture_sk,
    t.team_sk
from team_lines as t
inner join players_with_an_offside as p
    on t.fixture_sk = p.fixture_sk and t.team_sk = p.team_sk
inner join team_lines as o
    on t.fixture_sk = o.fixture_sk and t.team_sk != o.team_sk
where
    t.offsides = 0
    and coalesce(o.offsides, 0) = 0
    and t.fixture_sk != 1149592
