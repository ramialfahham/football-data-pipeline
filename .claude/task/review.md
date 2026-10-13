# Review — feat/lineup-research-elite

diff_sha256: 40e32f13f8c408ef35b7277bd69d3e8cc692134c142751ff639dfaa3d3cdf12c

rounds: 1

## scope-auditor
VERDICT: PASS
risks_checked:
- Only the contract and the seed change, both in scope_paths; the seed hunk adds 1,056 rows and removes none.
- Nothing decides the competitions parked in #216, the previous season (#215) or the garbled provider names; the rows are elite-pool and World Cup matches of the current season.
- The elite pool and World Cup selection and the formation rule carry their named approvals; the minute readings are stated readings of approved rules.
- No new mechanism and no recurring cost; nothing in Appendix A applies; no chat wording in the pushed files.

## analytics-engineer-reviewer
VERDICT: PASS
risks_checked:
- 23 matches, 46 team sheets with 11 distinct starters each; no repeated player id within a match.
- Every substitution's replaced player is on the same team with a matching minute off; offs equal ons; the chains of substitutes replaced later hold.
- Formations equal the provider's everywhere but New Zealand and Czechia, which take FIFA's where the provider has none.
- Sources are https on each competition's own site; notes are constant per match and true to their rows.
- Spot checks against the official data hold in every competition, including the two Ndiayes of Le Havre, Koum as E. Mbondo, Jemide's id and the half-time substitutions without an official minute.
- The earlier rows, the model, the schema and the tests are unchanged.

## escalations
(none)
