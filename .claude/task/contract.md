# Task contract — v2 frontend: design system + fixture template (Phase E, increment 1)

> Written on a CLEAN tree (branch `feat/site-v2-fixture-page` off main @ 7005052).
> CPO-directed this conversation 2026-07-11 ("Start the v2 frontend build — Phase E").
> Design is LOCKED (do not re-litigate): memory `project_v2_frontend_design.md` +
> the reference mockup artifact d70aae67 (tokens/components/layout extracted).
> See docs/working_agreement.md §1 (E→P→C→I→V), §2 (contract), §10 (decision rights),
> §11 (blinded escalation), Appendix A (anti-patterns).

objective: >
  Stand up the shared v2 design system in site_v2/ — the token layer, base components,
  and a Layout — and prove it by rendering ONE real exported fixture through a fixture
  template, built as the /v2/ preview artifact. The design system is the deliverable;
  the fixture page is the proof it composes. Import the system, never hand-style the
  screen. The live MVP (site/) and its Pages deploy stay untouched (cutover = #377).

refs: >
  epic #361 (v2 site) · design system #366 · fixture template #368 · export #365 ·
  Phase E. Binding specs: docs/wireframes/01_fixture_page.md (layout + JSON bindings),
  docs/wireframes/metrics_display.md (LOCKED 16-row team table), docs/site_architecture.md
  (IA/URLs/i18n/deploy), docs/content_architecture.md (fixture block = composed v2 export).
  Data schema: scripts/export_site_data.py :: shape_fixture_payload / fetch_fixture_payloads.
  Reference mockup: https://claude.ai/code/artifact/d70aae67-0c0a-43c3-86df-9d983742a881

scope_paths:
  - site_v2/**            # astro config (base), Layout, tokens CSS, components, fixture template, committed sample fixture JSON, minimal i18n strings
  - .claude/task/**       # this contract, review.md, review_input.patch
  - .claude/active_work.md # handover bullet (artifact-only follow-up commit)

# STRUCTURAL SURFACE = consumption (site*/). Short-form evidenced (new, isolated, leaf consumer):
impact_map: >
  New, isolated v2 frontend consumer under site_v2/ (already scaffolded: Astro 5, static,
  i18n de/en/fi, `base` unset). Touches NO dbt model, NO live export script, NO live Pages
  deploy, and NOTHING under site/. Reads ONE committed sample fixture JSON produced READ-ONLY
  by `python scripts/export_site_data.py --entities fixtures` (BigQuery ADC verified OK,
  rami.fahham@gmail.com; SELECT-only, no warehouse writes — the clobber risk is dbt-build-only,
  not read queries). No fact derivation in the frontend (select/display only, per the
  consumption-layer contract). Blast radius: the non-deployed v2 build only; the live product
  is unaffected by construction (separate directory, separate CI = ci-site-v2.yml npm build,
  which does NOT deploy). deploy_order: none — nothing is wired into the live Pages artifact
  this increment (see decisions_reserved: /v2/ deploy wiring is deferred to a follow-up PR).
  Gate: ci-site-v2.yml (`npm ci && npm run build` + existing dist index-page assertions).

