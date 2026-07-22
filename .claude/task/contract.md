# Task contract — point the display reviewer at built pages, not just specs

> Written on a CLEAN tree (branch `chore/route-display-reviewer-to-built-pages` off main @ fd0394f).
> CPO-directed 2026-07-22 after I proposed deferring this and he challenged it: *"So you suggested
> something that is not needed?"* It is needed, and the answer was that I had bundled a one-line
> routing fix with a large agent project and used the project's size to justify skipping both.
> See [[feedback-agent-guardrails]] [[feedback-design-off-the-cuff]].

protected_override: >
  `.claude/review_routing.json` and `.claude/agents/**` are PROTECTED: changing who reviews what,
  or what a reviewer looks for, is a governance event, precisely so the builder cannot weaken its
  own adversary. The CPO directed this change in conversation on 2026-07-22 in the words quoted
  above, after refusing my proposal to defer it. Routes to cto-reviewer; the opus-on-guards rule
  applies.

objective: >
  THE HOLE, demonstrated rather than hypothesised. Earlier today I planned to hand-write two
  metrics into a committed frontend sample so the team page would look finished while the data
  chain stayed broken. That violates the binding rule in `docs/wireframes/00_overview.md`, titled
  "the whole point": a block may reference ONLY fields that exist in today's exported data, and
  anything missing is NEVER SILENTLY DRAWN.

  `bi-analyst-reviewer` exists to enforce exactly that rule — it is the FIRST item in its hunt
  list. But it is routed to `docs/wireframes/**` and `site/i18n/**` only. A hand-written sample
  under `site_v2/src/data/` and a page under `site_v2/src/pages/` route to `cto-reviewer` (build
  config) and `scope-auditor` (contract scope), NEITHER of which checks whether a displayed field
  exists in the export. Verified by running the routing rules over the exact paths I was about to
  create: both returned `[cto-reviewer, scope-auditor]`. **Nothing would have stopped it.**

  So the rule is enforced on the DOCUMENT that describes a page and not on the PAGE, which is
  where a field actually gets drawn. Fix the route, and extend the reviewer's brief so it knows
  what to check on a built page as opposed to a spec.

  This is the ONE-LINE half of what I proposed this morning. The expensive half — a `ui-expert`
  doer, a new design reviewer, two consultants and a fan probe — stays deferred and is recorded
  as owed in the handover, along with mirroring the crests and amending the display contract.

refs: >
  Verified this session, not recalled:
  - Routing today: `docs/wireframes/**` and `site/i18n/**` -> `bi-analyst-reviewer`. `site_v2/**`
    -> `cto-reviewer` only. Confirmed by evaluating the fnmatch rules over
    `site_v2/src/data/teams/157.json` and `site_v2/src/pages/[lang]/teams/[team].astro`.
  - The reviewer's first hunt item is already the binding rule ("every wireframe block references
    only fields that exist in today's exported JSON; anything else must be a gaps-register
    entry"), so no new capability is being invented — only its aim is wrong.
  - FOUR places state its territory and must move together (swept, because a partial sweep is the
    failure I repeated three times today): the two route patterns in `review_routing.json`; the
    `description:` frontmatter AND the "Your territory" line in `.claude/agents/bi-analyst-reviewer.md`;
    and the cast list in `docs/agent_guardrails.md` line 72. `docs/metrics_context_model.md:250`
    mentions "bi-analyst-owned" about the display contract, not routing — correctly untouched.
  - `docs/working_agreement.md` does NOT enumerate routes, so it needs no edit. Checked.

impact_map: >
  writers: none. No data, no model, no table. This changes which reviewer the commit gate demands
    for a given set of staged paths, and what that reviewer is told to look for.
  downstream: `.claude/hooks/git_discipline.py` reads `review_routing.json` to compute the REQUIRED
    reviewer set for a staged diff and DENIES the commit unless every required reviewer has a
    verdict in `review.md`. `scripts/check_task_artifacts.py` is the CI backstop applying the same
    rules. So the effect is: from this commit on, any change touching `site_v2/src/**` requires a
    bi-analyst-reviewer verdict in addition to cto-reviewer and scope-auditor. That is the point,
    and it lands on the very next task (the team page). Build config OUTSIDE `src`
    (`astro.config.mjs`, `package.json`, `tsconfig.json`) is unaffected and still draws only
    `[scope-auditor, cto-reviewer]`.
    (CORRECTED after the round-2 cto review: this sentence said `site_v2/**`, which was false —
    the route is `site_v2/src/**`. The same review found the mitigation sentence below also
    describing the superseded design. Both are fixed here, in the same amendment that supersedes
    `decisions_taken` (2), rather than left standing in the one field the protected-path gate makes
    mandatory and the review hash binds.)
  layer_rules: none apply. No dbt model, no SQL, no seed, no CI workflow.
  deploy_order: none. No warehouse object. Takes effect for the next commit whose staged paths
    match the new patterns.
  blast_radius: bounded and deliberate. Every future frontend change costs one more reviewer, at
    sonnet, which is the price of the rule being enforced where it is broken rather than where it
    is written down. Risk of getting it wrong in the OTHER direction: too broad a pattern would
    demand a display review for changes with no display content (a build-config edit, a
    dependency bump), which is the cry-wolf failure the guardrails doc warns about. Mitigated by
    routing `site_v2/src/**` rather than all of `site_v2/**`: everything that can render a field
    lives inside `src`, and the build config that cannot lives outside it, so the exclusion needs
    no exception list to maintain. (An earlier version said the mitigation was "routing the page
    and data directories specifically" — that design is superseded, and it was exactly the partial
    sweep that missed seven files.) No existing route is removed or narrowed; this is purely
    additive, so nothing reviewed today stops being reviewed.

