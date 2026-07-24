# Review — feat/site-v2-real-data — 2026-07-24

diff_sha256: c60b8b89d7cc87971d42ad8a612588f6474aed9db927205f992c2a57fb1a4d76

rounds: 1

> Wire the v2 build to consume the real export: team + fixture `getStaticPaths` enumerate
> `src/data/{teams,fixtures}/*.json` via `import.meta.glob` (one page per file); the export emits a
> full registry-derived `competitions.json` (committed, 45 leagues); `.gitignore` keeps the two
> samples and ignores the bulk (populated at build time, never committed). Player+competition pages
> (undesigned) and the export->build->deploy automation (blocked on hosting) are OUT (CPO-approved plan).
> Verified: dev/PR build 9 pages (samples only); a raised-heap full build produced 14,874 pages across
> 26 leagues; all 4498 exported fixtures resolve their competition slug (no throw). Default-heap OOM is
> a documented deploy-time ceiling. All four required reviewers PASS. The one shared non-blocking note
> (stale site_v2/src/data/README.md) is a fast-follow (chipped), not gating.

## scope-auditor
VERDICT: PASS
risks_checked:
- Every changed file is within scope_paths (pages via the `site_v2/src/pages/` prefix, competitions.json,
  export, tests, .gitignore, contract); no out-of-scope edit; impact_map honest (writers: NONE, no
  warehouse/dbt/BigQuery change).
- No §10 decision made unilaterally: the deferred deploy automation + undesigned pages are explicit
  contract scope boundaries; the full competitions map is a registry passthrough, not a new product
  decision; the OOM-deferred-to-deploy is a phase boundary, not a dodge.

## analytics-engineer-reviewer
VERDICT: PASS
risks_checked:
- `_competitions_index` is a literal registry passthrough (selects authored name+slug via
  `_registry_competitions`, no `slugify()`/derivation), identical in shape to the pre-existing
  leaderboards `meta` dict — A5 compliant, not identity generation.
- The committed competitions.json is byte-consistent with the export's `_payload_bytes` output (2-space
  indent, ensure_ascii=False, no trailing newline, registry insertion order) and matches the live
  registry 45/45 by hand spot-check — real output, binding rule holds. No new BigQuery / query cost
  (registry-only). The frontend change is enumeration + key lookup, no derivation.

## bi-analyst-reviewer
VERDICT: PASS
risks_checked:
- Binding rule: zero new rendered fields — the page templates are byte-identical below the frontmatter;
  only getStaticPaths + its import changed. competitions.json is real registry output; the fixture
  slug lookup + team compName lookup resolve for every league (superset by construction: team/fixture
  data only exists for registry leagues; `_registry_competitions` is unfiltered).
- No missing-league gap (spot-checked 8 real bulk files across CDF/UEL/CAFCL/MLS/BSA/PL — all resolve);
  dev/PR build unchanged (9 pages, samples only; no other component hardcodes a sample or globs);
  full-scale arithmetic consistent (459x3 + 4498x3 + 3 = 14,874). README staleness NON-BLOCKING.

## cto-reviewer
VERDICT: PASS
risks_checked:
- `import.meta.glob({eager,import:"default"})` inside getStaticPaths is the sound Astro/Vite pattern
  (Vite rewrites the literal glob wherever it appears; the module-level attempt failed for scope);
  root-relative `/src/data/...` resolves; strict tsconfig has the ambient types.
- `.gitignore` negations keep exactly the two samples tracked and ignore the bulk (flat dirs, every
  filename is `<int>.json`, no conflicting broader pattern) — no bulk in the commit (full patch read),
  no repo-size risk. OOM correctly scoped OUT: nothing auto-deploys today, ci-site-v2 (unchanged) only
  asserts the 4 locale roots, and the failure mode is a fail-closed build crash, not a bad deploy;
  the raised-heap requirement belongs to the deferred deploy automation.

## escalations
- question: does "wire the real data" include the export->build->deploy CI automation and the
  full-scale build memory fix? CPO ANSWER: no — the CPO-approved plan (ExitPlanMode 2026-07-24) scopes
  those to the hosting decision (group 3); this PR makes the build READY to consume real data, not
  deployed. The default-heap OOM is a deploy-build concern (raise NODE_OPTIONS or long-tail on-demand),
  recorded in decisions_reserved.

## follow-ups (non-blocking)
- site_v2/src/data/README.md is stale (says one committed sample / featured-competition-only); update
  to the real-data setup. Flagged by cto + analytics + bi-analyst as non-blocking; chipped as a fast-follow.
