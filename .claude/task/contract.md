# Task contract — wire the v2 build to consume the real export

> Written on a CLEAN tree (branch `feat/site-v2-real-data` off main at f586457, after PR-B merged).
> Plan: C:\Users\Rami\.claude\plans\deep-puzzling-conway.md (CPO-approved via ExitPlanMode 2026-07-24).

objective: >
  Make the v2 build generate a page for EVERY team and EVERY fixture from real export output, instead
  of one committed sample per page, and resolve competition slugs across ALL active leagues. Launch
  group 2 ("real data"), decision-independent. Player + competition pages (undesigned, group 1) and the
  export->build->deploy automation (blocked on the hosting vendor, group 3) are OUT.

refs: >
  Plan file above. Verified this session (Explore map): only team + fixture pages exist, each hardwired
  to one imported sample via `getStaticPaths`; no enumeration primitive; `competitions.json` is a
  hand-trimmed 2-entry stand-in; the export already writes the full per-entity layout but nothing
  consumes it and its output is gitignored (committing the full export is not viable, >100s MB). The
  registry carries slug+name per league; the export already builds the `league_code -> {slug, name}`
  shape at `scripts/export_site_data.py:992` via `_registry_competitions()` (registry-only, no BigQuery).

scope_paths:
  # trailing-slash prefix: the page files live under bracketed [lang]/[team] dirs, which fnmatch
  # would read as char-classes — the prefix form matches them. Only the team + fixture pages change.
  - site_v2/src/pages/
  - site_v2/src/data/competitions.json
  - scripts/export_site_data.py
  - tests/test_export_site_data.py
  - .gitignore
  - .claude/active_work.md

impact_map: >
  writers: NONE. No warehouse/dbt/seed change. `export_site_data.py` gains a registry-only
    `competitions.json` emit in `export_all` (reuses `_registry_competitions()`, no new BigQuery query).
  downstream: the static site build only. The two page `getStaticPaths` switch from a single-file import
    to `import.meta.glob('/src/data/{teams,fixtures}/*.json', {eager:true})` — one page per file present.
    `competitions.json` becomes the full registry map, consumed by the fixture page + TeamHeader.astro
    via the existing `competitions[league_code].slug` lookup (now covering all leagues). No consumer
    breaks: with only the committed samples present (dev/PR), the build produces the same team + fixture
    pages as today.
  layer_rules: consumption layer (Appendix A5) — select/enumerate/route only, no fact derived. The
    export's competitions.json is a registry passthrough (slug+name), not a computed fact.
  deploy_order: none. Nothing is deployed (hosting undecided). The full export is generated at build
    time and NOT committed (gitignored bulk with sample exceptions), so the repo stays small.
  blast_radius: bounded / build-time only. Additive enumeration + a fuller competitions map + gitignore
    patterns. No warehouse object, no runtime service. The committed tree still holds only the two
    samples + the (tiny) full competitions.json.

decisions_taken: >
  (1) Enumerate via `import.meta.glob` (Astro-idiomatic, no fs); each entity's own `.slug` stays the
      URL param (unchanged pattern). CPO-approved plan.
  (2) The full competitions map is registry-derived and emitted by the export (reusing
      `_registry_competitions()`); committed because it is tiny (~14 leagues).
  (3) The bulk team/fixture JSON is gitignored (sample exceptions kept) — the build consumes real data
      generated at build time; the repo never carries the full export.
  (4) Deploy automation is deferred to the hosting decision; this PR makes the build READY, not deployed.

decisions_reserved:
  - Where the export runs in CI and where the site deploys — waits on the hosting vendor (group 3).
  - Player + competition pages wait on their designs (group 1).
  - Build memory/time at full scale (eager glob) — acceptable for team+fixture counts; the long-tail
    on-demand optimisation is a later hosting-time concern.

done_when:
  - Both pages enumerate all `src/data/{teams,fixtures}/*.json` via `import.meta.glob`; each generates
    one page per file x 3 locales; the fixture page resolves its competition slug from the full map.
  - `competitions.json` is the full registry-derived `league_code -> {slug, name}` map; the export emits
    it in `export_all`; a `tests/test_export_site_data.py` case covers the emit.
  - `.gitignore` ignores the bulk team/fixture JSON, keeps `teams/33.json` + `fixtures/1492306.json`.
  - Verified at scale: a real export (>= one full competition + a multi-league spot set) generated into
    `src/data/`, `astro build` clean in de/en/fi with a page per team + per fixture, spot-checked; then
    `src/data/` reverted to the committed samples (bulk NOT committed). Dev/PR build (samples only) still
    produces the team + fixture pages.
  - `pytest tests/test_export_site_data.py` green; `validate-local` Tier 1.
  - ONE commit, pushed with an explicit refspec, PR opened. The CPO merges.

amendments: (none)
