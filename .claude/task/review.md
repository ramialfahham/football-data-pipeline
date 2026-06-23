# Review — feat/player-competition-benchmark — 2026-06-23

> Player competition benchmark PR2 (engine + mart + macro). Three additive dbt models +
> one macro; no existing model modified. Reviewed after addressing a first-round FAIL
> (added not_null guards on the engine distribution columns + mart vs_median_delta;
> corrected the contract done_when percentile range to [0,1] + junk-leg caveat; pasted
> the position_code coverage evidence into the impact_map).

diff_sha256: 1554427e90b02af649d44a8df119ed9c68610ac4a9ffd29c89de772a1e1954f1

## scope-auditor
VERDICT: PASS
risks_checked:
- Leaderboard↔benchmark finishing-floor coherence: the contract asserts "finishing% uses the same floor on both" (CPO coherence ruling). Verified this is by-design — both lenses apply the same SoT>=10 threshold at their own natural grain (leaderboard = whole-season totals, benchmark = in-position per-90); for single-position players they coincide, for multi-position they differ, which is the intended two-lens separation. Leaderboards correctly out of scope (not modified).
- Edge case — players with only junk position_codes ('-'/'SUB'/null) in a season produce no benchmark row (no assignable position). Verified the magnitude live: 8 of 69,926 whole-season qualifiers (0.01%) — negligible and correct by design. Also confirmed every §10 decision (B1/B2/B3, D1–D8) is recorded in escalations.log + contract decisions_taken (not builder-decided); the diff stays inside scope_paths; no existing model/number changed (additive); impact_map pastes real BQ coverage evidence rather than asserting it.

## analytics-engineer-reviewer
VERDICT: PASS
risks_checked:
- Same-window rule for the finishing_efficiency floor: `shots_on_target >= 10` is applied in byte-identical CASE expressions in both the engine distribution CTE and the mart ranking CTE, both sourcing `int_player_season_position__metrics` after the same `minutes >= 270` filter; the engine `peer_count` equals the mart ranked-N for the metric by construction. Traced both CTEs line-by-line — no window mismatch.
- Grain uniqueness under the multi-position split: `per_fixture` groups by `(player_sk, league_sk, season_sk, league_code, season_api_year, position_group)`, producing genuinely disjoint per-role aggregates; a two-position player gets two rows with separate stat sums, enforced by the mart unique_combination on `(player_sk, season_sk, position_group, metric_key)`. No fan-out double-count. Also verified: all 18 metric formulas mirror `int_player_season__metrics` atom-for-atom and match the catalogue; no catalogue change (A1 clear); no intermediate→mart ref; no hardcoded competition identifier; not_null coverage now present on the engine distribution columns + the mart vs_median_delta.

## escalations
(none)
