{#
  An event, a player line, a line-up player line or a match statistics line filed under a team that
  did not play the match is flagged team_needs_research in base, is in no fact and is on
  mart_competition_research_list as misfiled_team_withheld, under the team id the provider filed it
  under. The misfiled lines are derived here from the match's two teams in fct_fixture, in SQL of
  their own and not through the macro that sets the flag, never from the flag. A match with an
  event filed under such a team proves no cards of its line-up players, because the card has no
  team to count for. Returns a misfiled line that is not flagged, a flagged line that is not
  misfiled, a flagged line that a fact holds, a flagged line that is not on the list, and a line-up
  player with cards in a match with a misfiled event.
#}
{{ config(store_failures = true, severity = 'error') }}

with participants as (
    select
        fixture_api_id as fixture_id,
        home_team_api_id as home_team_id,
        away_team_api_id as away_team_id
    from {{ ref('fct_fixture') }}
),

base_lines as (
    select
        'events' as feed,
        fixture_id,
        team_id,
        team_needs_research
    from {{ ref('base_apif__fixture_events_checked') }}
    union all
    select
        'player lines' as feed,
        fixture_id,
        team_id,
        team_needs_research
    from {{ ref('base_apif__fixture_players_checked') }}
    union all
    select
        'line-up players' as feed,
        fixture_id,
        team_id,
        team_needs_research
    from {{ ref('base_apif__fixture_players_from_lineups') }}
    union all
    select
        'statistics' as feed,
        fixture_id,
        team_id,
        team_needs_research
    from {{ ref('base_apif__fixture_statistics') }}
),

classified as (
    select distinct
        b.feed,
        b.fixture_id,
        b.team_id,
        b.team_needs_research,
        coalesce(
            b.team_id is not null
            and p.home_team_id is not null
            and p.away_team_id is not null
            and b.team_id not in (p.home_team_id, p.away_team_id),
            false
        ) as is_misfiled
    from base_lines as b
    left join participants as p
        on b.fixture_id = p.fixture_id
),

listed as (
    select
        fixture_sk,
        provider_team_id
    from {{ ref('mart_competition_research_list') }}
    where check_name = 'misfiled_team_withheld'
)

select
    c.feed,
    c.fixture_id,
    c.team_id,
    'misfiled line is not flagged' as failure
from classified as c
where c.is_misfiled and not c.team_needs_research

union all

select
    c.feed,
    c.fixture_id,
    c.team_id,
    'flagged line is filed under a team of the match, or the match has an unknown team' as failure
from classified as c
where c.team_needs_research and not c.is_misfiled

union all

select
    c.feed,
    c.fixture_id,
    c.team_id,
    'flagged line is not on the list' as failure
from classified as c
left join listed as l
    on cast(c.fixture_id as int64) = l.fixture_sk and cast(c.team_id as int64) = l.provider_team_id
where c.team_needs_research and l.fixture_sk is null

union all

select
    'line-up players' as feed,
    p.fixture_id,
    p.team_id,
    'line-up player has cards in a match with an event filed under a team that did not play it' as failure
from {{ ref('base_apif__fixture_players_from_lineups') }} as p
inner join (
    select distinct fixture_id
    from classified
    where feed = 'events' and is_misfiled
) as m
    on p.fixture_id = m.fixture_id
where p.cards_yellow is not null or p.cards_red is not null

union all

select
    'events' as feed,
    e.fixture_api_id as fixture_id,
    e.team_api_id as team_id,
    'flagged event is in the fact' as failure
from {{ ref('fct_fixture_event') }} as e
inner join {{ ref('base_apif__fixture_events_checked') }} as b
    on
        e.league_code = b.league_code
        and e.fixture_api_id = b.fixture_id
        and e.event_index = b.event_index
where b.team_needs_research

union all

select
    'player lines' as feed,
    s.fixture_api_id as fixture_id,
    s.team_api_id as team_id,
    'flagged player line is in the fact' as failure
from {{ ref('fct_fixture_player_stats') }} as s
inner join {{ ref('base_apif__fixture_players_checked') }} as b
    on
        s.league_code = b.league_code
        and s.fixture_api_id = b.fixture_id
        and s.team_api_id = b.team_id
        and s.player_api_id = b.player_id
where b.team_needs_research and not s.is_from_lineups

union all

select
    'line-up players' as feed,
    s.fixture_api_id as fixture_id,
    s.team_api_id as team_id,
    'flagged line-up player line is in the fact' as failure
from {{ ref('fct_fixture_player_stats') }} as s
inner join {{ ref('base_apif__fixture_players_from_lineups') }} as b
    on
        s.league_code = b.league_code
        and s.fixture_api_id = b.fixture_id
        and s.team_api_id = b.team_id
        and s.player_api_id = b.player_id
where b.team_needs_research and s.is_from_lineups
