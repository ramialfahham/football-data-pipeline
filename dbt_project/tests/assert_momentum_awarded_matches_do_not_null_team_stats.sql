-- The same rule as assert_awarded_matches_do_not_null_team_stats, for the FORM WINDOW.
--
-- Two surfaces compute team stat rates from the same legs: the season record and the last-5 momentum
-- window. Both gate all-or-nothing on stat coverage, so both had to move off `games_played` /
-- `games_in_window` and onto `games_expecting_team_stats` when awarded matches began to count. A test
-- on one surface only would let a reversion of the other's 10 gates through — and the two would then
-- disagree about the same match, which is the failure this pairing exists to prevent.
--
-- ⚠ NO CURRENT WINDOW EXERCISES THIS. Measured when written: 0 of 9,784 windows contain an awarded
-- match, because the window is a team's last five matches and no awarded fixture is that recent
-- anywhere. So this test is GREEN TODAY FOR A REASON THAT HAS NOTHING TO DO WITH THE GATE, and it
-- would stay green under a reverted gate until an awarded match happens to fall inside a window.
-- That is stated rather than hidden: the guarantee for this surface comes from the synthetic
-- mutation recorded in the acceptance evidence (a forced awarded-with-no-stats leg in every window;
-- 177 windows keep their rates that would otherwise be nulled), and this test is the standing guard
-- for when real data finally reaches it.
--
-- `games_expecting_team_stats` is projected out of mart_team_momentum for this test. Without it
-- nothing on this surface can tell a correct gate from one reverted to games_in_window.

with momentum as (
    select * from {{ ref('mart_team_momentum') }}
)

select
    upcoming_fixture_sk,
    team_sk,
    window_type,
    games_in_window,
    games_expecting_team_stats,
    games_with_team_stats,
    shots_per_match
from momentum
where
    games_expecting_team_stats > 0
    and games_with_team_stats >= games_expecting_team_stats
    and shots_per_match is null
