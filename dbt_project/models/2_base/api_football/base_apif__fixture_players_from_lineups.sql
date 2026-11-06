{#
  One row per player on a confirmed or researched team sheet of a played team match with no player
  statistics, in the columns of base_apif__fixture_players. The sheet gives who played and the
  substitutions their minutes; the goal events give the goals and assists. Everything else stays
  blank. The cleaning_rules doc block in models/docs/cleaning_rules.md applies as written.

  This is its own model because base_apif__lineups reads base_apif__fixture_players.

  Grain: (league_code, fixture_id, team_id, player_id).
#}

with team_matches_with_stats as (
    select distinct
        fixture_id,
        team_id
    from {{ ref('base_apif__fixture_players') }}
),

fixtures as (
    select
        fixture_id,
        status_short,
        goals_home,
        goals_away,
        cast(home_team_id as int64) as home_team_id
    from {{ ref('base_apif__fixtures_next') }}
    where
        status_short in ('FT', 'AET', 'PEN')
        and goals_home is not null
        and goals_away is not null
),

sheets as (
    select
        l.league_code,
        l.fixture_id,
        l.team_id,
        l.player_id,
        l.is_starter,
        l.shirt_number,
        l.position_code,
        l.minute_on,
        l.minute_off,
        l.raw_ingested_at,
        f.status_short,
        if(l.team_id = f.home_team_id, f.goals_home, f.goals_away) as team_goals_for,
        if(l.team_id = f.home_team_id, f.goals_away, f.goals_home) as team_goals_conceded
    from {{ ref('base_apif__lineups') }} as l
    inner join fixtures as f
        on l.fixture_id = f.fixture_id
    left join team_matches_with_stats as s
        on l.fixture_id = s.fixture_id and l.team_id = s.team_id
    where
        l.lineup_state in ('confirmed', 'researched')
        and s.fixture_id is null
),

events as (
    select
        fixture_id,
        team_id,
        player_id,
        minute_elapsed,
        event_type,
        event_detail,
        assist_player_id,
        assist_player_name,
        is_goal,
        is_own_goal,
        is_shootout_kick
    from {{ ref('base_apif__fixture_events') }}
),

match_events as (
    select
        fixture_id,
        countif(is_goal and assist_player_name is not null) as assisted_goal_events,
        coalesce(logical_or(minute_elapsed > 90 and not is_shootout_kick), false) as has_extra_time_event
    from events
    group by fixture_id
),

team_events as (
    select
        fixture_id,
        team_id,
        countif(is_goal and not is_own_goal) as goal_events,
        countif(is_goal and not is_own_goal and player_id is null) as goal_events_without_scorer,
        countif(is_goal and is_own_goal) as own_goals,
        countif(is_goal and event_detail = 'Normal Goal') as open_play_goal_events,
        countif(is_goal and not is_own_goal and assist_player_name is not null) as assisted_goal_events
    from events
    group by fixture_id, team_id
),

player_goals as (
    select
        fixture_id,
        team_id,
        player_id,
        countif(is_goal and not is_own_goal) as goals,
        countif(is_goal and event_detail = 'Penalty') as goals_penalty
    from events
    where player_id is not null
    group by fixture_id, team_id, player_id
),

player_assists as (
    select
        fixture_id,
        team_id,
        assist_player_id as player_id,
        countif(is_goal and not is_own_goal) as assists
    from events
    where assist_player_id is not null
    group by fixture_id, team_id, assist_player_id
),

sendings_off as (
    select
        fixture_id,
        player_id,
        min(minute_elapsed) as minute_sent_off
    from events
    where
        event_type = 'Card'
        and coalesce(event_detail, '') != 'Yellow Card'
        and player_id is not null
    group by fixture_id, player_id
),

-- Extra time shows in the status, or, for a match settled on penalties, in an event past minute 90.
played_spells as (
    select
        s.*,
        coalesce(m.assisted_goal_events, 0) as match_assisted_goal_events,
        coalesce(t.goal_events, 0) as team_goal_events,
        coalesce(t.goal_events_without_scorer, 0) as team_goal_events_without_scorer,
        coalesce(t.own_goals, 0) as team_own_goals,
        coalesce(t.open_play_goal_events, 0) as team_open_play_goal_events,
        coalesce(t.assisted_goal_events, 0) as team_assisted_goal_events,
        coalesce(g.goals, 0) as event_goals,
        coalesce(g.goals_penalty, 0) as event_goals_penalty,
        coalesce(a.assists, 0) as event_assists,
        nullif(least(coalesce(s.minute_off, 999), coalesce(o.minute_sent_off, 999)), 999) as minute_gone,
        if(s.status_short = 'AET' or (s.status_short = 'PEN' and coalesce(m.has_extra_time_event, false)), 120, 90)
            as match_minutes
    from sheets as s
    left join match_events as m
        on s.fixture_id = m.fixture_id
    left join team_events as t
        on s.fixture_id = t.fixture_id and s.team_id = t.team_id
    left join player_goals as g
        on s.fixture_id = g.fixture_id and s.team_id = g.team_id and s.player_id = g.player_id
    left join player_assists as a
        on s.fixture_id = a.fixture_id and s.team_id = a.team_id and s.player_id = a.player_id
    left join sendings_off as o
        on s.fixture_id = o.fixture_id and s.player_id = o.player_id
),

-- A match with no substitution on its sheets lacks that input, so its minutes stay blank. A player
-- who came on in the last minute played; his appearance needs a minute. A substitute with no minute
-- on who scored or assisted did play, and his minutes stay blank.
with_minutes as (
    select
        *,
        case
            when countif(minute_on is not null) over (partition by league_code, fixture_id) = 0 then null
            when is_starter or minute_on is not null
                then greatest(
                    least(coalesce(minute_gone, match_minutes), match_minutes) - coalesce(minute_on, 0),
                    1
                )
            when event_goals + event_assists > 0 then null
            else 0
        end as minutes
    from played_spells
),

-- The goal events name a team's goals only where they add up to its score and every scorer stands
-- on its sheet.
with_team_totals as (
    select
        *,
        sum(event_goals) over team_match as goals_on_sheet,
        sum(event_assists) over team_match as assists_on_sheet,
        countif(position_code = 'G' and minutes > 0) over team_match as team_keepers_with_minutes
    from with_minutes
    window team_match as (partition by league_code, fixture_id, team_id)
),

goals_checked as (
    select
        *,
        team_goal_events_without_scorer = 0
        and team_goal_events + team_own_goals = team_goals_for
        and goals_on_sheet = team_goal_events as goals_add_up
    from with_team_totals
),

-- An own goal is filed under the team it counts for, so every goal under the opponent is conceded.
keeper_spells as (
    select
        k.league_code,
        k.fixture_id,
        k.team_id,
        k.player_id,
        count(e.minute_elapsed) as goal_events_conceded,
        countif(
            e.minute_elapsed > coalesce(k.minute_on, -1) and e.minute_elapsed < coalesce(k.minute_gone, 999)
        ) as goals_conceded_in_spell,
        countif(e.minute_elapsed = k.minute_on or e.minute_elapsed = k.minute_gone) as goals_at_a_change
    from goals_checked as k
    left join events as e
        on k.fixture_id = e.fixture_id and k.team_id != e.team_id and e.is_goal
    where k.position_code = 'G' and (k.minute_on is not null or k.minute_gone is not null)
    group by k.league_code, k.fixture_id, k.team_id, k.player_id
),

cleaned as (
    select
        g.league_code,
        g.fixture_id,
        g.team_id,
        g.player_id,
        g.minutes,
        g.shirt_number,
        g.position_code,
        g.raw_ingested_at,
        not g.is_starter as is_substitute,
        case
            when g.team_goals_for = 0 then 0
            when g.goals_add_up then g.event_goals
        end as goals,
        case
            when g.team_goals_for = 0 then 0
            when g.goals_add_up then g.event_goals_penalty
        end as goals_penalty,
        case
            when g.team_goals_for = 0 then 0
            when
                g.goals_add_up
                and g.assists_on_sheet = g.team_assisted_goal_events
                and (g.team_open_play_goal_events = 0 or g.match_assisted_goal_events > 0)
                then g.event_assists
        end as assists,
        case
            when g.team_goals_conceded = 0 then 0
            when coalesce(g.position_code, '') != 'G' then null
            when g.minutes = 0 then 0
            when g.minute_on is null and g.minute_gone is null and g.team_keepers_with_minutes = 1
                then g.team_goals_conceded
            when k.goal_events_conceded = g.team_goals_conceded and k.goals_at_a_change = 0
                then k.goals_conceded_in_spell
        end as goals_against
    from goals_checked as g
    left join keeper_spells as k
        on
            g.league_code = k.league_code
            and g.fixture_id = k.fixture_id
            and g.team_id = k.team_id
            and g.player_id = k.player_id
)

select
    league_code,
    fixture_id,
    team_id,
    player_id,
    minutes,
    shirt_number,
    position_code,
    cast(null as bool) as is_captain,
    is_substitute,
    cast(null as int64) as offsides,
    cast(null as int64) as shots,
    cast(null as int64) as shots_on_target,
    goals,
    goals_penalty,
    goals_against,
    assists,
    cast(null as int64) as saves,
    cast(null as int64) as passes,
    cast(null as int64) as passes_key,
    cast(null as int64) as passes_accurate,
    cast(null as int64) as tackles,
    cast(null as int64) as blocks,
    cast(null as int64) as interceptions,
    cast(null as int64) as duels,
    cast(null as int64) as duels_won,
    cast(null as int64) as dribbles,
    cast(null as int64) as dribbles_success,
    cast(null as int64) as dribbles_against,
    cast(null as int64) as fouls,
    cast(null as int64) as fouls_against,
    cast(null as int64) as cards_yellow,
    cast(null as int64) as cards_red,
    cast(null as int64) as penalties_won,
    cast(null as int64) as penalties_committed,
    goals_penalty as penalties_scored,
    cast(null as int64) as penalties_missed,
    cast(null as int64) as penalties_saved,
    raw_ingested_at
from cleaned
