# Active work — handover

> The single handover contract. A fresh chat is given this file (via the `handover_in`
> SessionStart hook). Continue from here; do not re-scope or infer from issue titles or
> memory. Keep it current (status + next action + do-NOTs). Update it before you finish.

_Last updated: 2026-06-10 (EOD). Epic #317 modeling COMPLETE. Pivoted to **epic #361 — the new
website platform**. Phase 0 underway. Two PRs open awaiting merge: **#384** (docs fix) and
**#385** (#365 per-entity export). Continue tomorrow._

## Current focus
Building **epic #361 — the new website platform**: replace the mobile-card MVP (`site/`) with a
professional, responsive, multilingual football-analytics **website** (kicker/whoscored/fbref/
onefootball class), built as a **programmatic content site** (Astro) — a few templates rendered
from the marts into tens of thousands of SEO pages.
- **Read first:** `docs/site_architecture.md` (the IA/URL/template→mart contract) and
  `docs/ui_design_brief.md` (the design pass brief). Roadmap: plan file
  `C:\Users\Rami\.claude\plans\fuzzy-launching-meadow.md`.

## Status — the data layer (epic #317) is DONE
All performance/insight marts merged and live: `mart_matchday_insights`, `mart_momentum__team/__player`,
`mart_season_to_date__team/__player`, `mart_standings`, `mart_form_window__team`,
`mart_fixture_stats__team/__player`, `mart_team_profile`, `mart_player_profile`,
`mart_player_match_log`, `mart_head_to_head`, `mart_top_scorers`, `mart_team_season(_insights)`.
Epic #317 CLOSED. Earlier-session detail (momentum/standings/profiles/player-pipeline/backfill)
is in the prior handover history + memory; not repeated here.

## Status — epic #361 (new website)
**Created today:** epic **#361** + 16 sub-issues (#362–#377). Closed done/stale issues; folded
the old UI issues (#156/#159/#149/#160/#120/#132/#122) under the epic via pointer comments.

**Merged today (Phase 0 + a data add):**
- ✅ **#379** — `docs/site_architecture.md` (IA, URL scheme, template→mart contract, SEO surface).
- ✅ **#380** — `docs/ui_design_brief.md` (data-grounded design brief; the package for Claude Design).
- ✅ **#381** — registry display metadata (confederation, tier, slug, sort_order on all 45 comps)
  for the hybrid nav. YAML-only (no dbt seed change); onboard-competition skill updated.
- ✅ **#382** — Astro scaffold under `site_v2/` + `ci-site-v2.yml` (path-filtered build check, **no
  deploy**). Isolated from the live MVP.
- ✅ **#383** — `mart_head_to_head` (directed pair, past-meetings record + recent_meetings).

**Open PRs (merge first thing):**
- 🔶 **#384** — corrects the home-page composition in the two docs (see "home page" below).
- 🔶 **#385** — **#365 per-entity export** first slice: `scripts/export_site_data.py` + tests.
  Framework + **teams** (`mart_team_profile`) and **players** (`mart_player_profile` +
  `mart_player_match_log`) → `data/{entity}/{id}.json` + `slug_map.json` + `manifest.json`.
  Additive (does not touch `export_pages_data.py` or the live deploy); output gitignored.

## Locked decisions (do NOT re-debate)
- **Tech stack = Astro**, static-only, GitHub Pages. Islands for charts/search. No SSR/backend.
- **Hybrid competition IA**: browse by competition group AND country hub, registry-driven.
- **Home page = hybrid, fixtures-first** (CPO 2026-06-10): (1) upcoming-fixtures hero across
  competitions [the MVP's core feature elevated; cross-competition feed is a build], (2) hybrid
  browse [registry, exists], (3) storylines/trending from `mart_team_profile` [data exists;
  narrative generator is a build], (4) stats — leaderboards + standings [exist]. The MVP's
  competition-card landing is OBSOLETE for the website.
- **Two distinct "head-to-head" meanings — keep them straight:** (a) the **side-by-side form
  comparison** (the existing match preview — `mart_matchday_insights` + `mart_momentum__team`);
  (b) **past meetings** between the two clubs (new — `mart_head_to_head`, #383). Both belong on
  the fixture page. (b) reverses #323's "H2H dropped (no product value)".
- **Current MVP stays live until v2 parity + CPO sign-off** (#377). `site_v2/` is isolated;
  no epic-#361 PR may break the live site.
- **Metric governance = catalogue-only** (see do-NOTs).

## Next concrete action (tomorrow)
1. **Merge #384 + #385** (then delete branches, sync main).
2. **Continue #365 export — fast-follows** on the same framework, in order:
   **fixtures** (the core page — joins ~6 marts + `mart_head_to_head`; the fixture JSON is the
   biggest), then competitions/standings, leaderboards, and the **landing feed** (cross-competition
   fixtures + trending). Each: restate-spec-before-coding.
3. In parallel: the **design pass** — `docs/ui_design_brief.md` (corrected by #384) goes to Claude
   Design for visual directions; then codify the chosen direction into `site_v2` tokens/components
   (#366), then templates (#368).
4. Eventually: SEO engine (#369), i18n scale-out (#370), search/analytics/a11y/legal, migration (#377).

## Do NOT
- **Do not invent or re-define metrics in a mart/export.** The `metric_catalogue` seed is the only
  source of metric definitions; render by its formula, labels from its i18n keys. A metric not in
  the catalogue → propose a CPO-approved catalogue addition first. (Burned this session: #325 draft
  freelanced goal_conversion/per-90/shot_accuracy and mis-stated pass_accuracy.) See memory
  `feedback_metric_catalogue_governance`.
- **Do not present a design/IA/product decision as settled without discussing it.** (Burned this
  session: invented a home-page composition and wrote it into two docs as fact; #384 corrects it.)
  Ground every UI claim in real data (the §6 data contract) — no xG, shot maps, heat maps, pass
  networks, or win probabilities; we don't have them.
- **Do not touch the live MVP** (`site/`, `export_pages_data.py`, `pages-match-preview.yml`) while
  building v2. v2 is additive in `site_v2/` + `scripts/export_site_data.py`. Cutover is #377 only.
- **Do not hardcode a competition** anywhere above staging; `league_code` is the partition key.
- Branch from `main`; never commit to main; feature branch → push explicit refspec → PR (the
  post-commit hook auto-pushes + opens the PR; the `gh` PR step 401'd once — if so, open it manually).

## Environment notes (this machine)
- `~/.dbt/profiles.yml` is fixed (has the `football_data_pipeline` bigquery profile) — local dbt
  works with no `--profiles-dir`. dbt/sqlfluff run from the project `.venv` (global dbt is broken).
- `site_v2/` needs Node (v24 present); `cd site_v2 && npm ci && npm run build`.
- `scripts/export_site_data.py` reads BQ marts (uses ADC); `--sample N` for quick checks; output
  to `artifacts/site_data/` (gitignored).

## Small loose ends (optional)
- `ci-data-build` runs the full 8-min BQ build for any CI-workflow change (it triggered on the v2
  workflow add). Worth narrowing its path filter so pure-`site_v2/` PRs skip it.
- Orphaned macros from #321 (`bl1/bl2/l1_*_round_names`) cleanup chip — still pending, low priority.
