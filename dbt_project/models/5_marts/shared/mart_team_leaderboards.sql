{{ config(materialized='view') }}

{#
  mart_team_leaderboards — LONG per-board team rankings (the Top teams block; GAP-29). The team
  mirror of mart_leaderboards. One row per (team, board): where that team ranks on that board
  within its competition-season. Season-to-date, composed from int_team_season__metrics (the
  canonical whole-season team rollup) + dim_team identity — NOT mart-from-mart.

  FOUR boards, single-metric like the reduced player boards: goals_per_match,
  shots_on_goal_per_match, passes_per_match, duels_per_match. All four are higher_better in the
  metric catalogue, so one shared DESC order is correct for every board — a lower-is-better board
  would need its own direction and there is none here.

  rank = DENSE_RANK over the board's metric desc within (league_code, season_api_year): ties share a
  rank, no ranks are skipped, and the top-10 cut is inclusive of ties (the mart_leaderboards
  convention). The partition is per league — one team per league, same as players — so a board
  is each league's rank-1 team collected and ordered, and the ranking never
  crosses league_code. That also satisfies the block's rule that club and national-team
  competitions are never mixed: every competition is already its own ranking.

  NO GAMES FLOOR. A team ranks from its first finished game: early-season boards are thin and
  understood to be, and comparable sites show leaderboards from day one (GitLab #127). The
  >= 3 finished games gate that int_team_competition_benchmark_metrics_long applies is that
  model's rule for a DISTRIBUTION, where a one-game rate would distort the percentiles; a
  ranking has no such distortion to guard. The player mart's minutes/position floors have no
  analogue here either.

  UNPIVOT rather than mart_leaderboards' union-all loop, because all four boards share one rule —
  the union there exists to give each rate board its own qualification WHERE. BigQuery UNPIVOT
  excludes nulls, so a metric with no value for a team (a coverage gap) yields no row rather than a
  null rank. Source is int_team_season__metrics, deliberately NOT the benchmark long form: that
  model is the single source of the BENCHMARK metric set, and reading it here would couple this
  block's boards to that set.

  Grain: (team_sk, season_sk, metric_key).
#}

{# The board set. Adding or removing a key here must also move seeds' accepted_values AND the
   singular test — accepted_values alone is blind to a REMOVED board (a smaller set is still a
   subset), which is the silent direction. #}
{% set boards = [
    'goals_per_match',
    'shots_on_goal_per_match',
    'passes_per_match',
    'duels_per_match',
] %}

with season as (
    select * from {{ ref('int_team_season__metrics') }}
    where season_games_played >= 1
),

-- One row per (team-season, board). UNPIVOT drops nulls, so a team missing a metric through a
-- coverage gap is absent from that board rather than ranked on a null.
long as (
    select
        team_sk,
        season_sk,
        league_sk,
        league_code,
        season_api_year,
        season_games_played,
        metric_key,
        metric_value
    from season
    unpivot (
        metric_value for metric_key in (
            {% for board in boards %}
            {{ board }}{% if not loop.last %},{% endif %}
            {% endfor %}
        )
    )
),

-- Identity only. dim_team is unique on team_sk, so the left join cannot fan the row count out.
teams as (
    select
        team_sk,
        team_name,
        team_slug,
        team_logo_url
    from {{ ref('dim_team') }}
),

base as (
    select
        l.team_sk,
        l.season_sk,
        l.league_sk,
        l.league_code,
        l.season_api_year,
        l.season_games_played,
        l.metric_key,
        l.metric_value,
        t.team_name,
        t.team_slug,
        t.team_logo_url
    from long as l
    left join teams as t on l.team_sk = t.team_sk
),

ranked as (
    select
        base.*,
        dense_rank() over (
            partition by league_code, season_api_year, metric_key
            order by metric_value desc
        ) as board_rank,
        -- The TIE-BROKEN order within a league. `board_rank` above is a DENSE_RANK and stays one:
        -- ties sharing a rank, and the top-10 cut being inclusive of them, are a documented consumer
        -- contract. But a consumer that must show ONE team per league cannot use it — measured
        -- against prod, 2 of 259 league-board-seasons have more than one rank-1 team.
        -- Rare, but the block claims one team per league, and deciding WHICH is ranking, so it
        -- belongs here: all ranking and ordering lives in the warehouse, and the page renders the
        -- order it is served.
        -- ⛔ NO SPORTING TIE-BREAK EXISTS HERE, AND THAT IS DELIBERATE, NOT AN OVERSIGHT. The player
        -- mart breaks a tie on fewer MINUTES played, and teams have no minutes. `season_games_played`
        -- is the obvious analogue and was rejected — it will not work most of the time — for
        -- two reasons, the second being the real one: it barely discriminates (3.6 distinct game
        -- counts per league-season on average, and in 72 of 235 every team is level), and for a RATE
        -- fewer games is not better, it is LESS EVIDENCE for the same rate.
        -- So `team_sk` is the whole tie-break, and it is MEANINGLESS. It exists only so the order is
        -- stable and the committed payload does not churn between exports. GitLab #114 is open to
        -- find something that means anything.
        row_number() over (
            partition by league_code, season_api_year, metric_key
            order by metric_value desc, team_sk asc
        ) as league_leader_order
    from base
    where metric_value > 0
)

select
    {{ dbt_utils.generate_surrogate_key(['team_sk', 'season_sk', 'metric_key']) }}
        as team_leaderboard_sk,
    metric_key,
    board_rank as rank,
    league_leader_order,
    metric_value as sort_value,
    league_code,
    season_api_year,
    season_sk,
    league_sk,
    team_sk,
    team_name,
    team_slug,
    team_logo_url,
    season_games_played,
    -- WHICH SEASON a consumer should show, served as a fact rather than chosen downstream. Without
    -- it the export would pick a season itself, which is the window selection #846 moved out of that
    -- file. Same definition as mart_leaderboards: latest season per LEAGUE, not per team, so every
    -- row of a league agrees on the answer.
    rank() over (
        partition by league_code
        order by season_api_year desc
    ) = 1 as is_current_season,
    -- The order the league leaders appear in on a board, across every league, by the same rule.
    -- `league_leader_order` says WHICH team represents a league; this says in what ORDER those
    -- representatives are shown, so a consumer orders by one served column and compares nothing.
    -- NULL on any row that is not a league leader: the position is only defined among leaders, and a
    -- number here would invite ordering by a sequence the row is not part of.
    -- ⭐ PARTITIONED BY metric_key ALONE. The order is TOTAL, and restricting a total order to a
    -- subset preserves the relative sequence of what survives — so ranking every league leader
    -- globally lets any pool of leagues inherit the right order without this mart knowing which pool
    -- a consumer will show. Filtered to a handful of leagues the values are therefore SPARSE, which
    -- is the tell that the position is global. No season in the partition: `is_current_season` is
    -- per league, so leagues shown side by side can sit in different season years.
    -- ⚠ Computed here rather than in a CTE joined back, because SQLFluff rejects USING (ST07) and
    -- without it demands every column in this select be qualified (RF02). Sorting the leaders to the
    -- front of the window gives identical positions with no join.
    case
        when league_leader_order = 1 then row_number() over (
            partition by metric_key
            order by
                case when league_leader_order = 1 then 0 else 1 end,
                metric_value desc,
                team_sk asc
        )
    end as board_leader_order
from ranked
where board_rank <= 10
