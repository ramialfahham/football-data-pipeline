{#
  mart_competition_fixtures — every match of a competition-season, played and unplayed, one row
  per fixture, with both teams named and linked and the round it belongs to. The competition
  page's Matchdays tab shows one competition-season of it, one round at a time; the export reads
  the table whole and groups the rows by round.

  Rounds. round_name is the provider's label. round_order is its trailing integer — a league's
  matchday; null for a named cup round. round_sequence ranks a competition-season's rounds by
  their first kick-off, the order the tab steps through them; a postponed match keeps its round,
  so a straggler played late does not move its round.

  Played. A fixture with a finished leg in int_legs__team_match — the one definition of a result
  (full time, after extra time, on penalties, or awarded), never restated here.

  is_next_round is mart_next_matchday's round, not a second derivation: every fixture of the
  round that mart serves for the competition is flagged, played or not, so this table and the Home
  page can never name different next matchdays. is_match_that_matters is that mart's flag carried
  over, false on every other row. fixture_order is the reading order of a competition-season's
  rows, rounds in sequence and each round by kick-off, so nothing downstream sorts.

  is_last_round is the round just played: in the season of the competition's next matchday (its
  current season), the latest round by round_sequence with a played fixture, and only that round's
  played fixtures. A round in progress carries both flags, its played rows this one and its unplayed
  rows is_next_round; a postponed fixture is never flagged until it is played; a competition with no
  next matchday (a finished tournament) has no current season and no flag.

  is_home_team_next_match and is_away_team_next_match mark each team's earliest match not yet
  started (status NS or TBD, kick-off after the build), in any competition: a team's next match is
  a filter of this table, so every page names the same one.

  fixture_slug is the match's permanent URL segment: the kick-off date, the home team's slug,
  "-vs-", the away team's slug — the two published team slugs, so a team is spelt the same in its
  own URL and in every match URL. A fixture whose team is unknown to dim_team gets no slug and
  fails the tests, which name it, instead of the build inventing a URL.

  Goals. A played match's goals come from the first source that adds up to its score, side by
  side: its goal events (is_goal, with any goals corrected by hand), then its players' goals with
  its own-goal events. A played or abandoned match awarded afterwards adds up to its score on the
  pitch. goal_data_state names what the match has: goals (every goal with its minute; a 0-0 has
  none), goals_without_minutes (one entry per scorer), not_recorded (the provider recorded no goal),
  or awarded (award_kind says how; its goals as scored, none when not played). On a list in
  match order each goal carries the score after it.

  Result. winner_team_sk is the team that won or went through: the awarded team, else the
  shoot-out's winner, else the side with more goals; NULL on a draw.

  Line-ups. lineup_state names whether a played match's team sheets can be shown: confirmed,
  researched or not_available. The formations are served only for a confirmed or researched match.

  Grain: fixture_sk. league_code discriminates the competition and is not a BigQuery partition
  or cluster key.
#}

with fixtures as (
    select
        fixture_sk,
        league_code,
        season_api_year,
        round_name,
        kickoff_datetime,
        fixture_date,
        status_short,
        goals_home,
        goals_away,
        shootout_home,
        shootout_away,
        winner_team_sk,
        award_kind,
        on_pitch_home,
        on_pitch_away,
        home_team_sk,
        away_team_sk,
        venue_name_snapshot
    from {{ ref('fct_fixture') }}
),

team_next as (
    select
        fixture_sk,
        team_sk
    from (
        select
            fixture_sk,
            home_team_sk as team_sk,
            kickoff_datetime
        from fixtures
        where status_short in ('NS', 'TBD') and kickoff_datetime > current_timestamp()
        union all
        select
            fixture_sk,
            away_team_sk as team_sk,
            kickoff_datetime
        from fixtures
        where status_short in ('NS', 'TBD') and kickoff_datetime > current_timestamp()
    )
    qualify row_number() over (partition by team_sk order by kickoff_datetime asc, fixture_sk asc) = 1
),

teams as (
    select
        team_sk,
        team_name,
        team_slug,
        team_logo_url
    from {{ ref('dim_team') }}
),

played as (
    select distinct fixture_sk
    from {{ ref('int_legs__team_match') }}
),

flagged as (
    select
        fixture_sk,
        is_match_that_matters
    from {{ ref('mart_next_matchday') }}
),

