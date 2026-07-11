# Task contract — v2 team profile (Overview), reusing the design system

> Written on a CLEAN tree (branch `feat/site-v2-team-profile` off main @ d674905).
> Follows #672 (v2 Phase E increment 1 — design system + fixture page). CPO picked
> "Team profile" as the next template (AskUserQuestion, this conversation 2026-07-11).
> See docs/working_agreement.md §1 (E→P→C→I→V), §2 (contract), §10 (decision rights),
> §11 (blinded escalation), Appendix A (anti-patterns).

objective: >
  Build the Team profile Overview page (wireframe 02) in site_v2/, reusing the shared
  design system + components shipped in #672 and adding the team-specific components as
  consistent extensions of that system. Renders ONE real exported team (default season)
  across de/en/fi, behind /v2/. This proves the design system PAYS OFF (a second entity
  reuses it) and makes the fixture page's team links a real target. Live MVP untouched.

refs: >
  epic #361 · team profile #391 · wireframe `docs/wireframes/02_team_profile.md` (dated
  2026-06-11 — STALE in places, see decisions_reserved) · `docs/content_architecture.md`
  (Team tabs) · `docs/wireframes/metrics_display.md` (LOCKED 16-row table).
  Data: `scripts/export_site_data.py :: shape_team_payload`; mart `mart_team_profile`
  (columns re-read this session — deserved-vs-actual is now RANK-SPACE, GAP-13 resolved).

scope_paths:
  - site_v2/**            # new team components + page/route, new component CSS in system.css, committed sample team JSON, new i18n strings
  - .claude/task/**       # contract, review.md, review_input.patch
  - .claude/active_work.md # handover bullet (artifact-only follow-up commit)

# STRUCTURAL SURFACE = consumption (site*/). Short-form evidenced:
impact_map: >
  Additive to the existing v2 frontend (site_v2/). NO dbt model, NO live export script, NO
  live Pages deploy, NOTHING under site/ touched. Reads ONE committed sample team JSON from
  a READ-ONLY `python scripts/export_site_data.py --entities teams` (BigQuery ADC verified;
  SELECT-only). Reuses #672's lib (`format`/`bars`/`href`/`metricRows`/`types`) + components
  (Layout, Breadcrumb, Crest, SectionHead, form pills) + tokens; adds team-only component
  classes to the SAME global `system.css` (consistency by construction) + new i18n strings.
  Frontend is display-only (select/format/display; no fact derivation). Gate: ci-site-v2.yml
  (`npm ci && npm run build`). Blast radius: the non-deployed v2 build only; base stays "/v2/".

decisions_taken: >
  1. Template = Team profile Overview (screen 02), CPO-picked this conversation. Scope this
     increment to the DEFAULT SEASON (most-recent; domestic first) — the multi-season selector
     SWAP is a JS/island concern (deferred, #362); render the season as a static label/chip.
  2. Reuse the #672 design system; new team components (identity header, record block,
     single-value season-metric row, year-over-year row, streak chips, team fixture row) are
     designed as CONSISTENT extensions of the locked system rules (colour = meaning only;
     hierarchy = tone/weight/size; dark-first; the token set). CSS lives in `system.css`.
  3. Season metrics render the LOCKED 16-row table SINGLE-VALUE (label + one value, group
     subheads) — GAP-13 is now RESOLVED (all 16 season-variant rates exist on the mart;
     clean_sheets renders as count_fraction clean_sheets/played). Reuse `metricRows.ts`.
  4. Blocks that are well-specced + wired ship this increment: identity · record · season
     metrics (16) · year-over-year (domestic only; absent state) · streaks (runs ≥2) ·
     fixtures (next + last-5, GAP-15 wired) · internal links.
  5. Sample-data source: ONE real exported team, committed inside site_v2/ (temporary build
     input; replaced by the #365 wired export). CHOSEN: Arsenal (team_id 42, PL 2025-26) — a
     fully-covered, recognizable domestic team. Palmeiras (121) was preferred for the fixture→team
     cross-link, but the full teams export OOMs and the `--sample 200` scoped run did not include
     121; per the CPO-approved plan ("fall back to another well-covered team if needed") a
     well-covered fallback was used. The sample team is temporary demo data, NOT a §10 product
     decision (the template + blocks are the product surface, and come from the locked wireframe).

decisions_reserved:
  - "FLAGSHIP deserved-vs-actual (§10 — product/UX + the signature differentiator). The 02
     wireframe (§5) specs shot_share/points_capture % bars + a gap; but #606 shipped it as
     RANK-SPACE (`deserved_rank` vs actual `latest_rank` + `sot_rank_gap`) — its visual is
     NOT specced. RECOMMENDATION: DEFER the flagship block to its own design+build increment
     (design-first, the fixture-page precedent), and ship the rest of the Overview now. The
     CPO may instead want it designed now (mock-first, or as a proposed system extension).
     Surfaced in the plan-back."
  - "New-component VISUAL design (record block, YoY aligned rows, streak chips, single-value
     stat rows, identity header) — no locked mockup exists (the 02 wireframe is ASCII layout
     only). I will design them as consistent extensions of the #672 system per the rules and
     present a preview; the CPO confirms/redirects at plan-back + preview. Any specific visual
     the CPO wants to own (beyond the flagship) → say so."
  - "Multi-season competition selector SWAP = deferred (island #362); default season only."
  - "WHICH team to feature — RESOLVED (see decisions_taken 5): the CPO-approved plan authorized a
     fallback to another well-covered team; Palmeiras 121 (preferred) was not in the exportable
     --sample (OOM), so Arsenal 42 was used. Not a §10 product decision — temporary demo data."
  - "02 wireframe reconciliation (deserved-vs-actual → rank-space; GAP-13/15/20/23 resolved) =
     a docs/wireframes/** follow-up (out of THIS contract's scope; routes to bi-analyst)."

done_when:
  - site_v2 builds clean locally (`npm run build`) AND under ci-site-v2; the existing dist
    index-page assertions still pass, PLUS `dist/{de,en,fi}/teams/{slug}/index.html` generate.
  - The team Overview renders the ONE committed real team (default season): identity + record
    (rank/pts/W-D-L/goals/GD/clean sheets/form pills) + the LOCKED 16-row season metrics
    (single-value, honest "–") + year-over-year (or its absent state) + streaks (or omitted) +
    fixtures (next + last-5) + links — importing the system (no hand-styled screen).
  - Verified: local build + serve under /v2/; no fact derivation in the frontend (grep).
  - ONE substantive commit; ci-site-v2 green; required reviewers PASS (scope-auditor +
    cto-reviewer per review_routing.json); review.md diff_sha256 binds; CPO merges.
  - Handover bullet added to `.claude/active_work.md` (artifact-only follow-up commit).

amendments: (none)
