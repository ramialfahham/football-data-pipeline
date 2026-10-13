# Review — feat/lineup-research-mls-2

diff_sha256: 182a55b686965dbf71998a1de084bb79042a57aa25d51441ba632a66c25c5c47

rounds: 1

## scope-auditor
VERDICT: PASS
risks_checked:
- Only the contract and the seed change, both in scope_paths; the seed hunk adds rows only, so no earlier row changes.
- Nothing decides the next leagues, the older seasons or the garbled provider names, which stay reserved; the rows are MLS 2025 and 2026 only.
- MLS as the batch, the provider's formations and pitch positions, and Austin-LAFC left out each carry their named approval; the carried-over batch-1 and batch-2 rules are restated with theirs.
- No new mechanism and no recurring cost; nothing in Appendix A applies; no chat wording in the pushed files.

## analytics-engineer-reviewer
VERDICT: PASS
risks_checked:
- All 64 matches read: two teams with 11 distinct starters each, no starter with a minute on, every substitute's replaced player on the same team with a matching minute off, offs equal to ons.
- One formation per team; the four teams without one are the four the provider holds none for, which the schema allows.
- Sources are https on mlssoccer.com and change only at match boundaries; the notes of the playoff, Klauss, Vancouver-LAFC and D.C. United-Philadelphia matches are true to their rows and to the official data.
- Spot checks against the official data hold, including the swapped playoff match 1482413 and Klauss's id at LA Galaxy; substitutions the official data gives no minute keep the provider's.
- The earlier rows, the base model, the schema and the tests are unchanged.

## escalations
(none)