next_round as (
    select distinct
        league_code,
        season_api_year,
        round_name
    from {{ ref('mart_next_matchday') }}
),

rounds as (
    select
        league_code,
        season_api_year,
        round_name,
        dense_rank() over (
            partition by league_code, season_api_year
            order by min(kickoff_datetime) asc, round_name asc
        ) as round_sequence
    from fixtures
    group by league_code, season_api_year, round_name
),

last_round as (
    select
        f.league_code,
        f.season_api_year,
        max(r.round_sequence) as round_sequence
    from fixtures as f
    inner join next_round as n
        on
            f.league_code = n.league_code
            and f.season_api_year = n.season_api_year
    inner join played as p
        on f.fixture_sk = p.fixture_sk
    inner join rounds as r
        on
            f.league_code = r.league_code
            and f.season_api_year = r.season_api_year
            and f.round_name = r.round_name
    group by f.league_code, f.season_api_year
),

player_names as (
    select
        player_sk,
        player_name
    from {{ ref('dim_player') }}
),

scores as (
    select
        f.fixture_sk,
        f.home_team_sk,
        f.away_team_sk,
        if(f.award_kind in ('played', 'abandoned'), f.on_pitch_home, f.goals_home) as score_home,
        if(f.award_kind in ('played', 'abandoned'), f.on_pitch_away, f.goals_away) as score_away
    from fixtures as f
    inner join played as p
        on f.fixture_sk = p.fixture_sk
    where f.award_kind is distinct from 'not_played'
),

goal_events as (
    select
        e.fixture_sk,
        e.team_sk,
        e.player_sk,
        e.minute_elapsed,
        e.minute_extra,
        e.is_own_goal,
        e.assist_player_sk,
        e.event_index,
        coalesce(p.player_name, e.player_name_snapshot) as player_name,
        if(e.event_detail = 'Penalty', 1, 0) as penalties,
        coalesce(ap.player_name, e.assist_player_name) as assist_player_name
    from {{ ref('fct_fixture_event') }} as e
    left join player_names as p
        on e.player_sk = p.player_sk
    left join player_names as ap
        on e.assist_player_sk = ap.player_sk
    where e.is_goal
),

event_totals as (
    select
        s.fixture_sk,
        countif(g.team_sk = s.home_team_sk) = s.score_home
        and countif(g.team_sk = s.away_team_sk) = s.score_away
        and countif(g.team_sk not in (s.home_team_sk, s.away_team_sk)) = 0 as events_add_up,
        countif(g.fixture_sk is not null and g.minute_elapsed is null) = 0 as events_have_minutes
    from scores as s
    left join goal_events as g
        on s.fixture_sk = g.fixture_sk
    group by s.fixture_sk, s.score_home, s.score_away
),

player_lines as (
    select
        ps.fixture_sk,
        ps.team_sk,
        ps.player_sk,
        p.player_name,
        ps.goals,
        ps.goals_penalty
    from {{ ref('fct_fixture_player_stats') }} as ps
    inner join scores as s
        on ps.fixture_sk = s.fixture_sk
    left join player_names as p
        on ps.player_sk = p.player_sk
),

-- An own goal counts for the side its event names; the players' goals count for their own team.
own_goal_totals as (
    select
        s.fixture_sk,
        countif(g.team_sk = s.home_team_sk) as own_goals_home,
        countif(g.team_sk = s.away_team_sk) as own_goals_away
    from scores as s
    left join goal_events as g
        on s.fixture_sk = g.fixture_sk and g.is_own_goal
    group by s.fixture_sk
),

player_totals as (
    select
        s.fixture_sk,
        coalesce(logical_and(l.goals is not null), false)
        and coalesce(sum(if(l.team_sk = s.home_team_sk, l.goals, 0)), 0) + o.own_goals_home = s.score_home
        and coalesce(sum(if(l.team_sk = s.away_team_sk, l.goals, 0)), 0) + o.own_goals_away = s.score_away
            as players_add_up
    from scores as s
    inner join own_goal_totals as o
        on s.fixture_sk = o.fixture_sk
    left join player_lines as l
        on s.fixture_sk = l.fixture_sk
    group by s.fixture_sk, s.score_home, s.score_away, o.own_goals_home, o.own_goals_away
),

