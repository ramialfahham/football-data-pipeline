# Active work — handover

> The single handover contract. A fresh chat is given this file (via the `handover_in`
> SessionStart hook). Continue from here; do not re-scope or infer from issue titles or
> memory. Keep it current (status + next action + do-NOTs). Update it before you finish.

_Last updated: 2026-06-11 (EOD). Epic #361 (new website): Phase 0 done + the per-entity
**export is functionally complete** (every page's JSON except the landing feed). main healthy,
no open PRs. **Next: pin the HOMEPAGE SPEC (wireframe level) — it's the one thing blocking the
landing feed, and the design thread the CPO flagged.**_

## Current focus
Epic **#361 — the new website platform**: replace the mobile-card MVP (`site/`) with a
professional, responsive, multilingual football-analytics **website** (Astro, programmatic
content site). **Read first:** `docs/site_architecture.md` (IA/URL/template→mart contract),
`docs/ui_design_brief.md` (design brief), roadmap plan
`C:\Users\Rami\.claude\plans\fuzzy-launching-meadow.md`.

## Status
- **Data layer (epic #317): DONE** — all team/player/fixture/standings/H2H/profile marts merged.
- **Phase 0 (#361): DONE** — #379 architecture doc, #380 design brief, #381 registry display
  metadata (confederation/tier/slug/sort_order), #382 Astro scaffold under `site_v2/` +
  `ci-site-v2.yml` (build check, NO deploy), #384 home-composition doc fix.
- **Per-entity export (#365): functionally COMPLETE.** `scripts/export_site_data.py` →
  `artifacts/site_data/` (gitignored). Targets built + verified on BQ:
  - teams, players (+ match log) — #385
  - fixtures core (header + W1 momentum + W2 season-to-date + rank + H2H) — #387
  - nav.json (hybrid groups + country hubs), competitions/{league}/{season}.json,
    fixture drill-down (form_window + top_players) — #388
  - leaderboards/{league}/{season}.json (goals/assists/shots_on_target), metrics.json
    (glossary from catalogue), matchstats/{fixture}.json (form-window click-through) — #389
  - **NOT built: landing.json** — intentionally held until the homepage spec is pinned.
- **#383** — `mart_head_to_head` (past meetings, directed pair). **#387 also** added
  `mart_fixture_standing_context` (shared single source of phase-relevant rank) and refactored
  `mart_matchday_insights` (MVP) to read from it — validated output-IDENTICAL (0/163 mismatches).

## The actual website is NOT built yet
The export produces JSON for every page; the **Astro templates/pages, design system, SEO,
i18n, search** are the bulk of remaining work (#366 design, #368 templates, #369 SEO, #370 i18n,
#371 search, #372 analytics, #373 a11y/perf, #374 legal, #377 migration/cutover). All gated on
the design pass, which is gated on the homepage spec.

## Next concrete action
1. **Pin the HOMEPAGE SPEC at wireframe level** (the CPO flagged Claude Design's drafts as
   unprofessional; the fix is spec precision, not another tool pass). Approach: per-screen
   wireframes (home first, then fixture page, team profile) — exact layout, section order,
   above-the-fold, and **every block bound to a real field** from the data contract. Home model
   is the agreed **hybrid, fixtures-first** (see locked decisions). This unblocks `landing.json`.
2. Then: the design pass (brief + wireframes → visual directions) → codify into `site_v2`
   tokens/components (#366) → build templates (#368) against the real exported JSON.
3. Build `landing.json` export once the home modules/order are pinned (+ the cross-competition
   fixtures feed + the data-to-text narrative generator it needs).

## Locked decisions (do NOT re-debate)
- **Astro**, static-only, GitHub Pages; islands for charts/search. No SSR/backend.
- **Hybrid competition IA**: groups (leagues/cups/continental-club/national-teams) + country
  hubs, registry-driven (`nav.json`). Cards landing is OBSOLETE for the website.
- **Home = hybrid, fixtures-first**: (1) upcoming-fixtures hero across competitions, (2) browse,
  (3) storylines/trending (`mart_team_profile`), (4) stats (leaderboards + standings). The exact
  module order/above-the-fold is what the homepage spec will pin.
- **v2 reads SOURCE marts, never `mart_matchday_insights`** — that is the MVP's presentation
  pivot (retired at cutover #377). Phase-relevant rank lives once in
  `mart_fixture_standing_context`.
- **Two "head-to-head" meanings:** (a) side-by-side form **comparison** = the existing match
  preview (`mart_momentum__team` etc.); (b) **past meetings** = `mart_head_to_head` (#383). Both
  on the fixture page.
- **Current MVP stays live until v2 parity + CPO sign-off** (#377). v2 is additive in `site_v2/`
  + `scripts/export_site_data.py`; the legacy `export_pages_data.py` + Pages deploy are untouched.
- **Metric governance = catalogue-only** (see do-NOTs).

## Do NOT
- **Do not invent/redefine metrics** in a mart or export. `metric_catalogue` seed is the only
  source; render by its formula, labels from its i18n keys. New metric → CPO-approved catalogue
  addition first. (Memory `feedback_metric_catalogue_governance`.)
- **Do not present a design/IA/product decision as settled without discussing it.** Ground every
  UI claim in the §6 data contract — no xG, shot maps, heat maps, pass networks, win
  probabilities (we don't have them). (Burned earlier: an invented home-page composition.)
- **Do not route v2 through `mart_matchday_insights`** (MVP presentation pivot) — read the source
  marts; extract shared logic to a shared mart (as done for rank in #387).
- **Do not touch the live MVP** (`site/`, `export_pages_data.py`, `pages-match-preview.yml`).
- **Do not hardcode a competition** above staging; `league_code` is the partition key.
- Branch from `main`; never commit to main; feature branch → push explicit refspec → PR (the
  post-commit hook auto-pushes + opens the PR; if the `gh` PR step 401s, open it manually).

## Environment notes (this machine)
- `~/.dbt/profiles.yml` fixed — local dbt works with no `--profiles-dir`. dbt/sqlfluff from the
  project `.venv` (global dbt broken).
- `scripts/export_site_data.py` reads BQ marts via ADC; `--sample N` for quick checks; output to
  `artifacts/site_data/` (gitignored). Pure helpers unit-tested in `tests/test_export_site_data.py`
  (no BQ) → `python-ci` covers them.
- `site_v2/` needs Node (v24 present): `cd site_v2 && npm ci && npm run build`.

## Small loose ends (optional)
- `ci-data-build` runs the full ~8-min BQ build on any CI-workflow change (it fires on
  `site_v2/`-adjacent workflow edits). Worth narrowing its path filter.
- Per-metric leaderboards beyond goals/assists/shots need a "which metrics" design call.
- Orphaned macros from #321 (`bl1/bl2/l1_*_round_names`) cleanup chip — low priority.
