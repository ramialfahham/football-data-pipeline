# Task contract — end-of-session handover refresh (2026-06-26 EOD)

> Governance G2/G3 contract. Written on a clean tree BEFORE any edit.
> Artifact/handover task — `.claude/active_work.md` is NOT auto-editable, so it is named in scope_paths.

objective: >
  Rewrite `.claude/active_work.md` to current truth: #500 PR-d (the live-MVP → metric_catalogue SSoT
  migration) is DONE bar step 6 — #582/#583/#584/#585/#587 all MERGED. Capture the live metric chain
  post-migration, the remaining step-6 teardown (to be scoped), this session's hard-won lessons (local
  dbt-validation gaps + the dbt MCP parse seam + the two ci-data-build failures + the "mechanical"
  mis-framing + the amend-a-pushed-PR dance), the governance machinery, the next candidates, and the
  do-NOTs (incl. the CPO's plain-language communication feedback).

refs: end-of-session handover; #582+#583+#584+#585+#587 merged; #500 PR-d step 6 (teardown) the only remaining unit.

scope_paths:
  - .claude/active_work.md

decisions_taken: >
  Documentation only — no product/code/§10 decision. Records what merged and re-points the handover at
  step 6 (teardown) as a CPO-directed choice, not a pre-decided build.

decisions_reserved:
  - None new. Step 6 teardown is CPO-directed + needs scoping; not pre-decided here.

done_when:
  - active_work.md leads with: PR-d steps 1-5 MERGED (#582-#585 + #587); step 6 (teardown) the only remaining
    unit; the live metric chain; the session lessons; the governance machinery; the do-NOTs; next candidates.
  - Routes to scope-auditor only (active_work.md is in no routing path; the commit carries contract.md so it is
    NOT artifact-exempt — scope-auditor must run). CPO merges.

amendments: (none)
