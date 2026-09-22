-- Every team board is present in mart_team_leaderboards.
--
-- WHY THIS EXISTS ALONGSIDE accepted_values, rather than instead of it: the two catch OPPOSITE
-- failures. accepted_values asserts the observed metric_keys are a SUBSET of the declared list, so
-- it fails on an ADDED board and is blind to a REMOVED one — delete a key from the model's board
-- list and the observed set merely shrinks, still a subset, still green, and a page silently loses
-- a board. GAP-30 recorded that accepted_values on metric_key "is the only thing pinning the board
-- set"; the silent direction is the one that needs this test.
--
-- The board set is a product decision (twelve single-metric boards, the Rankings tab's). Changing
-- it means changing this number, the model's board list, the export's list and seeds'
-- accepted_values together — which is the point. A board whose metric the catalogue does not
-- define yields no rows (the model joins the seed for its direction) and lands here too.
--
-- Returns a row (= fails) when the count is anything other than 12.
{{ config(store_failures = true) }}

with observed as (
    select count(distinct metric_key) as board_count
    from {{ ref('mart_team_leaderboards') }}
)

select board_count
from observed
where board_count != 12
