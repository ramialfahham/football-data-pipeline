{#
  A player whose card events in one match name two teams has his cards withheld: both card counts
  are blank in base_apif__fixture_players (cards_need_research), and in
  base_apif__fixture_players_from_lineups where he is a sheet player with no stat line, until
  sourced research stands in fixture_card_corrections. The two-team players are derived from the
  card events, never from a flag. Returns one row per such player whose row in either model still
  carries a card count, which means the withholding failed.
#}
{{ config(store_failures = true, severity = 'error') }}

with two_teams as (
    {{ card_events_naming_two_teams(ref('base_apif__fixture_events')) }}
),

researched as (
    select distinct fixture_id
    from {{ ref('fixture_card_corrections') }}
),

player_lines as (
    select
        fixture_id,
        player_id,
        cards_yellow,
        cards_red
    from {{ ref('base_apif__fixture_players') }}
    union all
    select
        fixture_id,
        player_id,
        cards_yellow,
        cards_red
    from {{ ref('base_apif__fixture_players_from_lineups') }}
)

select
    t.fixture_id,
    t.player_id,
    p.cards_yellow,
    p.cards_red
from two_teams as t
inner join player_lines as p
    on t.fixture_id = p.fixture_id and t.player_id = p.player_id
left join researched as r
    on t.fixture_id = r.fixture_id
where
    r.fixture_id is null
    and (p.cards_yellow is not null or p.cards_red is not null)
