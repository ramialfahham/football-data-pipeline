# Review — feat/260-player-bio

diff_sha256: 6c335323a3dd2edddf7baac26d030fc60f4b402b88ca29fe22adf0777e631604

rounds: 2

## scope-auditor
VERDICT: PASS
risks_checked:
- Every path in the patch is in scope_paths, assert_base_player_stats_cleaned.sql included; contract.md is the only changed file outside dbt_project and site_v2.
- player_id_overrides holds exactly 8 rows and its description matches the approved text word for word.
- The reserved decisions stay undecided: name form and country spellings. The nationality rows are per-player corrections, not a spelling rule.
- New mechanisms, the two seeds and three singular tests, are declared. No recurring cost, ingestion change, extra run or new library.
- No secret, no host address, no chat words, no decision history in repo files.
- 211.json changes three birth dates to null, players 164707, 164877 and 164880, matching the acceptance criterion.

## analytics-engineer-reviewer
VERDICT: PASS
risks_checked:
- Round 1 failed on three points: assert_base_player_stats_cleaned compared raw ids to merged ids, the profile tie order was not total, and the merged test could not see two ids in one fetch. All three are fixed.
- Every place a player id enters base goes through player_id_override; the 8 wrong ids remain only in player_id_overrides.csv.
- The tests comparing seeds to base use kept ids and do not break; no model's grain gains a duplicate.
- The tie orders in base_apif__players and base_apif__player_profiles are total on their output columns.
- assert_player_birth_date_possible cannot fail on a date the macro kept, and still catches the 2026 placeholders.
- An empty correction clears the field in both base models.
- Three proposals rejected with measurements, each accepted: staging holds every fetch, so a row count would fail on correct data; base cleans stats, so a raw sum would too, and the check is matches, not summed stat values; the 8 wrong ids hold no transfer rows.

## bi-analyst-reviewer
VERDICT: PASS
risks_checked:
- The three changed rows, 164707, 164877 and 164880, read null with every other field intact and the same keys as their neighbours.
- No under-13 birth date remains in the file.
- TeamSquad.astro leaves the age out on a null date, as wireframe 11 says; it is the only reader of birth_date.
- The export passes player_birth_date straight through, so the sample matches what it would produce.
- The three rows sit in the 2017/18 block, which no page renders, so criterion 1 holds trivially for them; the featured squad already renders null-date members without an age.
- No new label, wording or number on a display surface.
