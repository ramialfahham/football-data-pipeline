-- A team's offsides count is not 0 while a player of it, by the cleaned team id, has an offside
-- above 0 (the cleaning_rules Blank rule). It holds whether the 0 came from the provider, from the
-- other team's line or from the team's own full line, and fails when a team id remap leaves the
-- guard looking at the wrong team.
{{ config(store_failures = true) }}

with players_with_an_offside as (
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
from {{ ref('fct_fixture_team_stats') }} as t
inner join players_with_an_offside as p
    on t.fixture_sk = p.fixture_sk and t.team_sk = p.team_sk
where t.offsides = 0
