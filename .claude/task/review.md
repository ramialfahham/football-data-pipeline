# Review — feat/235-table-exact — 2026-10-30

diff_sha256: 0c98e81a307f8db45e9b6cf6c0f484447f35423c51e5d34fd83a29e10aced790

rounds: 6

rounds_cap_override: the first two MR data builds failed the published-table test on places; the fourth and fifth rounds review the fixes, approved in chat, 2026-10-29; the sixth reviews the Portuguese head-to-head condition the league's 2025-26 tables showed, approved in chat, 2026-10-30

## scope-auditor
VERDICT: PASS
risks_checked:
- Every staged path is in scope_paths; nothing credential-shaped.
- The changed head-to-head condition carries its approval in the contract and stays inside the same Liga Portugal rule version; no mechanism, dependency or recurring cost is added.
- The condition description, the SQL and the evidence (612 places of 2025-26, 70 kick-offs of 2026-27) agree.

## analytics-engineer-reviewer
VERDICT: PASS
risks_checked:
- is_met_equally is true exactly when every pair of level teams has met once or every pair twice, in both head-to-head passes; a mixed set cannot pass and a one-team group counts as met.
- The window sits on the same partitions as is_complete over non-null counts; nothing fans out, and no reader of the old flag remains.
- first_pass_keys and valued read the first pass for h2h_ criteria and the second for h2h2_ ones.

## platform-reviewer
VERDICT: PASS
risks_checked:
- The round touches no script, test, hook, CI job or dependency; the renamed flag has no orphan reference.
- The two window functions are stateless, so re-runs change nothing.
- The published-table test does not compare Portugal's in-season places of teams level on points, so the condition is proven by the recorded run against the league's tables, as all_h2h_met was before.

## football-analytics-expert-reviewer
VERDICT: PASS
risks_checked:
- The condition description says plainly that head-to-head counts once the level teams have all played each other equally often, every pair once or every pair twice, as the league's 2025-26 matchday 20 table shows.
- The same rule applies in both head-to-head passes.
- The condition column still holds only a condition.

## escalations
(none)
