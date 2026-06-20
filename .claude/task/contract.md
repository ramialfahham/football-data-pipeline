# Task contract — chore: refresh the handover after the PL backfill + season-depth refactor

> Bookkeeping. Update .claude/active_work.md so a fresh session continues correctly: record this
> session's work — #414 closed as obsolete (premise-check), the PL deep-season backfill (PL now
> 2016-2026 = BL1 parity, ~3k calls total), and the season-depth config refactor merged as #520
> (history_seasons authoritative; V1_SEASON_WINDOW_YEARS -> DEFAULT_SEASON_WINDOW_YEARS), plus the
> filed #521 (phantom-current-season hardening, deferred). Re-point FIRST/NEXT. Preserve all durable
> standing sections verbatim. No code. active_work.md is artifact-only for commits but NOT
> auto-editable, so it is in scope_paths; the commit also carries contract.md (never review-exempt)
> -> scope-auditor reviews.

objective: >
  Update the session-specific parts of .claude/active_work.md: the Last-updated header, FIRST, the
  This-session section (replace the 2026-06-19 idle-mode fix with the 2026-06-20 session: #414 closed
  obsolete; the PL backfill — fixtures snapshot restored + 2016 fetched to reach BL1 parity 2016-2025
  finished; the #520 config refactor making history_seasons authoritative + retiring the v1 constant;
  the key cost lesson that PL was cheap because details pre-existed but PD/SA/L1 are NOT pre-existing
  (~12k each); #521 filed), and the NEXT pointer. Carry ALL durable standing sections (Standing
  authority, Product roadmap, the other NEXT items + Carryovers, dim_team, governance, form-window
  vocab, parked, pending CPO actions, Do-NOT, Environment) forward UNCHANGED + verbatim.

refs: >
  This conversation 2026-06-20. Closed #414 (obsolete — premise-check). Backfilled PL to 2016-2026
  (BL1 parity). Merged #520 (season-depth config refactor: history_seasons authoritative,
  V1_SEASON_WINDOW_YEARS -> DEFAULT_SEASON_WINDOW_YEARS). Filed #521 (phantom-season hardening).
  Memory: [[feedback-raw-staging-latest-payload]], [[no-hacky-solutions]].

scope_paths:
  - .claude/active_work.md
  - .claude/task/contract.md
  - .claude/task/review.md

decisions_taken: >
  CPO directed each step this conversation: closed #414 (Path A), approved the PL backfill (Phase 1),
  approved Path A (config refactor), merged #520. Pure bookkeeping: records already-merged/already-done
  work and re-points NEXT. No new product/metric/naming/layer decision — the refactor's design choices
  (history_seasons authoritative; the rename; PL hs=11; phantom-season deferral) are shipped + recorded,
  not re-decided. Durable standing sections preserved verbatim.

decisions_reserved:
  - No new scope. NEXT items remain CPO-directed; this is not the place to add or re-decide them.
  - If anything beyond active_work.md needs editing, STOP — that is not bookkeeping.

done_when:
  - .claude/active_work.md reflects: #414 closed obsolete; PL backfilled to 2016-2026 (BL1 parity, ~3k
    calls); #520 merged (history_seasons authoritative + v1 constant retired); the PD/SA/L1 cost lesson
    (~12k each, details not pre-existing); #521 filed; FIRST/NEXT re-pointed; all durable sections
    intact + verbatim.
  - Commit on branch chore/handover-pl-backfill; post-commit opens the PR.
  - reviewer: scope-auditor PASS (>=2 named risks); no FAIL; no ESCALATE.

amendments: (none)