decisions_taken: >
  1. Phase E is GO. active_work.md held "do NOT start the v2 frontend (Phase E) until the
     data+export is all green"; the CPO has now directed the start, and content_architecture.md
     (2026-07-07) confirms green — 18 marts wired, fixture screen ✓. This contract records that
     the hold is lifted by CPO direction this conversation.
  2. Design is LOCKED — extracted verbatim from the reference mockup: token set (dark-default
     `.fx` custom properties + `[data-theme=light]` swap), component classes, and the fixture
     layout/section order. Colour = meaning only (green = better value by catalogue `direction`,
     RESERVED — never links/labels); hierarchy = tone/weight/size. Not re-litigated.
  3. Data bindings follow docs/wireframes/01_fixture_page.md (each field verified against the
     v2 fixture payload) and the LOCKED 16-row table (metrics_display.md). Rows/fields absent
     from today's payload render the designed empty state ("-", no bar; W2 counts fall back to
     the window header) — data honesty, never fabricated. The committed sample JSON is the
     ground truth for what has data today.
  4. Sample-data source: ONE real fixture, exported READ-ONLY via export_site_data.py and
     committed inside site_v2/ so the static build (and ci-site-v2, which has no BigQuery) is
     self-contained. Clearly labelled a temporary committed sample, to be replaced when the v2
     export is wired as the build data source (#365 deploy).
  5. /v2/ = enact the preview-phase routing (`base: "/v2/"`, the value the astro.config comment
     already earmarks) WITHOUT touching the live Pages deploy — Option A below.

decisions_reserved:
  - "/v2/ LIVE DEPLOY WIRING (§10 — platform + live artifact) — RESOLVED 2026-07-11 (CPO ruled
     Option A this session: build-and-prove now, defer the live-deploy wiring; no scope change —
     the contract already baselines A). Option A (this
     contract): set base:\"/v2/\" + build the /v2/ artifact; verify via ci-site-v2 build +
     local astro preview + preview tooling; DEFER wiring the live Pages deploy. Option B: also
     wire the deploy now — edits PROTECTED .github/workflows/pages-match-preview.yml +
     scripts/build_match_preview_site.sh and changes the LIVE Pages artifact; the repo itself
     documents this as 'a separate, deliberately-reviewed change' (ci-site-v2.yml header).
     Option B requires a contract AMENDMENT adding a protected_override (CPO authority) + those
     paths + cto-review on the guard path. Surfaced in the plan-back; CPO rules at Confirm."
  - "WHICH real fixture to feature. --sample picks the earliest kickoff globally; a well-covered
     upcoming fixture (full w1/w2/form_window/top_players/h2h) makes a stronger proof. If none
     has full coverage today, the honest empty states render. CPO may prefer a specific league."
  - "i18n depth in increment 1. Rec: generate the fixture route under all 3 locale prefixes
     (routing is the point), chrome from a small site_v2/src/i18n strings map (the ~dozen fixture
     UI labels), metric ROW labels in English from the catalogue for now; full catalogue-i18n key
     wiring + DE/FI metric labels = the #370 follow-up slice. (Label completeness is a separate
     workstream, not this increment.)"
  - "Route shape. Rec: the real URL /{lang}/{competition-slug}/matches/{slug}/ via getStaticPaths
     over the one committed fixture (proves the programmatic pattern), vs a placeholder route."
  - "None of the above are decided by me — each is flagged blinded (§11) in the plan-back."

done_when:
  - site_v2 builds clean locally (`npm run build`) AND under ci-site-v2 (`npm ci && npm run build`);
    the existing dist index-page assertions still pass (base prefixes URLs, not the output dir — verified by the build).
  - The fixture route renders the ONE committed real fixture: dark-default; tokens + components
    imported (no hand-styled screen); masthead + standing chips (omitted when null) + segment
    (Last 5 / This season) + form (W1 pills / W2 counts-or-header) + the LOCKED comparison table
    (group order, direction-driven green, honest "-" for rows without data) + recent matches +
    players-to-watch + h2h + explore links + footnote — each section rendering real data or its
    designed empty state.
  - Verified in the preview tooling: screenshot dark + light, console/network clean; no fact
    derived in the frontend (grep the template — select/format/display only).
  - ONE substantive commit; ci-site-v2 green; required reviewers PASS (scope-auditor + cto-reviewer
    per review_routing.json — bi-analyst NOT required, site/i18n untouched); review.md diff_sha256
    binds; CPO merges (I never merge).
  - Handover bullet added to .claude/active_work.md (artifact-only follow-up commit).

amendments: (none)
# On amendment (clean tree only):
#   - <date>: + <path> — authority: <CPO answer / standing rule>; content: <what>
