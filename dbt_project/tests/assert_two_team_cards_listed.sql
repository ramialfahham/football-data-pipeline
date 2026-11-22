{#
  A match with a player whose card events name two teams is on mart_competition_research_list as
  cards_withheld, until sourced research stands in fixture_card_corrections. The two-team players
  are derived from the card events, never from a flag. Returns each such match without research
  that is not on the list.
#}
{{ config(store_failures = true, severity = 'error') }}

with two_team_matches as (
    select distinct fixture_id
    from ({{ card_events_naming_two_teams(ref('base_apif__fixture_events')) }})
),

researched as (
    select distinct fixture_id
    from {{ ref('fixture_card_corrections') }}
),

listed as (
    select fixture_sk
    from {{ ref('mart_competition_research_list') }}
    where check_name = 'cards_withheld'
)

select
    t.fixture_id,
    'match of a player whose card events name two teams is not on the list' as failure
from two_team_matches as t
left join researched as r
    on t.fixture_id = r.fixture_id
left join listed as l
    on cast(t.fixture_id as int64) = l.fixture_sk
where r.fixture_id is null and l.fixture_sk is null
