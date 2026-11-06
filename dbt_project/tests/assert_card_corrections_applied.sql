{#
  Every match of fixture_card_corrections is applied and sourced, one failing row per broken match:
  its cards in base_apif__fixture_events differ from the seed, or a source is not https URLs
  separated by a space, or match reports stand on fewer than two sites, or a card's player id is on
  neither the team's sheet nor its stat lines of that match, so the card reaches no player.
#}
{{ config(store_failures = true, severity = 'error') }}

with corrections as (
    select * from {{ ref('fixture_card_corrections') }}
),

seed_counts as (
    select
        fixture_id,
        countif(card_order > 0) as seed_cards
    from corrections
    group by fixture_id
),

event_counts as (
    select
        fixture_id,
        countif(card_correction_source is not null) as researched_cards,
        countif(event_type = 'Card' and card_correction_source is null) as provider_cards
    from {{ ref('base_apif__fixture_events') }}
    group by fixture_id
),

not_applied as (
    select
        'not_applied' as failure,
        s.fixture_id
    from seed_counts as s
    left join event_counts as e
        on s.fixture_id = e.fixture_id
    where coalesce(e.researched_cards, 0) != s.seed_cards or coalesce(e.provider_cards, 0) > 0
),

not_sourced as (
    select distinct
        'not_sourced' as failure,
        fixture_id
    from corrections
    where
        not regexp_contains(source, r'^https://\S+( https://\S+)*$')
        or (source_kind = 'match_reports' and array_length(split(source, ' ')) < 2)
),

match_players as (
    select
        fixture_id,
        team_id,
        player_id
    from {{ ref('base_apif__lineups') }}
    union distinct
    select
        fixture_id,
        team_id,
        player_id
    from {{ ref('base_apif__fixture_players') }}
),

off_the_sheet as (
    select distinct
        'off_the_sheet' as failure,
        c.fixture_id
    from corrections as c
    left join match_players as p
        on c.fixture_id = p.fixture_id and c.team_id = p.team_id and c.player_id = p.player_id
    where c.card_order > 0 and p.player_id is null
)

select * from not_applied
union all
select * from not_sourced
union all
select * from off_the_sheet
