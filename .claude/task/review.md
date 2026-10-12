# Review — feat/lineup-research-bl

diff_sha256: a357bcccef1fdc18bd0abae753584ea8260c0490d14eb61dc375595de29393d7

rounds: 1

## scope-auditor
VERDICT: PASS
risks_checked:
- Only the contract and the seed change, both in scope_paths; the seed hunk is additions only, so no Premier League row changes; nothing decides the next leagues, the older seasons or the garbled provider names, which stay reserved.
- The rules the rows follow are the batch-1 rules with their named approvals; the official pairing where the provider's differs and the squad-list id for a player the provider's sheet leaves out are applications of those rules, the seed replacing the provider's sheets with the official record and the ids staying the provider's.
- No new mechanism and no recurring cost; nothing in Appendix A applies.

## analytics-engineer-reviewer
VERDICT: PASS
risks_checked:
- All 1,318 new rows read: 33 matches, 11 distinct starters per sheet, no starter with a minute on, every substitute's replaced player on the same team with a matching minute off, offs equal to ons, one formation per team.
- The four named corrections (1388546, 1388621, 1388836, 1576194) are internally consistent; added time is stored as 90 plus extra, half-time substitutions as 46.
- Each note's stated fact matches its rows and is constant per match; every source is official, https and on bundesliga.com.
- The Premier League rows are unchanged; the base model, the schema and the tests are unchanged.

## escalations
(none)
