# Task contract — handover: player-page design conversation blocked (bookkeeping)

> Written on a CLEAN tree, branch `docs/handover-player-page-blocked` off `main` (`725f2ab`).
> Bookkeeping only — no code, no model, no product decision made here.

objective: >
  Rewrite .claude/active_work.md so a fresh chat continues the player-page design conversation
  with zero re-investigation and zero risk of overstating progress. Current true state: two
  content questions (GK stat order, YoY-after-transfer wording) have strong, sourced
  recommendations (consultant-reviewed, real-data-grounded) but are NOT CPO-approved — the mock
  built to show them has failed to render for the CPO twice via the Artifact/SendUserFile path,
  root cause undiagnosed. The CPO explicitly asked for a handover ensuring no amnesia; this
  captures the corrected 3-tab structure, both recommendations with their reasoning, and the
  unresolved rendering blocker, distinctly from "decided."

refs: >
  This session, 2026-07-27. Issue #753 (player page) comment posted with the same content this
  handover records. Corrected tab structure sourced from memory (feedback_v2_design_schema_first.md,
  2026-07-20 CPO-approved mock 6c21ef71) + docs/wireframes/12_player_stats.md +
  docs/wireframes/13_player_career.md + site_v2/src/components/team/Tabs.astro (the shipped
  mechanism mirrored). CPO corrections this session: "This is the player page??" (the first mock
  was a decision fragment, not a real page) and "the player page doesn't look like the mockup we
  have been working on. It had at least 2 tabs (if not 3). Things are going south again" (missed
  the Performance/Career tabs entirely). CPO's final instruction: "we need to continue in a new
  chat. Prepare a handover and ensure that you don't have amnesia."

scope_paths:
  - .claude/active_work.md

decisions_taken: >
  Pure bookkeeping. No new product/metric/mechanism decision. The two content-question
  recommendations are recorded as RECOMMENDATIONS, explicitly not approved — the contract itself
  makes no claim they are settled.

decisions_reserved:
  - Both player-page content questions (GK stat order promotion, YoY transfer wording) remain
    open pending the CPO actually seeing a working mock — recorded as pending, not decided here.
  - Root cause of the Artifact/SendUserFile rendering failure is undiagnosed — not decided/fixed
    here; flagged as the literal next blocking step.

done_when:
  - active_work.md leads with the blocked state (not "in progress" understated, not "done"
    overstated), carries the corrected 3-tab structure, both recommendations with sourced
    reasoning, the rendering blocker as the explicit next step, every OWED item intact, stays
    under 16,000 chars.
  - Issue #753 carries the same substance (already posted this session, verified present).
  - ONE commit; artifact-exempt (active_work.md only); pushed with an explicit refspec; PR opened.

amendments: (none)