goal_sources as (
    select
        s.fixture_sk,
        case
            when e.events_add_up then 'events'
            when p.players_add_up then 'players'
        end as goal_source,
        e.events_add_up and e.events_have_minutes as has_minutes
    from scores as s
    inner join event_totals as e
        on s.fixture_sk = e.fixture_sk
    inner join player_totals as p
        on s.fixture_sk = p.fixture_sk
),

served_goals as (
    select
        g.fixture_sk,
        g.team_sk,
        g.player_sk,
        g.player_name,
        g.minute_elapsed,
        g.minute_extra,
        1 as goals,
        g.penalties,
        g.is_own_goal,
        g.assist_player_sk,
        g.assist_player_name,
        g.event_index
    from goal_events as g
    inner join goal_sources as s
        on g.fixture_sk = s.fixture_sk
    where s.goal_source = 'events'
    union all
    select
        l.fixture_sk,
        l.team_sk,
        l.player_sk,
        l.player_name,
        cast(null as int64) as minute_elapsed,
        cast(null as int64) as minute_extra,
        l.goals,
        l.goals_penalty as penalties,
        false as is_own_goal,
        cast(null as int64) as assist_player_sk,
        cast(null as string) as assist_player_name,
        cast(null as int64) as event_index
    from player_lines as l
    inner join goal_sources as s
        on l.fixture_sk = s.fixture_sk
    where s.goal_source = 'players' and l.goals > 0
    union all
    select
        g.fixture_sk,
        g.team_sk,
        g.player_sk,
        g.player_name,
        cast(null as int64) as minute_elapsed,
        cast(null as int64) as minute_extra,
        1 as goals,
        0 as penalties,
        true as is_own_goal,
        cast(null as int64) as assist_player_sk,
        cast(null as string) as assist_player_name,
        g.event_index
    from goal_events as g
    inner join goal_sources as s
        on g.fixture_sk = s.fixture_sk
    where s.goal_source = 'players' and g.is_own_goal
),

scorer_goals as (
    select
        g.fixture_sk,
        g.team_sk,
        g.player_sk,
        g.player_name,
        g.is_own_goal,
        sum(g.goals) as goals,
        sum(g.penalties) as penalties
    from served_goals as g
    inner join goal_sources as s
        on g.fixture_sk = s.fixture_sk
    where not s.has_minutes
    group by g.fixture_sk, g.team_sk, g.player_sk, g.player_name, g.is_own_goal
),

timed_goals as (
    select
        g.fixture_sk,
        g.player_sk,
        g.player_name,
        g.minute_elapsed,
        g.minute_extra,
        g.goals,
        g.penalties,
        g.is_own_goal,
        g.assist_player_sk,
        g.assist_player_name,
        g.event_index,
        case g.team_sk when sc.home_team_sk then 'home' when sc.away_team_sk then 'away' end as side,
        countif(g.team_sk = sc.home_team_sk) over match_so_far as score_home_after,
        countif(g.team_sk = sc.away_team_sk) over match_so_far as score_away_after
    from served_goals as g
    inner join goal_sources as s
        on g.fixture_sk = s.fixture_sk
    inner join scores as sc
        on g.fixture_sk = sc.fixture_sk
    where s.has_minutes
    window match_so_far as (
        partition by g.fixture_sk
        order by g.minute_elapsed, g.minute_extra, g.event_index
        rows between unbounded preceding and current row
    )
),

-- With every minute known, one entry per goal in match order; otherwise one entry per scorer. A
-- player's provider id is his player_sk.
goal_lists as (
    select
        g.fixture_sk,
        array_agg(
            struct(
                g.side,
                g.player_sk as player_api_id,
                g.player_name,
                g.minute_elapsed,
                g.minute_extra,
                g.goals,
                g.penalties,
                g.is_own_goal,
                g.assist_player_sk as assist_player_api_id,
                g.assist_player_name,
                g.score_home_after,
                g.score_away_after
            )
            order by g.minute_elapsed, g.minute_extra, g.event_index
        ) as goals
    from timed_goals as g
    group by g.fixture_sk
    union all
    select
        g.fixture_sk,
        array_agg(
            struct(
                case g.team_sk when sc.home_team_sk then 'home' when sc.away_team_sk then 'away' end as side,
                g.player_sk as player_api_id,
                g.player_name,
                cast(null as int64) as minute_elapsed,
                cast(null as int64) as minute_extra,
                g.goals,
                g.penalties,
                g.is_own_goal,
                cast(null as int64) as assist_player_api_id,
                cast(null as string) as assist_player_name,
                cast(null as int64) as score_home_after,
                cast(null as int64) as score_away_after
            )
            order by g.goals desc, g.player_name asc
        ) as goals
    from scorer_goals as g
    inner join scores as sc
        on g.fixture_sk = sc.fixture_sk
    group by g.fixture_sk
),

