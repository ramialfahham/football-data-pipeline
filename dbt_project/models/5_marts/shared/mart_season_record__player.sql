{{ config(materialized='view') }}

{#
  W2 season-record mart — player. One row per player per upcoming fixture side: the
  player's cumulative record in the fixture's own competition this season (complement to
  mart_momentum__player, W1 = last 5).

  Source: int_season_record__player. Each upcoming fixture side's team is joined to its
  players' latest season-to-date row for the fixture's (league_code, season_api_year);
  before-phase fallback to the same competition's previous season (window_type='prev_season').

  Raw counts passed through; ratios (save_pct, pass_accuracy_pct, duels_won_pct,
  dribbles_success_pct) computed here via safe_divide. save_pct is only meaningful for
  goalkeepers. Grain: (upcoming_fixture_sk, team_sk, player_sk).
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
    from {{ ref('int_season_record__player') }}
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
        sf.goals_total,
        sf.goals_conceded,
        sf.goals_assists,
        sf.goals_saves,
        sf.shots_on,
        sf.passes_key,
        sf.passes_accurate,
        sf.passes_total,
        sf.tackles_total,
        sf.tackles_blocks,
        sf.tackles_interceptions,
        sf.duels_won,
        sf.duels_total,
        sf.dribbles_success,
        sf.dribbles_attempts,
        sf.dribbles_past,
        sf.offsides,
        sf.penalty_won,
        sf.penalty_committed,
        sf.cards_yellow,
        sf.cards_red,
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
        sf.goals_total,
        sf.goals_conceded,
        sf.goals_assists,
        sf.goals_saves,
        sf.shots_on,
        sf.passes_key,
        sf.passes_accurate,
        sf.passes_total,
        sf.tackles_total,
        sf.tackles_blocks,
        sf.tackles_interceptions,
        sf.duels_won,
        sf.duels_total,
        sf.dribbles_success,
        sf.dribbles_attempts,
        sf.dribbles_past,
        sf.offsides,
        sf.penalty_won,
        sf.penalty_committed,
        sf.cards_yellow,
        sf.cards_red,
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
    qualify row_number() over (
        partition by upcoming_fixture_sk, team_sk, player_sk
        order by priority asc
    ) = 1
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
    is_home,
    -- raw cumulative counts
    goals_total,
    goals_assists,
    goals_saves,
    shots_on,
    passes_key,
    passes_accurate,
    passes_total,
    tackles_total,
    tackles_blocks,
    tackles_interceptions,
    duels_won,
    duels_total,
    dribbles_success,
    dribbles_attempts,
    dribbles_past,
    offsides,
    penalty_won,
    penalty_committed,
    cards_yellow,
    cards_red,
    -- ratios
    safe_divide(goals_saves, goals_saves + goals_conceded) as save_pct,
    safe_divide(dribbles_success, dribbles_attempts) as dribbles_success_pct,
    safe_divide(passes_accurate, passes_total) as pass_accuracy_pct,
    safe_divide(duels_won, duels_total) as duels_won_pct
from chosen
