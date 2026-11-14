# Review — feat/291-midfield-roles — 2026-11-14

diff_sha256: 1afe7faf267cf2ddfb0d732c4aa4a049afb185c25eed61ed5cb50ebef6d80155

rounds: 7

rounds_cap_override: the CPO approved, in chat on 14 Nov 2026, two more rounds for this branch (the one-file grid-test fix and the site commit after it), and then one more for the four warehouse changes. Round 6 is the site commit, which also carries the two-literal fix in the grid-fetch test. The CPO approved, in chat on 14 Nov 2026, round 7: the parsed team sheet in its own base table so base_apif__lineups plans inside BigQuery's limit, and the header wrap fix.

## scope-auditor
VERDICT: PASS
risks_checked:
- Round 2: every changed file is inside scope_paths; the site_v2 paths and tests/test_midfield_roles.py are in scope and not in this commit.
- The diff decides nothing beyond decisions_taken: grid rule, substitute slots, checked team sheets only, no earlier-season fallback, the most-frequent, latest-match, code order, no pool minimum. A role-less player gets NULL and the role-coverage test fails on him instead of a guess.
- No new model, seed, schedule or dependency; the impact_map carries the pasted lineage, deploy order and the measured BL1 pool shift. Round 3 changed only a CTE alias in base_apif__lineups.
- Round 4: the only change is the grid test, in scope; it brings no decision, mechanism or cost, and walks the same four substitutions as the model.
- Round 5: the stats-line midfielder, the earlier fetch's grid places and the other-seasons role each carry a dated CPO approval in decisions_taken and amendments; the starters of a sheet that failed only the substitutions or squad_lists checks now count, with the CPO's dated approval (each part of a sheet by its own checks); its bench and substitutions do not. The earlier fetch lends only grid places and formation, and the impact_map names the 132 sheets that reach. The position_role doc states the other-seasons source.
- Round 6: every site and test file is in scope_paths; the title and meta description keep the position group; decisions_taken names the comparison legend as the approved mock shows it, with its dated CPO approval; the grid-fetch test change touches no model.
- Round 7: base_apif__lineup_sheets.sql, base.yml, system.css and PlayerHeader.astro are in scope_paths; the amendment names the CPO's round approval and the coordinator's call for the split; the new table is an ordinary base model with no new rule, seed, schedule or dependency, and only base_apif__lineups reads it.

## analytics-engineer-reviewer
VERDICT: PASS
risks_checked:
- Round 1 findings closed: the catalogue-formula test's position_rows takes the season role from int_player_season__metrics; the season role and its test count confirmed or researched sheets only.
- Substitute-slot chain checked against the recursive recompute in the grid test; layer placement (grid rule in base, aggregate in intermediate, marts pass columns); no ref cycle; no hardcoded competition; the export only passes position_role.
- Round 3 delta: the new CTE is slot_substitutions, so no alias repeats in the model's single WITH; the compiled model dry-ran cleanly against the prod tables.
- Round 4 delta: no WITH RECURSIVE remains under dbt_project; the grid test walks four substitutions forward from the starter, the model four backward, and both give NULL to a broken chain; the test returned 0 rows against the MR's built fct_fixture_lineup.
- Round 5: the stats-line join is on the unique stats grain and starters only; the lending fetch is one row per team and lends starters' places by provider id and the formation by coalesce; the other-seasons tie-break (count, nearest season, earlier) matches its test; role_matches counts confirmed or researched sheets, and the starters of a sheet that failed only substitutions or squad_lists; fct_fixture_lineup passes failed_checks through, never NULL. Residual noted: a lender sheet with two id-less starters would break the base grain test loudly, never silently.
- Round 6: the grid-fetch test matches a lent place by shirt number, the same on the sheet row and the lender, so a paired or overridden id no longer drops out of the join; the other branches are unchanged. Residual noted: a starter with no shirt number, or two with one number, would show red, never hide a defect.
- Round 7: the new base table reads only staging, base and seeds; the one-pass fetch choice and lending keep the rule the fetch test recomputes; the role steps keep the line rule with a null guard; the pairs for the substitutions are the paired sheet rows. Measured on prod data: output equal to the base table except the lent grid places, formations and the role, and 0 role mismatches against the round-6 joins. Residuals noted: a person listed twice under one sheet id would duplicate a pair row, absorbed by the came_on and went_off dedup; lined is still read about nine times, so more readers could reach the planner limit again.

## platform-reviewer
VERDICT: PASS
risks_checked:
- Round 1 findings closed: the two index tests carry position_role; the new export test pins the column lists and both shaped payloads, so reverting any edit fails it.
- The grid test agrees with the model branch by branch and on substitution depth (four hops); the 17 known-formation rows match the rule; every singular test is severity error and read-only.
- The singular tests' joins cannot fan out (base grain unique per league, fixture, team and player; int_player_season__metrics one row per player and season). The peer files grow from one MID file per pool to up to DM, CM and AM.
- Round 4 delta: the hop CTEs share one column shape for the union; a player sits at one hop depth only, so slots cannot duplicate rows; the test still fails if the model's rule is reverted.
- Round 5: the fetch test recomputes from staging in three branches (read from the latest fetch, formation, a starter's lent place) and fails on a revert either way; the season-role test agrees with the model on the sheet filter and the other-seasons order. Residual noted: the fetch test keys on raw provider and staging team ids, so an overridden id could show red, never hide a defect.
- Round 6: no recursion, semicolons or apostrophe literals in the grid-fetch test; its union keeps five columns of matching types; reverting the lending or lending a wrong place still turns wrong_place red.
- Round 7: the new table's grain holds (one fetch per team, one offset per list) and carries its unique and not_null tests; no ref cycle; no script, test or build config changes; the design check counts a split only for a word broken inside one text node, and system.css has no net diff against main, so the Player and Team header counts return to their pins. Residual noted: a duplicated researched row would fail the build in the hop lookups, as it already breaks the grain test.

## bi-analyst-reviewer
VERDICT: PASS
risks_checked:
- Round 6: the header, the Players index row and the comparison legend show the role (DM, CM, AM in EN, DE, FI); squad groups and the position filter keep the four groups; the four explainers carry no player name; the FI legend reads through teamBeforeCompound.
- rendered_page_evidence.md measures the Player page at 260, 280, 320 and 375px in EN, DE and FI: body column, clipping, header wrap, separators, comparison rows and alignment; the DE and FI wraps agree with the header rule in system.css.
- Every field traces to the export and the marts; no metric, tier or order changed; title and meta description keep the position group.
- Round 7: the position item is a plain span, the club and the other items keep nowrap; every separator follows a no-break space, so none starts a line; re-measured at the four widths in three languages with no nowrap item split and the round-6 results unchanged.

## escalations
(none)
