{#
  The team competition-benchmark metrics in LONG form, per team-season: one row per
  (team_sk, season_sk, metric_key) unpivoted from int_team_season__metrics (season-to-date, teams with
  at least the var team_min_matches finished games). The set is every team metric the site's served
  list shows (metric_rows.json) plus the shots-on-target difference and the clean-sheet share. This is the single source of the
  benchmark metric set — both int_team_competition_benchmarks (which aggregates it to the league
  distribution) and mart_team_competition_benchmarks (which ranks each team against that
  distribution) read from here, so the two cannot drift apart. BigQuery UNPIVOT excludes nulls, so a
  metric with no value for a team (e.g. a player-stat coverage gap) simply yields no row. Counts are
  cast to FLOAT64, the one type an UNPIVOT column list holds.

  Each row also carries the team's value at the same point last season (rule R6), from
  int_team_season__metrics_cumulative, chosen as int_team_profile__yoy chooses it: the previous
  season's latest match at or before this season's match count, domestic leagues only.
  Grain: (team_sk, season_sk, metric_key).
#}

with season as (
    select
        team_sk,
        season_sk,
        league_sk,
        league_code,
        season_api_year,
        season_games_played,
        goals_per_match,
        goals_against_per_match,
        cast(clean_sheets as float64) as clean_sheets,
        clean_sheets_pct,
        shots_per_match,
        shots_on_goal_pct,
        shots_inside_box_pct,
        shots_inside_box_per_match,
        shots_on_goal_per_match,
        shots_on_goal_against_per_match,
        shots_on_goal_difference_per_match,
        finishing_efficiency_pct,
        duels_per_match,
        duels_won_per_match,
        duels_won_pct,
        defensive_actions_per_match,
        tackles_per_match,
        interceptions_per_match,
        blocks_per_match,
        passes_per_match,
        passes_accurate_per_match,
        passes_accuracy_pct,
        passes_share_pct,
        passes_key_per_match,
        dribbles_attempts_per_match,
        dribbles_success_per_match,
        dribbles_success_pct,
        corners_per_match,
        corners_against_per_match,
        free_kicks_per_match,
        fouls_per_match,
        offsides_per_match,
        saves_per_match,
        saves_pct,
        cast(cards_yellow as float64) as cards_yellow,
        cast(cards_red as float64) as cards_red
    from {{ ref('int_team_season__metrics') }}
    where season_games_played >= {{ var('team_min_matches') }}
),

registry as (
    select
        league_code,
        competition_type
    from {{ ref('competition_registry') }}
),

domestic_cumulative as (
    select c.*
    from {{ ref('int_team_season__metrics_cumulative') }} as c
    inner join registry as r
        on c.league_code = r.league_code
    where r.competition_type = 'domestic_league'
),

-- each domestic team-season's match count, the N its previous season is read at
season_n as (
    select
        team_sk,
        league_code,
        season_api_year,
        max(match_number) as match_count
    from domestic_cumulative
    group by team_sk, league_code, season_api_year
),

previous as (
    select
        n.team_sk,
        n.league_code,
        n.season_api_year,
        c.goals_per_match,
        c.goals_against_per_match,
        cast(c.clean_sheets as float64) as clean_sheets,
        c.clean_sheets_pct,
        c.shots_per_match,
        c.shots_on_goal_pct,
        c.shots_inside_box_pct,
        c.shots_inside_box_per_match,
        c.shots_on_goal_per_match,
        c.shots_on_goal_against_per_match,
        c.shots_on_goal_difference_per_match,
        c.finishing_efficiency_pct,
        c.duels_per_match,
        c.duels_won_per_match,
        c.duels_won_pct,
        c.defensive_actions_per_match,
        c.tackles_per_match,
        c.interceptions_per_match,
        c.blocks_per_match,
        c.passes_per_match,
        c.passes_accurate_per_match,
        c.passes_accuracy_pct,
        c.passes_share_pct,
        c.passes_key_per_match,
        c.dribbles_attempts_per_match,
        c.dribbles_success_per_match,
        c.dribbles_success_pct,
        c.corners_per_match,
        c.corners_against_per_match,
        c.free_kicks_per_match,
        c.fouls_per_match,
        c.offsides_per_match,
        c.saves_per_match,
        c.saves_pct,
        cast(c.cards_yellow as float64) as cards_yellow,
        cast(c.cards_red as float64) as cards_red
    from season_n as n
    inner join domestic_cumulative as c
        on
            n.team_sk = c.team_sk
            and n.league_code = c.league_code
            and n.season_api_year - 1 = c.season_api_year
            and n.match_count >= c.match_number
    qualify row_number() over (
        partition by n.team_sk, n.league_code, n.season_api_year
        order by c.match_number desc
    ) = 1
),

current_long as (
    select
        team_sk,
        season_sk,
        league_sk,
        league_code,
        season_api_year,
        metric_key,
        metric_value
    from season
    unpivot (
        metric_value for metric_key in (
            goals_per_match,
            goals_against_per_match,
            clean_sheets,
            clean_sheets_pct,
            shots_per_match,
            shots_on_goal_pct,
            shots_inside_box_pct,
            shots_inside_box_per_match,
            shots_on_goal_per_match,
            shots_on_goal_against_per_match,
            shots_on_goal_difference_per_match,
            finishing_efficiency_pct,
            duels_per_match,
            duels_won_per_match,
            duels_won_pct,
            defensive_actions_per_match,
            tackles_per_match,
            interceptions_per_match,
            blocks_per_match,
            passes_per_match,
            passes_accurate_per_match,
            passes_accuracy_pct,
            passes_share_pct,
            passes_key_per_match,
            dribbles_attempts_per_match,
            dribbles_success_per_match,
            dribbles_success_pct,
            corners_per_match,
            corners_against_per_match,
            free_kicks_per_match,
            fouls_per_match,
            offsides_per_match,
            saves_per_match,
            saves_pct,
            cards_yellow,
            cards_red
        )
    )
),

previous_long as (
    select
        team_sk,
        league_code,
        season_api_year,
        metric_key,
        metric_value
    from previous
    unpivot (
        metric_value for metric_key in (
            goals_per_match,
            goals_against_per_match,
            clean_sheets,
            clean_sheets_pct,
            shots_per_match,
            shots_on_goal_pct,
            shots_inside_box_pct,
            shots_inside_box_per_match,
            shots_on_goal_per_match,
            shots_on_goal_against_per_match,
            shots_on_goal_difference_per_match,
            finishing_efficiency_pct,
            duels_per_match,
            duels_won_per_match,
            duels_won_pct,
            defensive_actions_per_match,
            tackles_per_match,
            interceptions_per_match,
            blocks_per_match,
            passes_per_match,
            passes_accurate_per_match,
            passes_accuracy_pct,
            passes_share_pct,
            passes_key_per_match,
            dribbles_attempts_per_match,
            dribbles_success_per_match,
            dribbles_success_pct,
            corners_per_match,
            corners_against_per_match,
            free_kicks_per_match,
            fouls_per_match,
            offsides_per_match,
            saves_per_match,
            saves_pct,
            cards_yellow,
            cards_red
        )
    )
)

select
    cur.team_sk,
    cur.season_sk,
    cur.league_sk,
    cur.league_code,
    cur.season_api_year,
    cur.metric_key,
    cur.metric_value,
    prev.metric_value as metric_value_prev_season
from current_long as cur
left join previous_long as prev
    on
        cur.team_sk = prev.team_sk
        and cur.league_code = prev.league_code
        and cur.season_api_year = prev.season_api_year
        and cur.metric_key = prev.metric_key
