{#
  W2 season-record mart — player. One row per player per upcoming fixture side: the
  player's cumulative record in the fixture's own competition this season (complement to
  mart_player_momentum, W1 = last 5).

  Source: int_player_season_record, which computes every metric (counts and ratios) from its catalogue
  formula. Each upcoming fixture side's team is joined to its players' latest season-to-date row for the
  fixture's (league_code, season_api_year); a side with no row there yet takes the same competition's previous
  season (window_type='prev_season'). Goals, assists and shots on target are handed to the export under the keys
  the site reads (goals_total, goals_assists, shots_on). saves_player_pct is only meaningful for
  goalkeepers. top_player_rank orders a side by goals plus assists, then goals, then fewer minutes; NULL
  when the player's goals plus assists is unknown.
  The Players to watch boards rank a side's outfield players: scorer_points_rank by goals plus assists,
  then goals, then fewer minutes; ball_actions_per90_rank by ball actions per 90, then more minutes, among
  players with at least a third of the team's minutes in the window (team_matches x 90 / 3). Each is NULL
  for a player off its board. Grain: (upcoming_fixture_sk, team_sk, player_sk).
#}

with upcoming as (
    select
        fixture_sk,
        home_team_sk,
        away_team_sk,
        league_code,
        season_api_year
    from {{ ref('fct_fixture') }}
    where
        status_short in ('NS', 'TBD')
        and fixture_date >= current_date()
),

sides as (
    select
        fixture_sk as upcoming_fixture_sk,
        home_team_sk as team_sk,
        league_code,
        season_api_year,
        true as is_home
    from upcoming

    union all

    select
        fixture_sk as upcoming_fixture_sk,
        away_team_sk as team_sk,
        league_code,
        season_api_year,
        false as is_home
    from upcoming
),

season_final as (
    select *
    from {{ ref('int_player_season_record') }}
    qualify row_number() over (
        partition by team_sk, player_sk, league_code, season_api_year
        order by kickoff_datetime desc, fixture_sk desc
    ) = 1
),

matched as (
    select
        s.upcoming_fixture_sk,
        s.team_sk,
        sf.player_sk,
        s.league_code,
        s.is_home,
        sf.entity_type,
        sf.season_api_year,
        'season_to_date' as window_type,
        sf.position_code,
        sf.games_played,
        sf.goals_player,
        sf.assists_player,
        sf.saves_player,
        sf.shots_on_goal_player,
        sf.passes_key_player,
        sf.passes_accurate_player,
        sf.passes_player,
        sf.tackles_player,
        sf.blocks_player,
        sf.interceptions_player,
        sf.duels_won_player,
        sf.duels_player,
        sf.dribbles_success_player,
        sf.dribbles_attempts_player,
        sf.dribbles_past_player,
        sf.offsides_player,
        sf.penalty_won_player,
        sf.penalty_committed_player,
        sf.cards_yellow_player,
        sf.cards_red_player,
        sf.saves_player_pct,
        sf.dribbles_success_player_pct,
        sf.passes_accuracy_player_pct,
        sf.duels_won_player_pct,
        sf.scorer_points_player,
        sf.ball_actions_per90,
        sf.minutes,
        1 as priority
    from sides as s
    inner join season_final as sf
        on
            s.team_sk = sf.team_sk
            and s.league_code = sf.league_code
            and s.season_api_year = sf.season_api_year

    union all

    select
        s.upcoming_fixture_sk,
        s.team_sk,
        sf.player_sk,
        s.league_code,
        s.is_home,
        sf.entity_type,
        sf.season_api_year,
        'prev_season' as window_type,
        sf.position_code,
        sf.games_played,
        sf.goals_player,
        sf.assists_player,
        sf.saves_player,
        sf.shots_on_goal_player,
        sf.passes_key_player,
        sf.passes_accurate_player,
        sf.passes_player,
        sf.tackles_player,
        sf.blocks_player,
        sf.interceptions_player,
        sf.duels_won_player,
        sf.duels_player,
        sf.dribbles_success_player,
        sf.dribbles_attempts_player,
        sf.dribbles_past_player,
        sf.offsides_player,
        sf.penalty_won_player,
        sf.penalty_committed_player,
        sf.cards_yellow_player,
        sf.cards_red_player,
        sf.saves_player_pct,
        sf.dribbles_success_player_pct,
        sf.passes_accuracy_player_pct,
        sf.duels_won_player_pct,
        sf.scorer_points_player,
        sf.ball_actions_per90,
        sf.minutes,
        2 as priority
    from sides as s
    inner join season_final as sf
        on
            s.team_sk = sf.team_sk
            and s.league_code = sf.league_code
            and sf.season_api_year = s.season_api_year - 1
),

players as (
    select
        player_sk,
        player_name,
        player_photo_url,
        player_position
    from {{ ref('dim_player') }}
),

team_matches as (
    select
        team_sk,
        league_code,
        season_api_year,
        count(distinct if(not is_awarded_result, fixture_sk, null)) as team_matches
    from {{ ref('int_legs__team_match') }}
    group by team_sk, league_code, season_api_year
),

chosen as (
    select
        m.*,
        p.player_name,
        p.player_photo_url,
        tm.team_matches,
        if(m.position_code is null, coalesce(p.player_position != 'Goalkeeper', true), m.position_code != 'G')
            as is_outfield
    from matched as m
    left join players as p
        on m.player_sk = p.player_sk
    left join team_matches as tm
        on
            m.team_sk = tm.team_sk
            and m.league_code = tm.league_code
            and m.season_api_year = tm.season_api_year
    qualify m.priority = min(m.priority) over (partition by m.upcoming_fixture_sk, m.team_sk)
),

-- The two Players to watch boards. A most-first board leaves out a zero (ranking_rules).
boards as (
    select
        *,
        is_outfield and scorer_points_player > 0 as on_scorer_points_board,
        is_outfield and ball_actions_per90 > 0 and minutes >= team_matches * 90 / 3
            as on_ball_actions_per90_board
    from chosen
)

select
    upcoming_fixture_sk,
    team_sk,
    player_sk,
    player_name,
    player_photo_url,
    league_code,
    entity_type,
    season_api_year,
    window_type,
    position_code,
    games_played,
    minutes,
    is_home,
    -- cumulative counts
    goals_player as goals_total,
    assists_player as goals_assists,
    scorer_points_player,
    saves_player,
    shots_on_goal_player as shots_on,
    passes_key_player,
    passes_accurate_player,
    passes_player,
    tackles_player,
    blocks_player,
    interceptions_player,
    duels_won_player,
    duels_player,
    dribbles_success_player,
    dribbles_attempts_player,
    dribbles_past_player,
    offsides_player,
    penalty_won_player,
    penalty_committed_player,
    cards_yellow_player,
    cards_red_player,
    -- ratios
    saves_player_pct,
    dribbles_success_player_pct,
    passes_accuracy_player_pct,
    duels_won_player_pct,
    ball_actions_per90,
    team_matches,
    if(
        scorer_points_player is null,
        null,
        row_number() over (
            partition by upcoming_fixture_sk, team_sk, scorer_points_player is null
            order by scorer_points_player desc, goals_player desc, minutes asc nulls last, player_sk asc
        )
    ) as top_player_rank,
    if(
        on_scorer_points_board,
        row_number() over (
            partition by upcoming_fixture_sk, team_sk, on_scorer_points_board
            order by scorer_points_player desc, goals_player desc, minutes asc nulls last, player_sk asc
        ),
        null
    ) as scorer_points_rank,
    if(
        on_ball_actions_per90_board,
        row_number() over (
            partition by upcoming_fixture_sk, team_sk, on_ball_actions_per90_board
            order by ball_actions_per90 desc, minutes desc, player_sk asc
        ),
        null
    ) as ball_actions_per90_rank
from boards
