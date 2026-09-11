-- league_leader_order must be a TOTAL order within a league-board, and its 1 must be the right row.
--
-- WHY IT EXISTS. `rank` is a DENSE_RANK, so joint leaders share it — measured against prod,
-- 12 of the 28 league-boards the Home page renders had more than one rank-1 player, and
-- one board returned 24 rank-1 rows across 7 leagues. A consumer showing ONE player per league
-- cannot use `rank`, which is why `league_leader_order` exists: all ranking and ordering lives in
-- the warehouse, and the page renders the order it is served.
--
-- TWO INVARIANTS, and the second is the one that would rot silently. The first — exactly one row
-- per league-board carries 1 — is structural and a broken window function would break it loudly.
-- The second — that the row carrying 1 is the one the RULE picks — is what a wrong ORDER BY breaks
-- while leaving the count perfectly correct. Dropping the `minutes` leg still yields exactly one
-- leader per league-board; it is just the wrong player. So the count alone would be a test that
-- cannot fail for the reason the column was written.
--
-- ⚠ NOT scoped to the elite group or the current season, unlike
-- assert_mart_leaderboards_every_home_board_has_a_leader. That test asks whether the Home block has
-- something to show, which is a question about the pool it renders. This one asks whether a column
-- means what it says, which is true of every row or the column is broken.

with import_mart_leaderboards as (
    select * from {{ ref('mart_leaderboards') }}
),

-- 1. The order is total: one and only one leader per league-board.
not_exactly_one_leader as (
    select
        league_code,
        season_api_year,
        metric_key,
        countif(league_leader_order = 1) as leaders
    from import_mart_leaderboards
    group by league_code, season_api_year, metric_key
    having leaders != 1
),

-- 2. The leader is the row the RULE picks: best value, then fewest minutes.
--    `min(minutes)` is taken only among the rows that share the league-board's best value, because
--    a lower-scoring player with fewer minutes must NOT win — minutes break a tie, they do not
--    outrank the metric. Nulls are excluded from the comparison the same way `nulls last` excludes
--    them from winning one.
leaders as (
    select
        league_code,
        season_api_year,
        metric_key,
        sort_value,
        minutes
    from import_mart_leaderboards
    where league_leader_order = 1
),

best as (
    select
        l.league_code,
        l.season_api_year,
        l.metric_key,
        max(m.sort_value) as best_value,
        min(if(m.sort_value = l.sort_value, m.minutes, null)) as fewest_minutes_at_best
    from leaders as l
    inner join import_mart_leaderboards as m
        on
            l.league_code = m.league_code
            and l.season_api_year = m.season_api_year
            and l.metric_key = m.metric_key
    group by l.league_code, l.season_api_year, l.metric_key
),

wrong_leader as (
    select
        leaders.league_code,
        leaders.season_api_year,
        leaders.metric_key
    from leaders
    inner join best
        on
            leaders.league_code = best.league_code
            and leaders.season_api_year = best.season_api_year
            and leaders.metric_key = best.metric_key
    where
        leaders.sort_value != best.best_value
        or (leaders.minutes is not null and leaders.minutes != best.fewest_minutes_at_best)
        -- ⚠ THE NULLS-FIRST REGRESSION, which the two clauses above cannot see. Both are gated on
        -- the leader's own minutes being known, so flipping the model's `nulls last` to `nulls
        -- first` would hand the league to a player with UNKNOWN minutes and neither would fire.
        -- This clause is the one that catches it: the leader has no minutes while a player tied
        -- with it on the same best value does. `min()` ignores nulls, so `fewest_minutes_at_best`
        -- is null only when NO tied row has minutes — in which case there is nothing to compare and
        -- this correctly stays silent.
        or (leaders.minutes is null and best.fewest_minutes_at_best is not null)
)

select
    league_code,
    season_api_year,
    metric_key,
    'not exactly one leader' as failure
from not_exactly_one_leader

union all

select
    league_code,
    season_api_year,
    metric_key,
    'leader is not the ruled pick' as failure
from wrong_leader
