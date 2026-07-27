# Task contract — handover: player-page mock drift correction (bookkeeping)

> Written on a CLEAN tree, branch `docs/handover-player-page-drift` off `main` (`95c0dd1`).
> Bookkeeping only — no code, no model, no product decision made here.

objective: >
  Record the CPO's correction on the player-page mock ("badly drifting": redundancy, content/
  design-language inconsistency across the 3 tabs, no decided per-tab content boundary) into
  .claude/active_work.md, alongside the corrected process (decide per-tab boundaries in writing
  first, build tabs one at a time). Memory (feedback_design_off_the_cuff.md,
  project_player_page_design.md, MEMORY.md) and issue #753 already carry this same correction,
  written this same session.

refs: >
  This session, 2026-07-27, continuing directly from PR #836 (merged). CPO: "the player mockup
  hasn't been approved yet. You were badly drifting with your proposals" then, on being asked what
  specifically: "redundancy, inconsistency (content, design language), lack of clarity what to show
  where. we have to go through each tab one by one." Confirmed against the mock: Save percentage
  and Pass accuracy each appeared verbatim in both Overview and Performance tabs with no stated
  reason.

scope_paths:
  - .claude/active_work.md

decisions_taken: >
  Pure bookkeeping. No new product/metric/mechanism decision. Records a CPO correction and its
  process fix; does not decide any content question.

decisions_reserved:
  - Both player-page content questions remain open pending an actual approved mock. The corrected
    process (tab-by-tab, written content boundaries) is itself a process fix, not a content
    decision.

done_when:
  - active_work.md's "⭐ CURRENT" section records the drift correction precisely (redundancy
    example, inconsistency, the tab-by-tab process fix) without softening or overstating it.
  - ONE commit; artifact-exempt (active_work.md only); pushed with an explicit refspec; PR opened.

amendments: (none)
