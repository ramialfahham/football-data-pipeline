# Review - claude/262-staging-duplicate-keys

diff_sha256: 43e57ba7069ecc3f182de1b31681f701dc7001c293b51a8091801b99b947ee09

rounds: 3

## scope-auditor
VERDICT: PASS
risks_checked:
- Round 1 passed on the first design; round 2 passed; round 3 passed after the coordinating session ruled that a tie is found on the team after fixture_team_id_overrides.
- Every changed path is in scope_paths: the macro, base_apif__lineup_fetches, base_apif__lineup_fetch_ties, base_apif__lineup_sheets, base_apif__fixture_players, the mart branch, the three dbt tests, the two pin tests, the cleaning_rules sentence and the skill line.
- The row-kind name, the seed value none, the per-team withhold and the cleaning_rules sentence are named in decisions_taken with the coordinating session's ruling; the base unique tests stay at error and the staging test goes under that ruling.
- No decision history in repo files; the cleaning_rules sentence has one home and fits the sentence limit.

## analytics-engineer-reviewer
VERDICT: PASS
risks_checked:
- Round 1 FAIL: a tie among older fetches could change the grid lender, and a tie existing only after the team-id correction was neither found nor failed. Round 2 PASS with the wider residual noted. Round 3: the tie is found on the corrected team through base_apif__lineup_fetches, and the lender lends nothing when its candidates differ.
- Read-only simulations on prod data: the refactored lineup_sheets equals the prod table (2,345,391 rows, 0 only in either side); latest_sheets old and new read (115,700 rows each, 0 differences); a differing duplicate removes only that team's rows; an alias duplicate under the wrong provider id collapses when identical and is withheld when it differs.
- Downstream of one withheld team: base_apif__lineups marks a one-sheet match not_available (check two_sheets), every fact reads confirmed or researched only, and no singular test can fail on a team left out.
- Known notes, not defects: a researched match with a differing tie is still listed; the contract's lender wording speaks of the fetches tied at the lender's ingest time while the code looks at the lender candidates; an older tie in an aliased team's other provider id can pick arbitrarily in the ownerless-card check of base_apif__fixture_players.

## platform-reviewer
VERDICT: PASS
risks_checked:
- Round 1 FAIL: the items pin of the research list no longer anchored the player_team_withheld tail. Round 2 FAIL: yml descriptions over 25 words, and the staging-test removal pinned by name only. Round 3: sentences split, the staging block pinned to carry no tests key, the row 4a of the answer key pinned.
- 48 pin mutants (macro, fetches correction joins and filters, ties keys and ignores, lineup_sheets and fixture_players joins, sources and provider id, mart, yml, staging test restored unnamed, base proof lowered, proof test, answer key, cleaning_rules sentence, skill) and 4 of 4 hand mutants of the answer key on BigQuery are caught.
- ci_local --mr: lint, test:python (full suite), data:build:mr (lint and parse) and secrets pass; governance fails only before this file exists.
- Residual weakness, not a defect: the three correction joins of base_apif__lineup_fetches are pinned by their conditions, not by the join keyword.

## escalations
(none)
