{#
  A player's stat line and his match events, own goals aside, name the same team. Where they name
  the two different teams of the match and the player's-team rule cannot decide, the player has
  player_team_needs_research: his stat line and his events of the match are left out of the facts
  and are on mart_competition_research_list as player_team_withheld. Where a line is under a team of
  another match, the misfiled-team flag withholds it. A hand-corrected goal or card is no provider
  event and is left out. The conflicts are derived here from the match's two teams in fct_fixture, in
  SQL of their own and not through the macro that sets the flag. Returns a conflict that is not
  withheld, a flagged line without a conflict, a flagged line that a fact holds, and a flagged match
  that is not on the list.
#}
{{ config(severity = 'error', store_failures = true) }}

with participants as (
    select
        fixture_api_id as fixture_id,
        home_team_api_id as home_team_id,
        away_team_api_id as away_team_id
    from {{ ref('fct_fixture') }}
),

conflicts as (
    select distinct
        r.fixture_id,
        r.player_id,
        r.team_id as row_team_id,
        e.team_id as event_team_id,
        e.league_code,
        e.event_index,
        coalesce(
            r.team_id in (p.home_team_id, p.away_team_id) and e.team_id in (p.home_team_id, p.away_team_id),
            false
        ) as between_the_two_teams,
        coalesce(
            p.home_team_id is not null and p.away_team_id is not null
            and r.team_id not in (p.home_team_id, p.away_team_id),
            false
        ) as row_team_is_another_match,
        coalesce(
            p.home_team_id is not null and p.away_team_id is not null
            and e.team_id not in (p.home_team_id, p.away_team_id),
            false
        ) as event_team_is_another_match
    from {{ ref('base_apif__fixture_players') }} as r
    inner join {{ ref('base_apif__fixture_events') }} as e
        on r.fixture_id = e.fixture_id and r.player_id = e.player_id
    left join participants as p
        on r.fixture_id = p.fixture_id
    where
        e.team_id != r.team_id
        and not (e.event_type = 'Goal' and e.event_detail = 'Own Goal')
        and e.goal_correction_source is null
        and e.card_correction_source is null
),

disputes as (
    select distinct
        fixture_id,
        player_id
    from conflicts
    where between_the_two_teams
),

flagged_events as (
    select
        c.league_code,
        c.fixture_id,
        c.event_index,
        e.player_id as raw_player_id,
        c.team_needs_research,
        c.player_team_needs_research
    from {{ ref('base_apif__fixture_events_checked') }} as c
    inner join {{ ref('base_apif__fixture_events') }} as e
        on c.league_code = e.league_code and c.fixture_id = e.fixture_id and c.event_index = e.event_index
),

player_lines as (
    select
        fixture_id,
        team_id,
        player_id,
        player_team_needs_research,
        team_needs_research,
        false as is_from_lineups
    from {{ ref('base_apif__fixture_players_checked') }}
    union all
    select
        fixture_id,
        team_id,
        player_id,
        player_team_needs_research,
        team_needs_research,
        true as is_from_lineups
    from {{ ref('base_apif__fixture_players_from_lineups') }}
),

listed as (
    select fixture_sk
    from {{ ref('mart_competition_research_list') }}
    where check_name = 'player_team_withheld'
)

select
    c.fixture_id,
    c.player_id,
    'dispute between the two teams: event is not flagged' as failure
from conflicts as c
inner join flagged_events as f
    on c.league_code = f.league_code and c.fixture_id = f.fixture_id and c.event_index = f.event_index
where c.between_the_two_teams and not f.player_team_needs_research

union all

select
    c.fixture_id,
    c.player_id,
    'dispute between the two teams: stat line is not flagged' as failure
from conflicts as c
inner join player_lines as l
    on c.fixture_id = l.fixture_id and c.row_team_id = l.team_id and c.player_id = l.player_id
where c.between_the_two_teams and not l.is_from_lineups and not l.player_team_needs_research

union all

select
    c.fixture_id,
    c.player_id,
    'event under a team of another match is not withheld' as failure
from conflicts as c
inner join flagged_events as f
    on c.league_code = f.league_code and c.fixture_id = f.fixture_id and c.event_index = f.event_index
where c.event_team_is_another_match and not f.team_needs_research

union all

select
    c.fixture_id,
    c.player_id,
    'stat line under a team of another match is not withheld' as failure
from conflicts as c
inner join player_lines as l
    on c.fixture_id = l.fixture_id and c.row_team_id = l.team_id and c.player_id = l.player_id
where c.row_team_is_another_match and not l.is_from_lineups and not l.team_needs_research

union all

select
    f.fixture_id,
    f.raw_player_id as player_id,
    'event is flagged without a dispute' as failure
from flagged_events as f
left join disputes as d
    on f.fixture_id = d.fixture_id and f.raw_player_id = d.player_id
where f.player_team_needs_research and d.fixture_id is null

union all

select
    l.fixture_id,
    l.player_id,
    'player line is flagged without a dispute' as failure
from player_lines as l
left join disputes as d
    on l.fixture_id = d.fixture_id and l.player_id = d.player_id
where l.player_team_needs_research and d.fixture_id is null

union all

select
    e.fixture_api_id as fixture_id,
    f.raw_player_id as player_id,
    'flagged event is in the fact' as failure
from {{ ref('fct_fixture_event') }} as e
inner join flagged_events as f
    on e.league_code = f.league_code and e.fixture_api_id = f.fixture_id and e.event_index = f.event_index
where f.player_team_needs_research

union all

select
    s.fixture_api_id as fixture_id,
    s.player_api_id as player_id,
    'flagged player line is in the fact' as failure
from {{ ref('fct_fixture_player_stats') }} as s
inner join player_lines as l
    on
        s.fixture_api_id = l.fixture_id
        and s.team_api_id = l.team_id
        and s.player_api_id = l.player_id
        and s.is_from_lineups = l.is_from_lineups
where l.player_team_needs_research

union all

select
    f.fixture_id,
    f.raw_player_id as player_id,
    'flagged match is not on the list' as failure
from flagged_events as f
left join listed as l
    on cast(f.fixture_id as int64) = l.fixture_sk
where f.player_team_needs_research and l.fixture_sk is null