scope_paths:
  - .claude/review_routing.json
  - .claude/agents/bi-analyst-reviewer.md
  - docs/agent_guardrails.md
  - .claude/active_work.md
  - tests/test_governance_hooks.py

decisions_taken: >
  (1) DO THIS NOW rather than defer it. CPO 2026-07-22, challenging my proposal to defer:
      "So you suggested something that is not needed?" It is needed; deferring it immediately
      before building a page defers it at the worst possible moment, because the page is exactly
      what it protects.
  (2) Route the PAGE and DATA directories, not all of `site_v2/**`. Engineering call, not §10:
      a build-config or dependency change has no display content, and demanding a display review
      for it is the cry-wolf failure that trains everyone to ignore the guard.
  (3) The expensive agent work stays deferred and is RECORDED as owed in the handover rather than
      held in my head. Today proved the difference: compressing the handover this morning deleted
      an owed rename, which then cost two review rounds to reconstruct.

decisions_reserved:
  - Whether the display reviewer should ALSO judge whether a built page matches its approved
    design mock, as opposed to only whether its fields exist in the export. That is a bigger
    question about who owns design review, and it belongs with the deferred agent set.
  - The deferred items themselves are recorded, NOT decided: the agent set, the metric-change
    skill, mirroring crests off the provider's origin, and amending the locked display contract to
    carry the two newly-surfaced metrics.

done_when:
  - The routing rules, evaluated over a page path and a committed data path, return
    bi-analyst-reviewer in the required set. Tested by running the same evaluation used to find
    the hole, so the fix is proven against the exact case that motivated it.
  - A build-config path under `site_v2/` does NOT pull in the display reviewer (the cry-wolf
    check, the other direction).
  - `review_routing.json` still parses as JSON and the hooks still read it without error.
  - The reviewer's own brief tells it what to check on a BUILT page, not only on a spec.
  - All four statements of its territory agree.
  - The handover records every deferred item as owed, in the file a fresh session is given.
  - ONE commit, pushed with an explicit refspec, PR opened. The CPO merges.

amendments:
  - 2026-07-22: + `tests/test_governance_hooks.py`.
    AUTHORITY: the cto-reviewer FAIL at opus (F4), plus the CPO's ruling below which widened what
    is routed and so widened what needs proving.
    CONTENT: nothing tests the REAL routing file. The suite's `ROUTING` fixture at line 387 is
    synthetic (`{"dbt_project/**": [...]}`); no test loads `.claude/review_routing.json` or asserts
    a required-reviewer set for any real path. `done_when` originally said "tested by running the
    same evaluation used to find the hole" — a one-off manual run recorded only as prose. For a
    guard change whose entire payload is data in a JSON file, that is not verification. A test that
    loads the real routing and asserts the reviewer set over paths enumerated from `git ls-files`
    WOULD HAVE CAUGHT the gap below, which is the whole argument for it.

  - 2026-07-22: SCOPE OF THE ROUTE CORRECTED, and this is the substantive amendment.
    THE GAP, found by the cto-reviewer: the first attempt routed `site_v2/src/pages/**`,
    `components/**`, `data/**` and `i18n/**` — and MISSED `site_v2/src/lib/`, which holds
    `metricRows.ts`, the CPO-locked 16-row display contract, plus `format.ts` (the
    no-naked-percentage and null-as-dash rules) and `bars.ts` (the direction-to-green encoding).
    Fabricating a metric takes TWO files: a row in `metricRows.ts` and a key in the committed
    sample. I routed the sample and not the contract, so the fix caught half of a two-file fake.
    `layouts/` and `styles/` were missed as well: SEVEN tracked files in total, enumerated rather
    than counted from memory — `lib/metricRows.ts`, `lib/format.ts`, `lib/bars.ts`, `lib/href.ts`,
    `lib/types.ts`, `layouts/Layout.astro`, `styles/system.css`. (This said "six" until the round-2
    cto review counted them: an undercount inside the very amendment whose lesson is "enumerate the
    real tree". Twice in one entry.)
    HOW I MISSED IT, which matters more than the miss: my `refs` claimed verification against
    `site_v2/src/data/teams/157.json` and `site_v2/src/pages/[lang]/teams/[team].astro`. NEITHER
    FILE EXISTS. They are files I intended to create. I verified against an imagined tree in the
    very contract that says "a partial sweep is the failure I repeated three times today".
    Enumerating `git ls-files site_v2` takes one command and finds all six immediately.
    THE FIX IS THE CLASS, NOT THE INSTANCE: one pattern, `site_v2/src/**`, instead of a directory
    list that can be incomplete again. Verified over every tracked file: zero `src/` files without
    the display reviewer, zero non-`src/` files with it.
    AUTHORITY: **CPO, AskUserQuestion 2026-07-22: "Yes, everything under site_v2/src"**, to a
    discrete question offering three paths (all of src / pages-and-data only / no change).
    This ALSO answers the scope-auditor's FAIL, which was right: routing a reviewer at a new path
    class is a §10 rule extension, and my authority for it was the CPO asking a rhetorical
    question ("So you suggested something that is not needed?"), not a discrete answer. That is
    the identical failure the metric rename was caught on three hours earlier, in a contract that
    quotes that lesson. Recorded in `escalations.log`.
    DECISIONS_TAKEN (2) IS SUPERSEDED by this: the pages/components/data split is gone, and with
    it the claim that build config was the only exclusion.
