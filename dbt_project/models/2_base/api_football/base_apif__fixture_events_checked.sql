with events as (
    select * from {{ ref('base_apif__fixture_events') }}
),

participants as (
    select
        fixture_id,
        cast(home_team_id as int64) as home_team_id,
        cast(away_team_id as int64) as away_team_id
    from {{ ref('base_apif__fixtures_next') }}
),

disputed_players as (
    {{ player_team_disputes(ref('base_apif__fixture_players'), 'events', 'participants') }}
),

-- Minutes as elapsed * 100 + added time. A minute at the end of a period with no added minute can
-- be any minute of that period's added time.
sheet as (
    select
        league_code,
        fixture_id,
        player_id,
        if(is_starter, 0, minute_on * 100 + coalesce(minute_on_extra, 0)) as on_from,
        if(
            minute_off is null,
            99999,
            minute_off * 100 + coalesce(minute_off_extra, if(minute_off in (45, 90, 105, 120), 99, 0))
        ) as off_to
    from {{ ref('base_apif__lineups') }}
    where lineup_state in ('confirmed', 'researched')
    qualify row_number() over (
        partition by league_code, fixture_id, player_id
        order by team_id
    ) = 1
),

goals as (
    select
        league_code,
        fixture_id,
        event_index,
        player_id,
        assist_player_id,
        minute_elapsed * 100 + coalesce(minute_extra, 0) as goal_from,
        minute_elapsed * 100 + coalesce(minute_extra, if(minute_elapsed in (45, 90, 105, 120), 99, 0)) as goal_to
    from events
    where is_provider_goal and minute_elapsed is not null
),

checked as (
    select
        goals.league_code,
        goals.fixture_id,
        goals.event_index,
        scorer.player_id is not null
        and (scorer.on_from is null or scorer.on_from > goals.goal_to or scorer.off_to < goals.goal_from)
            as scorer_needs_research,
        assister.player_id is not null
        and (assister.on_from is null or assister.on_from > goals.goal_to or assister.off_to < goals.goal_from)
            as assist_needs_research
    from goals
    left join sheet as scorer
        on
            goals.league_code = scorer.league_code
            and goals.fixture_id = scorer.fixture_id
            and goals.player_id = scorer.player_id
    left join sheet as assister
        on
            goals.league_code = assister.league_code
            and goals.fixture_id = assister.fixture_id
            and goals.assist_player_id = assister.player_id
)

select
    events.league_code,
    events.fixture_id,
    events.event_index,
    events.minute_elapsed,
    events.minute_extra,
    events.event_type,
    events.event_detail,
    events.event_comments,
    events.raw_ingested_at,
    events.resolved_player_team_id,
    events.team_id,
    events.team_name,
    events.goal_correction_source,
    events.card_correction_source,
    events.is_shootout_kick,
    events.is_own_goal,
    events.is_provider_goal,
    events.is_goal,
    events.is_missed_penalty,
    events.has_full_events,
    if(coalesce(checked.scorer_needs_research, false), null, events.player_id) as player_id,
    if(coalesce(checked.scorer_needs_research, false), null, events.player_name) as player_name,
    if(coalesce(checked.assist_needs_research, false), null, events.assist_player_id) as assist_player_id,
    if(coalesce(checked.assist_needs_research, false), null, events.assist_player_name) as assist_player_name,
    coalesce(checked.scorer_needs_research, false) as scorer_needs_research,
    coalesce(checked.assist_needs_research, false) as assist_needs_research,
    {{ team_not_in_fixture('events.team_id', 'participants.home_team_id', 'participants.away_team_id') }}
        as team_needs_research,
    disputed_players.fixture_id is not null as player_team_needs_research
from events
left join checked
    on
        events.league_code = checked.league_code
        and events.fixture_id = checked.fixture_id
        and events.event_index = checked.event_index
left join participants
    on events.fixture_id = participants.fixture_id
left join disputed_players
    on events.fixture_id = disputed_players.fixture_id and events.player_id = disputed_players.player_id
