-- The three columns the Top teams block orders and filters on must mean what they say.
--
-- WHY IT EXISTS. `rank` is a DENSE_RANK, so joint leaders share it — measured against prod,
-- 2 of 259 league-board-seasons have more than one rank-1 team. Rare, but the block
-- claims one team per league, and a consumer that must pick cannot use `rank`. Deciding which team
-- represents a league, and in what order the representatives appear, is ranking, so it lives here:
-- all ranking and ordering lives in the warehouse, and the page renders the order it is served.
--
-- FOUR INVARIANTS. The first three mirror the player mart's; the fourth guards `is_current_season`,
-- which this mart did not have before and which stops the export choosing a season for itself.
-- ⚠ The adjacency check (3) is deliberately NOT a re-computation of the window. Re-running
-- `row_number()` inside the test with the same ORDER BY would pass for ANY ordering, because the
-- test would be using the one it is meant to check. It walks consecutive pairs with `lead()`
-- instead and asserts the later row is not strictly better on the ruled keys — "better" in the
-- direction the board serves as `rank_order`: a larger value on a most-first board, a smaller one
-- on a fewest-first board.
--
-- ⚠ THE TIE-BREAK IS `team_sk` AND IT IS MEANINGLESS. There is no sporting criterion for two teams
-- on an equal per-match rate — the player mart's fewer-minutes rule does not transfer, because for
-- a RATE fewer games means less evidence, not better performance (a better key is an open question).
-- The test still pins it, because an arbitrary key that is not STABLE would churn the committed
-- payload between exports.

{{ config(store_failures = true) }}

with import_mart_team_leaderboards as (
    select * from {{ ref('mart_team_leaderboards') }}
),

leaders as (
    select
        metric_key,
        rank_order,
        league_code,
        season_api_year,
        board_leader_order,
        sort_value,
        team_sk
    from import_mart_team_leaderboards
    where league_leader_order = 1
),

-- 1. Exactly one leader per league-board-season.
not_exactly_one_leader as (
    select
        league_code,
        season_api_year,
        metric_key
    from import_mart_team_leaderboards
    group by league_code, season_api_year, metric_key
    having countif(league_leader_order = 1) != 1
),

-- 2a. The board order is unique within a board.
duplicated_position as (
    select
        metric_key,
        board_leader_order
    from leaders
    group by metric_key, board_leader_order
    having count(*) > 1
),

-- 2b. It is defined on the leaders and on nothing else.
wrongly_defined as (
    select
        metric_key,
        league_code
    from import_mart_team_leaderboards
    where
        (league_leader_order = 1 and board_leader_order is null)
        or (league_leader_order != 1 and board_leader_order is not null)
),

-- 3. Consecutive leaders must not contradict the ruled order.
adjacent as (
    select
        metric_key,
        rank_order,
        board_leader_order,
        sort_value,
        team_sk,
        lead(sort_value) over w as next_value,
        lead(team_sk) over w as next_team_sk
    from leaders
    window w as (partition by metric_key order by board_leader_order)
),

out_of_order as (
    select
        metric_key,
        board_leader_order
    from adjacent
    where
        next_value is not null
        and (
            (rank_order = 'desc' and next_value > sort_value)
            or (rank_order = 'asc' and next_value < sort_value)
            or (next_value = sort_value and next_team_sk < team_sk)
        )
),

-- 4. `is_current_season` — CARDINALITY, RECENCY *and* ROW COMPLETENESS, all three.
--
-- ⛔ THIS STARTED AS A CARDINALITY-ONLY CHECK AND THAT WAS A REGRESSION, caught in review. The
-- player mart's sibling, `assert_one_current_season_per_league.sql`, already carries all three, and
-- its header records exactly why the first two were not enough. Repeating a guard the repo had
-- already strengthened, on the identical column in the mirror mart, is the weaker shape twice.
--   · CARDINALITY alone: flipping the window's ORDER BY to ascending flags the OLDEST season, still
--     exactly one per league, and the check stays GREEN. The block would show last season's leaders
--     under a heading that says season totals to date.
--   · CARDINALITY + RECENCY: reverting the model's `rank()` to `row_number()` flags exactly ONE ROW
--     per league. The distinct-season count is still 1 and that row's season is still the max, so
--     both halves stay GREEN while the flag is false on every other row of the season.
-- A flagged season must therefore be the LATEST and be flagged ENTIRELY.
per_season as (
    select
        league_code,
        season_api_year,
        countif(is_current_season) as flagged_rows,
        count(*) as season_rows
    from import_mart_team_leaderboards
    group by league_code, season_api_year
),

bad_current_season as (
    select league_code
    from per_season
    group by league_code
    having
        countif(flagged_rows > 0) != 1
        or max(case when flagged_rows > 0 then season_api_year end) != max(season_api_year)
        or countif(flagged_rows > 0 and flagged_rows != season_rows) > 0
)

select
    metric_key,
    cast(season_api_year as string) as detail,
    'not exactly one league leader' as failure
from not_exactly_one_leader

union all

select
    metric_key,
    cast(board_leader_order as string) as detail,
    'two leaders share a board position' as failure
from duplicated_position

union all

select
    metric_key,
    league_code as detail,
    'board_leader_order defined on the wrong rows' as failure
from wrongly_defined

union all

select
    metric_key,
    cast(board_leader_order as string) as detail,
    'consecutive leaders contradict the ruled order' as failure
from out_of_order

union all

select
    'n/a' as metric_key,
    league_code as detail,
    'not exactly one current season for the league' as failure
from bad_current_season
