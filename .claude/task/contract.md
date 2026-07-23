# Task contract — repo polish: honest shopfront, kill dead links, frame the guardrails

> Written on a CLEAN tree (branch `chore/repo-polish` off main @ 07a224c, after the guardrail trim
> #808 merged). Presentation/docs only.
> No structural surface, so no impact_map and no consulted field are required.

objective: >
  Make the public repo make the right first impression IN ITS CURRENT STATE, for an experienced
  data / analytics / web / AI engineer assessing it as the owner's flagship. Three problems, all
  verified this session:
  (1) GitHub Pages is 404 (confirmed via `gh api .../pages`). Every outward link is dead — the
  README live-demo link, the dbt-docs link, and the repo's own homepage URL — and the repo
  DESCRIPTION advertises a "live web app". The MVP was taken offline deliberately over possible
  rights issues with provider content, so the demo stays dead; the links and the description must
  stop pointing at it.
  (2) The README hero image `docs/assets/screenshot.png` is that retired app, showing competition
  branding — the same class of content the app was pulled for. It is removed, and the architecture
  diagram becomes the lead visual (a strict upgrade for a data-pipeline repo, and rights-clean).
  (3) The `.claude/` AI-assisted-development guardrails are ~3,300 lines plus 244 tests, committed
  and unframed, so a reviewer reads them as over-engineering. CPO direction: SHOWCASE them, do not
  hide them. A README section frames them as deliberate, sized to what a staff-level review judges
  worth keeping (that review is running; its verdict shapes the section and may spawn a separate
  trim task — trimming is NOT in this PR).

refs: >
  Verified this session, not recalled:
  - `gh api repos/.../pages` -> 404: Pages is genuinely gone, so all three github.io links are dead.
  - `gh repo view`: description = "...live web app. ...built to scale"; homepageUrl = the dead
    match-preview link; 14 topics already set (good, untouched); MIT license (good).
  - README badges (CI, Data Build, License, dbt, BigQuery, Python) resolve and are kept.
  - `docs/assets/screenshot.png` read directly: the retired Matchday IQ landing page with league
    crests/branding.
  - The presentation principles are `C:\Users\Rami\.claude\skills\polish-repo\repo-presentation.md`
    (understated, honest about state, non-brittle numbers, owner owns product framing).

scope_paths:
  - README.md
  - docs/assets/screenshot.png
  - docs/assets/README.md
  - .claude/active_work.md

decisions_taken: >
  (1) DO THE POLISH NOW, before the team page, so a reviewer meets a clean repo. CPO 2026-07-22,
      after an honest state assessment: "do it" / "Do as recommended so I'm making the best
      impressions in the current state."
  (2) The retired demo stays dead (CPO: "We removed the mvp because of possible legal issues").
      Remove the dead links and the screenshot; make the description and headline honest about
      state (pipeline solid, web app a prototype not currently public).
  (3) SHOWCASE the guardrails rather than hide them (CPO: "Don't hide ... quite the opposite. It
      should show that I'm capable of doing it").

decisions_reserved:
  - The exact README prose (headline, live-status line, the guardrails section) and the new repo
    DESCRIPTION text are product framing — proposed to the CPO for sign-off before any file is
    written, never set unilaterally.
  - Whether to TRIM the guardrail machinery, and by how much, depends on the staff-level review and
    is a SEPARATE decision and task, explicitly out of this PR (which only frames what exists).
  - Whether to revive a dbt-docs site later: deferred. This pass keeps everything static and off
    Pages, per the legal caution.

done_when:
  - No dead github.io link remains in README.md, and the repo description/homepage no longer point
    at the retired app. Verified by re-checking each link resolves (or is removed).
  - `docs/assets/screenshot.png` is removed and no longer referenced; the README lead visual is the
    Mermaid diagram, which renders (valid syntax).
  - The README states repo state honestly: pipeline live/gated, web app a prototype not public.
  - A README section frames the `.claude/` guardrails as deliberate AI-collaboration engineering.
  - CPO signed off on the README prose and the description BEFORE it was written.
  - ONE commit, pushed with an explicit refspec, PR opened. The CPO merges.

amendments: (none)
