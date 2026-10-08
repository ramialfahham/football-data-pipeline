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
  when the player's goals plus assists is unknown. Grain: (upcoming_fixture_sk, team_sk, player_sk).
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
        sf.minutes,
        2 as priority
    from sides as s
    inner join season_final as sf
        on
            s.team_sk = sf.team_sk
            and s.league_code = sf.league_code
            and sf.season_api_year = s.season_api_year - 1
),

chosen as (
    select *
    from matched
    qualify priority = min(priority) over (partition by upcoming_fixture_sk, team_sk)
)

select
    upcoming_fixture_sk,
    team_sk,
    player_sk,
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
    if(
        scorer_points_player is null,
        null,
        row_number() over (
            partition by upcoming_fixture_sk, team_sk, scorer_points_player is null
            order by scorer_points_player desc, goals_player desc, minutes asc nulls last, player_sk asc
        )
    ) as top_player_rank
from chosen
