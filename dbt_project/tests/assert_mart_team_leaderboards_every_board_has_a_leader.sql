-- Every board has a rank 1 in every league-season it appears in.
--
-- This pins the CPO's 2026-08-18 ruling — "one team per league, same as players" — which the model
-- implements as `partition by league_code, season_api_year, metric_key`. Under that partition a
-- DENSE_RANK always starts at 1 in every group, so the property holds BY CONSTRUCTION and this test
-- asserts the construction. The block reads each league's rank-1 team; a board with no leader in a
-- league is a board that silently drops that league.
--
-- ⭐ WHY IT EXISTS: dropping metric_key from the partition — which ranks all four boards against
-- each other, and is the exact way that ruling gets violated — is caught by NOTHING else here.
-- Measured on live prod data, healthy vs mutated:
--
--     unique_combination_of_columns   0 duplicate rows   0 duplicate rows    SURVIVES
--     ..._all_boards_present          4 boards           4 boards            SURVIVES
--     rank between 1 and 10           in range           in range            SURVIVES
--     this test                       0 of 865 groups    34 of 266 groups    FAILS
--
-- The grain stays unique because each team-season-board still appears at most once: the RANK is
-- wrong, not duplicated. All four boards still appear because leagues with no team-stat coverage
-- have no passes_per_match rows and let the smaller-valued boards through. Only 2,297 of 9,438 rows
-- survive the top-10 cut, and nothing asserts a row count.
--
-- Returns a row (= fails) for every board with no leader in a league-season.
with per_board as (
    select
        league_code,
        season_api_year,
        metric_key,
        min(rank) as best_rank
    from {{ ref('mart_team_leaderboards') }}
    group by league_code, season_api_year, metric_key
)

select
    league_code,
    season_api_year,
    metric_key,
    best_rank
from per_board
where best_rank != 1
