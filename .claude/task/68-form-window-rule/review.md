# Review — claude/68-form-window-rule-2b0f15 — 2026-11-16

diff_sha256: 0255e9097fb3f978354112e6e90e501862c9d607b66e1bfd2766d8ebddbdfa4e

rounds: 3

## scope-auditor
VERDICT: PASS
risks_checked:
- Every changed file is in scope_paths; the test file enters through the recorded amendment.
- The section 4 qualifying cell is the only rule edit; its authority is the national-context ruling in 4a1a348d, and the in-file section 8.4 matrix states the same rule.
- No new metric, label, mechanism or cost; the model SQL is unchanged, so no shipped number moves.
- The impact_map pastes the dbt ls lineage and states the comment-only blast radius; approved_design none is honest, no site_v2 or export change.
- The changed comments and the new cell state the current state only.
- Round 3: the second amendment adds the pin file under the pin-only-goes-down rule; no new mechanism or cost.

## analytics-engineer-reviewer
VERDICT: PASS
risks_checked:
- Round 1 FAIL: the form-window test still excluded a qualifying side whose campaign is under way, and its header named the old cell. Round 2: both exclusions and the header sentence are gone.
- The test's last_5 branch builds the same set as int_team_momentum_window for a qualifying side: national legs, no season cap, at most 5 by recency.
- The side_kinds join still keeps team-window rows (NULL upcoming_fixture_sk) and match-window rows (played fixtures) out of the comparison.
- The changed model comments match the code: no row without a finished match in the window; mart_team_season_record serves the pre-season domestic-league window.
- No ref, column, grain, materialisation, seed or catalogue change; no hardcoded league_code.
- Round 3: the pin change accounts for exactly the three issue references the comments lost; both models keep a flagged line, so PINNED_FILES stays 93.

## platform-reviewer
VERDICT: PASS
risks_checked:
- PINNED_LINES 273 to 270, PINNED_FILES 93 unchanged: the three removed comment lines are the whole difference, and the test's two-way check still fails if a reference returns or the pin is left high.
- The replacement comment text adds no flagged line; no hook, workflow, CI, requirements or build-config file changes.

## escalations
(none)
