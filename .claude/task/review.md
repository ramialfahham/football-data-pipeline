# Review — fix/264-narrow-table-name-first

diff_sha256: 17ac5282be947637c939e243b832a723076a6b8be2099210c0f7079752dcbc66

rounds: 1

## scope-auditor
VERDICT: PASS
risks_checked:
- The diff is `system.css` and the contract, both in scope_paths; no locked file, no registry rule change, no §10 decision class touched.
- Two CSS rules matching the registry's Table narrow row; no new class, token, mechanism, metric, label or cost.
- Impact map names the two name-first tables and the approved design covering the Team page.

## bi-analyst-reviewer
VERDICT: PASS
risks_checked:
- Specificity: both `.tm:first-child` rules outrank the rule they override and the pinned nth-child placements, so they fire.
- Rank tables (Standings, RankingBoard, DeservedTable) open with `.rk` and are not matched; the evidence's 36 Bundesliga rows stay in column 2.
- Name-first tables are exactly TeamLastSeason and TeamDeserved; numbers keep their columns under their heads; no field, label or number added.
- Rendered evidence: names move from 79px to 0px at 280px in DE and FI, 0px at every listed width and language.

## escalations
(none)
