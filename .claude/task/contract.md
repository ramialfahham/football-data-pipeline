# Task contract — end-of-session handover refresh (2026-06-27)

> Governance G2/G3 contract. Written on a clean tree BEFORE any edit.
> Artifact/handover task — `.claude/active_work.md` is NOT auto-editable, so it is named in scope_paths.

objective: >
  Rewrite `.claude/active_work.md` to current truth after this session: #500 PR-d step 6 (teardown)
  candidates 1 + 4 are BUILT and shipped as PR #590 (CI green, awaiting CPO merge). Record what #590
  changed, that step-6 candidates 3 + 5 are DEFERRED to the CPO (design call + domain-semantic), and
  that the remaining out-of-scope trigger-block rot (dead build_metric_glossary_json.py path + stale
  flat mart paths) is flagged for the CPO as background task_44698a18. Carry this session's lessons
  (the `cd && git commit` sole-command gotcha; the data-build/ui-checks CI skip on docs/workflow-only
  changes; the catalogue-vs-bindings trigger reasoning). Keep the governance machinery, the rest of
  the next-candidates list, and the do-NOTs intact.

refs: end-of-session handover; #590 OPEN (CI green, awaiting CPO merge); #500 PR-d step 6 candidates 3 + 5 deferred; trigger-block rot flagged as task_44698a18.

scope_paths:
  - .claude/active_work.md

decisions_taken: >
  Documentation only — no product/code/§10 decision. Records what shipped in #590 and re-points the
  handover at the remaining step-6 items (candidates 3 + 5) as CPO-directed choices, not pre-decided builds.

decisions_reserved:
  - None new. Step-6 candidate 3 (benchmark-macro seam) + candidate 5 (description enrichment) stay
    CPO-directed; the trigger-block-rot follow-up is CPO-scoped (flagged, not pre-decided).

done_when:
  - active_work.md leads with: PR-d step 6 candidates 1+4 SHIPPED as #590 (awaiting merge); candidates
    3+5 deferred; trigger-rot flagged (task_44698a18); the session lessons; governance machinery and
    do-NOTs intact.
  - Routes to scope-auditor only (active_work.md is in no routing path; the commit carries contract.md so
    it is NOT artifact-exempt — scope-auditor must run). CPO merges.

amendments: (none)
