# Review — feat/lineup-research-apd

diff_sha256: d4a5969da23e5abdbe91c294388ab12264a75f7eb066ea3e0e1a6ae8b488648a

rounds: 2

## scope-auditor
VERDICT: PASS
risks_checked:
- Only the contract and the seed change, both in scope_paths; the seed hunk adds 1,185 rows and removes none.
- Nothing decides the next leagues, the previous season (#215) or the garbled provider names.
- The current-season order, Argentina as the batch and the widened id rule each carry their named approval; the provider's formations, positions and unused substitutes are a stated reading, as the official sheet shows none.
- Round 1 note: the extra-time break reading appeared only in the evidence; round 2 names it in decisions_taken as a reading of the half-time rule.
- No new mechanism and no recurring cost; nothing in Appendix A applies; no chat wording in the pushed files.

## analytics-engineer-reviewer
VERDICT: PASS
risks_checked:
- 572 starter rows, 11 distinct per team sheet in all 52, checked against the official sheets; no starter with a minute on; one formation per team.
- 241 substitutions, equal to the official lists: each replaced player on the same team with a matching minute off, each pair the official commentary's.
- Spot checks hold: Herrera's id in 1493176, Ramírez's in 1493169, the official pairing in 1493166, and the extra-time minutes of the three knockout matches.
- Round 1 note: three notes left out a minute change on a substitution whose outgoing player the provider lacked; round 2 counts it, and only the note column of those matches changed.
- Notes constant per match and true to their rows; every source https on ligaprofesional.ar; earlier rows, model, schema and tests unchanged.

## escalations
(none)
