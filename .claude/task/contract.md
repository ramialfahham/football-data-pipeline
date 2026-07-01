# Task contract — GAP-20 close-out: mark shipped + flip roster to wired + refresh handover

> Written on a CLEAN tree (branch docs/391-gap20-shipped-status off main @ ac261da).
> DOC-STATUS reconciliation only — records the already-merged fact that #619 wired mart_roster into
> the team export (GAP-20). No code/model change. Bookkeeping/status → skip plan mode (CPO 2026-06-30
> carve-out); show the diff inline → go → commit through the same contract+review+gate.
> See docs/working_agreement.md §2 (contract), §10 (decision rights).

objective: >
  Close out #391 GAP-20 now that #619 (per-season squad[] on the team payload) is MERGED. Three
  factual status updates: (1) mark GAP-20 "shipped" in docs/wireframes/99_gaps_register.md; (2) flip
  the Squad/roster block in docs/content_architecture.md §3 from "⚠ orphan" to "✓ wired" + update §7's
  mart_roster row + bump the queried-mart count 14→15; (3) refresh .claude/active_work.md (track A now
  FULLY GREEN — roster built AND wired; next = a CPO pick). All three record merged reality — no design
  decision, no product/UX/metric/naming call.

refs: >
  #619 (GAP-20 export wiring) MERGED, main @ ac261da: fetch_team_payloads now queries mart_roster and
  shape_team_payload attaches seasons[].squad[]. GAP-20 row = 99_gaps_register.md; roster status =
  content_architecture.md §3 (Listings row) + §7 (mart_roster row) + the §3 legend count. Precedent for
  a doc-status reconciliation PR = #615 (content_architecture §3/§7 reconciled to reality).

scope_paths:
  - docs/wireframes/99_gaps_register.md
  - docs/content_architecture.md
  - .claude/active_work.md
  - .claude/task/**

decisions_taken: >
  Doc-status reconciliation only. GAP-20 Ruling → "approved (CPO 2026-07-01); shipped 2026-07-01 (#619)".
  content_architecture §3 Squad/roster row → ✓ (wired #619); §7 mart_roster row → built + wired; the §3
  legend queried-mart count 14 → 15 (mart_roster now queried by the team export). Handover refreshed to
  post-#619 (track A fully green; GAP-20 closed; #619 in RECENT PRs; next = CPO pick). Records merged
  facts only — invents NO product/UX/metric/naming decision.

decisions_reserved:
  - The next track — a CPO pick (Stats-percentile screen spec / Career screen spec / Phase C / Phase D);
    present, do not auto-start.
  - The broader fold-generalization question (whether spec-sync folds into gap PRs) — still open, CPO call.
  - The two stale-wireframe flags + the wireframe §10 doc-status sweep — separate items, not touched here.

done_when:
  - GAP-20 marked shipped (99_gaps_register.md); content_architecture §3 roster ✓ + §7 + legend count
    updated; active_work.md refreshed to post-#619 (track A green, GAP-20 closed).
  - scope-auditor + bi-analyst-reviewer PASS (>=2 risks each); review.md diff_sha256 binds; CPO merges.

amendments: (none)
