{#
  A team's match stat is the newest value any fetch's line carried. Returns one row per team-match
  and stat blank in base_apif__fixture_statistics while a fetch in stg_apif__fixture_statistics
  carries it, unless the cleaning blanked it (a stat_corrections entry) or, for a card count, the
  match's events hold fewer cards that could be of that colour, or more that certainly are, or,
  for offsides, the team has a player with an offside above 0 (the 0 is withheld). The events of a
  match with an event filed under a team that did not play it bound no count; those matches are
  derived here from the match's two teams in base_apif__fixtures_next, not through the macro the
  model calls.
#}
{{ config(store_failures = true, severity = 'error') }}

with carried as (
    select
        league_code,
        fixture_id,
        team_id,
        stat_type
    from {{ ref('stg_apif__fixture_statistics') }}
    where fixture_id is not null and team_id is not null and stat_value_raw is not null
    group by league_code, fixture_id, team_id, stat_type
),

newest_card_counts as (
    select
        fixture_id,
        team_id,
        stat_type,
        array_agg(safe_cast(stat_value_raw as int64) order by raw_ingested_at desc limit 1)[offset(0)] as cards
    from {{ ref('stg_apif__fixture_statistics') }}
    where stat_type in ('Yellow Cards', 'Red Cards') and stat_value_raw is not null
    group by fixture_id, team_id, stat_type
),

matches_with_events as (
    select e.fixture_id
    from {{ ref('base_apif__fixture_events') }} as e
    left join {{ ref('base_apif__fixtures_next') }} as p
        on e.fixture_id = p.fixture_id
    group by e.fixture_id
    having
        logical_or(e.has_full_events)
        and not coalesce(
            logical_or(
                e.team_id is not null
                and p.home_team_id is not null
                and p.away_team_id is not null
                and e.team_id not in (cast(p.home_team_id as int64), cast(p.away_team_id as int64))
            ),
            false
        )
),

card_bounds as (
    select
        e.fixture_id,
        e.team_id,
        countif(e.event_type = 'Card' and e.event_detail = 'Yellow Card') as yellow_certain,
        countif(
            (e.event_type = 'Card' and coalesce(e.event_detail, '') != 'Red Card')
            or (e.event_type = 'Var' and e.event_detail = 'Card reviewed')
        ) as yellow_possible,
        countif(e.event_type = 'Card' and e.event_detail = 'Red Card') as red_certain,
        countif(
            (e.event_type = 'Card' and coalesce(e.event_detail, '') != 'Yellow Card')
            or (
                e.event_type = 'Var'
                and (
                    starts_with(e.event_detail, 'Card upgrade')
                    or e.event_detail in ('Red card cancelled', 'Card reviewed')
                )
            )
        ) as red_possible
    from {{ ref('base_apif__fixture_events') }} as e
    inner join matches_with_events as m
        on e.fixture_id = m.fixture_id
    where e.team_id is not null
    group by e.fixture_id, e.team_id
),

players_with_an_offside as (
    select
        fixture_id,
        team_id
    from {{ ref('base_apif__fixture_players') }}
    where offsides > 0
    group by fixture_id, team_id
),

held as (
    select
        b.league_code,
        b.fixture_id,
        b.team_id,
        stat.stat_type,
        stat.stat_name
    from {{ ref('base_apif__fixture_statistics') }} as b
    cross join
        unnest([
            struct('Shots on Goal' as stat_type, 'shots_on_target' as stat_name, b.shots_on_target as stat_value),
            struct('Shots off Goal', 'shots_off_target', b.shots_off_target),
            struct('Total Shots', 'shots', b.shots),
            struct('Blocked Shots', 'shots_blocked', b.shots_blocked),
            struct('Shots insidebox', 'shots_inside_box', b.shots_inside_box),
            struct('Shots outsidebox', 'shots_outside_box', b.shots_outside_box),
            struct('Fouls', 'fouls', b.fouls),
            struct('Corner Kicks', 'corners', b.corners),
            struct('Offsides', 'offsides', b.offsides),
            struct('Free Kicks', 'free_kicks', b.free_kicks),
            struct('Ball Possession', 'possession_pct', b.possession_pct),
            struct('Yellow Cards', 'cards_yellow', b.cards_yellow),
            struct('Red Cards', 'cards_red', b.cards_red),
            struct('Goalkeeper Saves', 'saves', b.saves),
            struct('Total passes', 'passes', b.passes),
            struct('Passes accurate', 'passes_accurate', b.passes_accurate)
        ]) as stat
    left join players_with_an_offside as po
        on b.fixture_id = po.fixture_id and b.team_id = po.team_id
    where
        stat.stat_value is null
        and stat.stat_name not in (select c.stat from unnest(b.stat_corrections) as c)
        and not (stat.stat_name = 'offsides' and po.fixture_id is not null)
)

select
    held.league_code,
    held.fixture_id,
    held.team_id,
    held.stat_name
from held
inner join carried
    on
        held.league_code = carried.league_code
        and held.fixture_id = carried.fixture_id
        and held.team_id = carried.team_id
        and held.stat_type = carried.stat_type
left join newest_card_counts as cards
    on
        held.fixture_id = cards.fixture_id
        and held.team_id = cards.team_id
        and held.stat_type = cards.stat_type
left join matches_with_events as m
    on held.fixture_id = m.fixture_id
left join card_bounds as bounds
    on held.fixture_id = bounds.fixture_id and held.team_id = bounds.team_id
where not coalesce(
    m.fixture_id is not null
    and case held.stat_type
        when 'Yellow Cards'
            then cards.cards not between coalesce(bounds.yellow_certain, 0) and coalesce(bounds.yellow_possible, 0)
        when 'Red Cards'
            then cards.cards not between coalesce(bounds.red_certain, 0) and coalesce(bounds.red_possible, 0)
        else false
    end,
    false
)
