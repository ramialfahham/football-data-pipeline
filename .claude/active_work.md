# Active work — handover

> The single handover contract. A fresh chat is given this file (via the `handover_in`
> SessionStart hook). Continue from here; do not re-scope or infer from issue titles or
> memory. Keep it current (status + next action + do-NOTs). Update it before you finish.

_Last updated: 2026-06-11 (mid-session). Epic #361 / blueprint #391: wireframes 01–03
merged, metric + window + consumption contracts LOCKED, data gap queue largely shipped.
**Next: the mart-side gap work (GAP-15/16/19), then the slim export PR, then blueprint
PR 3 (screens 04–07).**_

## Current focus
Epic **#361** via **#391 (website blueprint)**: field-bound wireframes per screen +
the data gaps they surface. **Read first:** `docs/wireframes/00_overview.md` (format
contract), `docs/wireframes/metrics_display.md` (LOCKED metric display contract),
`docs/wireframes/99_gaps_register.md` (GAP-01..19 + rulings),
`dbt_project/docs/layering.md` §Consumption layer (the newest contract).

## Status
- **Blueprint**: PR 1 (overview + 01 fixture page + register) and PR 2 (02 team,
  03 player) MERGED. Screens 04–10 pending (home LAST — pins the homepage spec →
  unblocks `landing.json`).
- **Metric display contract (`metrics_display.md`) LOCKED**: team = 16 single-metric
  rows, blocks Goals→Shooting→Duels→Defending→Passing→Set pieces→Goalkeeping, tiers
  4/9/3 (tier never reorders; tier 1 = compact surfaces); player = the 9 bundled rows,
  NO tiers, full-triple ratios `{num} of {den} · {pct}%`, zero-denominator `0 of 0 · —`.
- **Window & scope contract (same file)**: one cross-competition number in the product
  (W1 live form); every cumulative number is within one competition; W2's user-facing
  name = "through matchday N"; tournament exception = cumulative + qualifier preview
  (GAP-18, unimplemented, needed before WC 2026).
- **Data PRs MERGED**: #395 catalogue v2 (group/tier/order columns + 6 new metrics),
  #396 window marts (W/D/L counts, clean sheets, SoT/duels/defensive-actions rates,
  GK atomics, SoT own-coverage fix), #397 season rollup (5 season variants).
  All cross-checked on BQ (0 mismatches over 3,007 team-seasons).
- **OPEN: PR #400** — consumption-layer contract (layering.md section + edit-time hook
  on `scripts/export_*.py` / `site/` / `site_v2/` + GAP-19 audit + this handover).

## Gaps register state (docs/wireframes/99_gaps_register.md)
- Shipped: GAP-09/10/11/12 (catalogue + window marts), GAP-13 (season variants).
- Approved, NOT built: **GAP-15** (mart_team_fixtures — next + last 5 per team-season,
  on `fct_fixture` + `int_legs__team_match` perspective legs), **GAP-16** (player→team
  affiliation in dbt, DQ-tested), **GAP-14** (export surfaces birth_date — trivial,
  rides the slim export PR), **GAP-18** (tournament window mode + phase descriptor —
  before WC 2026), **GAP-19** (migrate the 5 Python derivations to dbt: leaderboard
  ranks, top-player ranks, nav taxonomy→registry/seed, H2H pair key, **slugs**).
- Pending rulings: GAP-01..08 (at their screens' reviews), GAP-17 (rollup denominators
  — changes shipped MVP numbers).

## Next concrete actions (in order)
1. **Marts PR(s)**: GAP-15 `mart_team_fixtures` + GAP-16 player affiliation + GAP-19
   migrations (rank columns per `mart_top_scorers.scorer_rank` pattern, leaderboards
   mart, `display_group` in registry/seed, canonical pair key on `mart_head_to_head`,
   slug columns on entity marts).
2. **Slim export PR**: GAP-14 birth_date + replace the five Python derivations with
   mart reads; export = selection/grouping/formatting ONLY.
3. **GAP-18** tournament window (before WC 2026).
4. **Blueprint PR 3** (04 competition hub, 05 leaderboards, 06 h2h, 07 glossary),
   then PR 4 (08 browse, 09 chrome), PR 5 (10 home → `landing.json` issue).

## Locked decisions (do NOT re-debate)
- **CONSUMPTION-LAYER CONTRACT (CPO, verbatim)**: "All the logic and transformation is
  done in dbt. We could consume from the metrics using any frontend tooling.
  Transformations, logic must never happen in the frontend." Export/site may select,
  group, rename, format — never compute (no ranking, windows, perspective, affiliation,
  slugs, taxonomy). Test: deserves a DQ test, or must be byte-identical across two
  frontends? → dbt. See layering.md §Consumption layer; hook enforces at edit time.
- Metric governance = catalogue-only; display contract = `metrics_display.md` (rulings
  log inside). MVP row order is untouchable; new metrics slot into blocks.
- Astro static, hybrid IA, v2 reads SOURCE marts (never `mart_matchday_insights`),
  MVP stays live until cutover #377, home spec LAST.
- Blueprint workflow: markdown-only specs; gaps → register with proposed disposition,
  CPO rules at review; gap fixes never inside blueprint PRs.

## Do NOT
- **Do not compute anything in the frontend/export** (see contract above).
- **Do not invent/redefine metrics** — catalogue rows only, CPO approval first.
- **Do not touch the live MVP** (`site/`, `export_pages_data.py`,
  `pages-match-preview.yml`); GAP-17 explicitly parked for this reason.
- **Do not change existing season-rollup denominators** (GAP-17 pending ruling).
- Do not hardcode a competition above staging; `league_code` is the partition key.
- Branch from `main`; never commit to main; explicit-refspec push → PR; post-commit
  hook auto-pushes (if its `gh` step 401s, open the PR manually).

## Environment notes (this machine)
- dbt/sqlfluff from project `.venv`; local dbt works with no `--profiles-dir`.
- BQ is a SHARED single environment: ci-data-build rebuilds it from whichever branch
  built last — local builds get overwritten; re-deploy before BQ-based verification.
- `scripts/export_site_data.py` reads BQ via ADC; `--sample N`; output
  `artifacts/site_data/` (gitignored); pure helpers tested in
  `tests/test_export_site_data.py`.