formations as (
    select
        fixture_sk,
        team_sk,
        any_value(team_formation) as team_formation
    from {{ ref('fct_fixture_lineup') }}
    where lineup_state in ('confirmed', 'researched')
    group by fixture_sk, team_sk
),

lineup_states as (
    select
        fixture_sk,
        any_value(lineup_state) as lineup_state
    from {{ ref('fct_fixture_lineup') }}
    where lineup_state in ('confirmed', 'researched')
    group by fixture_sk
)

select
    f.fixture_sk,
    f.league_code,
    f.season_api_year,
    f.round_name,
    r.round_sequence,
    f.kickoff_datetime,
    f.fixture_date,
    f.status_short,
    f.goals_home,
    f.goals_away,
    f.shootout_home,
    f.shootout_away,
    f.winner_team_sk,
    f.home_team_sk,
    h.team_name as home_team_name,
    h.team_slug as home_team_slug,
    h.team_logo_url as home_team_logo_url,
    hf.team_formation as home_team_formation,
    f.away_team_sk,
    a.team_name as away_team_name,
    a.team_slug as away_team_slug,
    a.team_logo_url as away_team_logo_url,
    af.team_formation as away_team_formation,
    f.venue_name_snapshot as venue_name,
    f.award_kind,
    f.on_pitch_home,
    f.on_pitch_away,
    gl.goals,
    safe_cast(regexp_extract(f.round_name, r'(\d+)$') as int64) as round_order,
    p.fixture_sk is not null as is_played,
    case
        when h.team_slug is not null and a.team_slug is not null
            then concat(
                format_date('%Y-%m-%d', f.fixture_date), '-', h.team_slug, '-vs-', a.team_slug
            )
    end as fixture_slug,
    n.round_name is not null as is_next_round,
    l.league_code is not null and p.fixture_sk is not null as is_last_round,
    coalesce(m.is_match_that_matters, false) as is_match_that_matters,
    nh.fixture_sk is not null as is_home_team_next_match,
    na.fixture_sk is not null as is_away_team_next_match,
    case
        when p.fixture_sk is null then null
        when f.status_short in ('AWD', 'WO') then 'awarded'
        when gs.goal_source = 'events' and gs.has_minutes then 'goals'
        when gs.goal_source is not null then 'goals_without_minutes'
        else 'not_recorded'
    end as goal_data_state,
    case
        when p.fixture_sk is null then null
        else coalesce(ls.lineup_state, 'not_available')
    end as lineup_state,
    row_number() over (
        partition by f.league_code, f.season_api_year
        order by r.round_sequence asc, f.kickoff_datetime asc, f.fixture_sk asc
    ) as fixture_order
from fixtures as f
inner join rounds as r
    on
        f.league_code = r.league_code
        and f.season_api_year = r.season_api_year
        and f.round_name = r.round_name
left join teams as h
    on f.home_team_sk = h.team_sk
left join teams as a
    on f.away_team_sk = a.team_sk
left join played as p
    on f.fixture_sk = p.fixture_sk
left join flagged as m
    on f.fixture_sk = m.fixture_sk
left join next_round as n
    on
        f.league_code = n.league_code
        and f.season_api_year = n.season_api_year
        and f.round_name = n.round_name
left join last_round as l
    on
        f.league_code = l.league_code
        and f.season_api_year = l.season_api_year
        and r.round_sequence = l.round_sequence
left join team_next as nh
    on
        f.fixture_sk = nh.fixture_sk
        and f.home_team_sk = nh.team_sk
left join team_next as na
    on
        f.fixture_sk = na.fixture_sk
        and f.away_team_sk = na.team_sk
left join goal_sources as gs
    on f.fixture_sk = gs.fixture_sk
left join goal_lists as gl
    on f.fixture_sk = gl.fixture_sk
left join formations as hf
    on
        f.fixture_sk = hf.fixture_sk
        and f.home_team_sk = hf.team_sk
left join formations as af
    on
        f.fixture_sk = af.fixture_sk
        and f.away_team_sk = af.team_sk
left join lineup_states as ls
    on f.fixture_sk = ls.fixture_sk
