# Review — feat/291-midfield-roles — 2026-11-14

diff_sha256: f016ee87a298e2df814f2b9c166ad8c45546c2afc5873975d8dad825a3d31caf

rounds: 3

## scope-auditor
VERDICT: PASS
risks_checked:
- Round 2: every changed file is inside scope_paths; the site_v2 paths and tests/test_midfield_roles.py are in scope and not in this commit.
- The diff decides nothing beyond decisions_taken: grid rule, substitute slots, checked team sheets only, no earlier-season fallback, the most-frequent, latest-match, code order, no pool minimum. A role-less player gets NULL and the role-coverage test fails on him instead of a guess.
- No new model, seed, schedule or dependency; the impact_map carries the pasted lineage, deploy order and the measured BL1 pool shift. Round 3 changed only a CTE alias in base_apif__lineups.

## analytics-engineer-reviewer
VERDICT: PASS
risks_checked:
- Round 1 findings closed: the catalogue-formula test's position_rows takes the season role from int_player_season__metrics; the season role and its test count confirmed or researched sheets only.
- Substitute-slot chain checked against the recursive recompute in the grid test; layer placement (grid rule in base, aggregate in intermediate, marts pass columns); no ref cycle; no hardcoded competition; the export only passes position_role.
- Round 3 delta: the new CTE is slot_substitutions, so no alias repeats in the model's single WITH; the compiled model dry-ran cleanly against the prod tables.

## platform-reviewer
VERDICT: PASS
risks_checked:
- Round 1 findings closed: the two index tests carry position_role; the new export test pins the column lists and both shaped payloads, so reverting any edit fails it.
- The grid test agrees with the model branch by branch and on substitution depth (four hops); the 17 known-formation rows match the rule; every singular test is severity error and read-only.
- The singular tests' joins cannot fan out (base grain unique per league, fixture, team and player; int_player_season__metrics one row per player and season). The peer files grow from one MID file per pool to up to DM, CM and AM.

## escalations
(none)
