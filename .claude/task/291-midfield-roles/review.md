# Review — feat/291-midfield-roles — 2026-11-14

diff_sha256: 2b2fbea8d8df867657a72a2c34f09981b86bb7e1465723a4f9a78581749f259a

rounds: 4

rounds_cap_override: the CPO approved two more rounds for this branch in chat on 14 Nov 2026, the one-file grid-test fix and the site commit after it.

## scope-auditor
VERDICT: PASS
risks_checked:
- Round 2: every changed file is inside scope_paths; the site_v2 paths and tests/test_midfield_roles.py are in scope and not in this commit.
- The diff decides nothing beyond decisions_taken: grid rule, substitute slots, checked team sheets only, no earlier-season fallback, the most-frequent, latest-match, code order, no pool minimum. A role-less player gets NULL and the role-coverage test fails on him instead of a guess.
- No new model, seed, schedule or dependency; the impact_map carries the pasted lineage, deploy order and the measured BL1 pool shift. Round 3 changed only a CTE alias in base_apif__lineups.
- Round 4: the only change is the grid test, in scope; it brings no decision, mechanism or cost, and walks the same four substitutions as the model.

## analytics-engineer-reviewer
VERDICT: PASS
risks_checked:
- Round 1 findings closed: the catalogue-formula test's position_rows takes the season role from int_player_season__metrics; the season role and its test count confirmed or researched sheets only.
- Substitute-slot chain checked against the recursive recompute in the grid test; layer placement (grid rule in base, aggregate in intermediate, marts pass columns); no ref cycle; no hardcoded competition; the export only passes position_role.
- Round 3 delta: the new CTE is slot_substitutions, so no alias repeats in the model's single WITH; the compiled model dry-ran cleanly against the prod tables.
- Round 4 delta: no WITH RECURSIVE remains under dbt_project; the grid test walks four substitutions forward from the starter, the model four backward, and both give NULL to a broken chain; the test returned 0 rows against the MR's built fct_fixture_lineup.

## platform-reviewer
VERDICT: PASS
risks_checked:
- Round 1 findings closed: the two index tests carry position_role; the new export test pins the column lists and both shaped payloads, so reverting any edit fails it.
- The grid test agrees with the model branch by branch and on substitution depth (four hops); the 17 known-formation rows match the rule; every singular test is severity error and read-only.
- The singular tests' joins cannot fan out (base grain unique per league, fixture, team and player; int_player_season__metrics one row per player and season). The peer files grow from one MID file per pool to up to DM, CM and AM.
- Round 4 delta: the hop CTEs share one column shape for the union; a player sits at one hop depth only, so slots cannot duplicate rows; the test still fails if the model's rule is reverted.

## escalations
(none)
