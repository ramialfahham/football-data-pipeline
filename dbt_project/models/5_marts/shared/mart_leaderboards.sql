{{ config(materialized='view') }}

{#
  mart_leaderboards — LONG per-board player rankings (the Leaderboards block; content_architecture §3).
  Generalises the retired mart_top_scorers beyond goals. One row per (player, board): the player's rank on
  that board within its competition-season. Season-to-date, composed from the canonical
  int_player_season__metrics (the single source) + dim_player identity — NOT mart-from-mart.
  dim_team supplies the club a row belongs to, so a row can link to its club as well as its player.

  15 boards: 10 COUNT + 5 RATE (#506). metric_key = the catalogue metric_id. rank = DENSE_RANK over the
  board's metric desc within (league_code, season_api_year): ties share a rank, no ranks are skipped, and
  the top-10 cut is inclusive of ties (the mart_top_scorers convention). Only players with a positive
  value on a board are ranked (a leaderboard shows positive performers).

  RATE boards add a qualification rule (CPO, #506) so a tiny sample can't game a rate: minutes >= 270
  (3 full matches), a position scope, and — for finishing — a shots-on-target floor. pass / duels /
  dribble / finishing are outfield (excl. GK); save is GK-only. finishing also needs
  shots_on_goal_player >= 10 (minutes don't bound shot count, so a 1-shot 1-goal player would otherwise
  read a perfect rate). finishing_efficiency_player_pct is now open-play conversion in [0, 1] (CPO Option A).
  sort_value is FLOAT64: it holds both the integer counts and the 0-1 rates (the values are unchanged).

  Each row carries the union of the boards' display atoms so the export selects per board (marts contain
  what we show); sort_value is the board's own ranked value. Grain: (player_sk, season_sk, metric_key).
#}

{% set count_boards = [
    'goals_player',
    'assists_player',
    'scorer_points_player',
    'shots_on_goal_player',
    'dribbles_success_player',
    'passes_player',
    'passes_key_player',
    'duels_won_player',
    'defensive_actions_player',
    'cards_player',
] %}

{# RATE boards (#506): qualify on minutes >= 270 + a position scope (+ a SoT floor for finishing). #}
{% set outfield = "player_position is not null and player_position != 'Goalkeeper'" %}
{% set rate_boards = [
    {'key': 'passes_accuracy_player_pct', 'qualify': outfield},
    {'key': 'duels_won_player_pct', 'qualify': outfield},
    {'key': 'dribbles_success_player_pct', 'qualify': outfield},
    {'key': 'finishing_efficiency_player_pct', 'qualify': outfield ~ ' and shots_on_goal_player >= 10'},
    {'key': 'saves_player_pct', 'qualify': "player_position = 'Goalkeeper'"},
] %}

{# Unified board specs — each carries its own WHERE so ONE ranked loop drives the union-all
   guard. Count boards rank all positive performers; rate boards add the qualification rule. #}
{% set boards = [] %}
{% for key in count_boards %}
{% do boards.append({'key': key, 'where': key ~ ' > 0'}) %}
{% endfor %}
{% for board in rate_boards %}
{% set rate_where = 'minutes >= 270 and ' ~ board.qualify ~ ' and ' ~ board.key ~ ' > 0' %}
{% do boards.append({'key': board.key, 'where': rate_where}) %}
{% endfor %}

with season as (
    select * from {{ ref('int_player_season__metrics') }}
),

players as (
    select
        player_sk,
        player_name,
        player_nationality,
        player_position,
        player_photo_url
    from {{ ref('dim_player') }}
),

-- The club the row belongs to. team_sk arrives from int_player_season__metrics already resolved to
-- the player's last known club that competition-season, so this is identity lookup only — no
-- affiliation logic here, and deliberately not a join to a squad mart. dim_team is unique on
-- team_sk, so the left join cannot fan the row count out.
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
        s.player_sk,
        s.season_sk,
        s.league_sk,
        s.league_code,
        s.season_api_year,
        s.appearances,
        s.minutes,
        s.goals_player,
        s.assists_player,
        s.shots_on_goal_player,
        s.dribbles_attempts_player,
        s.dribbles_success_player,
        s.passes_player,
        s.passes_key_player,
        s.duels_player,
        s.duels_won_player,
        s.tackles_player,
        s.interceptions_player,
        s.blocks_player,
        s.cards_yellow_player,
        s.cards_red_player,
        s.scorer_points_player,
        s.defensive_actions_player,
        s.cards_player,
        s.passes_accuracy_player_pct,
        s.duels_won_player_pct,
        s.dribbles_success_player_pct,
        s.saves_player_pct,
        s.finishing_efficiency_player_pct,
        p.player_name,
        p.player_nationality,
        p.player_position,
        p.player_photo_url,
        s.team_sk,
        t.team_name,
        t.team_slug,
        t.team_logo_url
    from season as s
    left join players as p on s.player_sk = p.player_sk
    left join teams as t on s.team_sk = t.team_sk
),

ranked as (
    {% for board in boards %}
    select
        base.*,
        '{{ board.key }}' as metric_key,
        cast({{ board.key }} as float64) as sort_value,
        dense_rank() over (
            partition by league_code, season_api_year
            order by {{ board.key }} desc
        ) as board_rank,
        -- The TIE-BROKEN order within a league. `board_rank` above is a DENSE_RANK and stays one:
        -- ties SHARING a rank is a documented consumer contract here, and the top-10 cut is
        -- inclusive of them. But a consumer that must show ONE player per league cannot use it —
        -- measured against prod 2026-09-09, 12 of the 28 league-boards the Home block renders have
        -- more than one rank-1 player. Deciding which of them is shown is ranking, so it belongs
        -- here and not in the export (CPO 2026-09-09, escalations.log: "All ranking and ordering
        -- lives in the warehouse. The page renders the order it is served.").
        -- ⭐ FEWER MINUTES WINS (CPO, same day): the same tally in less time is the better
        -- performance, and that reads identically on every board — fewer minutes for the same
        -- passes or assists is also the better return. It settles 11 of those 12 ties.
        -- ⚠ `player_sk` last is MEANINGLESS AND SAID TO BE. It exists so the one tie that survives
        -- minutes has a stable answer; it makes no claim about the players. Player NAME was offered
        -- as the fallback and NOT taken, because a name correction would then reorder a board.
        -- ⚠ `nulls last` is load-bearing. BigQuery sorts NULLs FIRST ascending, so without it an
        -- unknown minutes total would beat every known one and win the tie. Prod currently has no
        -- NULL `minutes` among elite leaders; this is the guard for the general case, not the
        -- measured one.
        row_number() over (
            partition by league_code, season_api_year
            order by {{ board.key }} desc, minutes asc nulls last, player_sk asc
        ) as league_leader_order
    from base
    where {{ board.where }}
    {% if not loop.last %}
    union all
    {% endif %}
    {% endfor %}
),

-- THE ORDER OF THE LEAGUE LEADERS ON A BOARD, so a consumer showing one leader per league orders by
-- a single served column and compares nothing itself. `league_leader_order` above answers "who
-- represents this league"; this answers "in what order do those leaders appear".
-- CPO 2026-09-09 (escalations.log): "All ranking and ordering lives in the warehouse. The page
-- renders the order it is served." Same three ruled keys as the within-league order, for the same
-- reason — fewer minutes for the same tally is the better performance, and player_sk is a stable
-- last resort that means nothing (GitLab #112 is open to find a better one).
--
-- ⭐ PARTITIONED BY metric_key ALONE, AND THAT IS THE WHOLE POINT. An earlier attempt argued this
-- could not live here because the row order is scoped to a POOL of leagues (`competition_group`,
-- rotating nightly under #101) and the mart knows nothing about pools. That was wrong: the ruled
-- order is TOTAL, and restricting a total order to a subset preserves the relative order of what
-- survives. So ranking every league leader globally lets ANY pool filter inherit the right order
-- for free, and the pool never has to be known here.
-- ⚠ CONSEQUENCE, INTENDED AND VISIBLE: filtered to seven leagues the values come out SPARSE
-- (17, 18, 21, 31, 36, 40, 41 on the assists board). Sparse is the tell that this is a global
-- position. Contiguity is not something a consumer needs, and producing it would require knowing
-- the pool — the mistake above.
-- ⚠ NO SEASON in the partition, deliberately: `is_current_season` is per LEAGUE, so leagues shown
-- side by side can sit in different `season_api_year` values and partitioning by season would split
-- them.
-- ⚠ COMPUTED IN THE FINAL SELECT, NOT IN A CTE JOINED BACK. The obvious shape — rank the leaders in
-- their own CTE and left join — needs a USING or forty qualified column references, and SQLFluff
-- rejects the first (ST07) and demands the second (RF02). Sorting the leaders to the FRONT of the
-- window instead gives them positions 1..N in the ruled order with no join at all; the CASE then
-- keeps those and discards the numbers the non-leaders picked up.
select
    {{ dbt_utils.generate_surrogate_key(['player_sk', 'season_sk', 'metric_key']) }}
        as player_leaderboard_sk,
    metric_key,
    board_rank as rank,
    league_leader_order,
    sort_value,
    league_code,
    season_api_year,
    season_sk,
    league_sk,
    player_sk,
    player_name,
    player_nationality,
    player_position,
    player_photo_url,
    team_sk,
    team_name,
    team_slug,
    team_logo_url,
    appearances,
    minutes,
    goals_player,
    assists_player,
    shots_on_goal_player,
    dribbles_attempts_player,
    dribbles_success_player,
    passes_player,
    passes_key_player,
    duels_player,
    duels_won_player,
    tackles_player,
    interceptions_player,
    blocks_player,
    cards_yellow_player,
    cards_red_player,
    scorer_points_player,
    defensive_actions_player,
    cards_player,
    passes_accuracy_player_pct,
    duels_won_player_pct,
    dribbles_success_player_pct,
    saves_player_pct,
    finishing_efficiency_player_pct,
    -- WHICH SEASON a consumer should show, served as a fact rather than chosen downstream.
    -- The Home block shows one league's current-season leader; without this the export would have
    -- to pick a season itself, which is the window-selection shape analytics-engineer-reviewer
    -- FAILed twice under GAP-32. Same answer #846 reached for mart_player_profile's
    -- is_featured_season: serve the pick, let consumption filter on it.
    -- Latest season per LEAGUE, not per player: the flag answers "is this the season the site is
    -- currently showing for this competition", so every row of a league agrees. ST06 puts
    -- calculations after simple targets, hence its position last.
    rank() over (
        partition by league_code
        order by season_api_year desc
    ) = 1 as is_current_season,
    -- NULL on every row that is not a league leader: the position is only defined among leaders, and
    -- a number here would invite a consumer to order by a sequence the row is not part of.
    case
        when league_leader_order = 1 then row_number() over (
            partition by metric_key
            order by
                case when league_leader_order = 1 then 0 else 1 end,
                sort_value desc,
                minutes asc nulls last,
                player_sk asc
        )
    end as board_leader_order
from ranked
where board_rank <= 10
