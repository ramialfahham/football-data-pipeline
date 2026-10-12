# Review — feat/goals-on-match-mart

diff_sha256: 6f599492a91b4625a07c0d74dbb143f5bde69ea56a79bcd0cc93b9dd6f796aed

rounds: 4

rounds_cap_override: data:build:mr failed on one match whose provider team lists are swapped; the narrowed test and a fourth round approved in chat, 2026-10-11.

## scope-auditor
VERDICT: PASS
risks_checked:
- Every file is in scope_paths, the result-corrections seed and the two narrowed tests by recorded amendments; nothing reserved (#175, CAF 1619054, the mart renames) is touched; the swapped team lists of match 247587 are named as a separate item.
- The impact map pastes the 67-model lineage of both seeds and a blast radius with each changed number; the diff adds no model, hook, library or cadence.

## analytics-engineer-reviewer
VERDICT: PASS
risks_checked:
- The goal seed is applied in base like the other correction seeds and the mart stays one row per fixture; both narrowed tests still check every provider event and skip only the corrected goals.
- Tests ship with the change (the seed's grain and value tests, the extended corrections test, the new mart test); the 43 result rows keep the seed's invariants, a winner only on a 0-0 award.

## escalations
- question: Review rounds are capped at three; allow a fourth for the build failure on match 247587?
  CPO ANSWER: allowed; approved in chat, 2026-10-11.
