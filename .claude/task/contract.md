# Task contract — page-spec contract (#826)

> Written on a CLEAN tree, branch `feat/826-page-spec-contract` off `main` (`a05c342`).
> See docs/working_agreement.md §2 (contract), §10 (decision rights), §11 (blinded escalation).

objective: >
  Each site_v2 page template declares a spec (its blocks, the mart each block reads, its i18n
  label keys) in a small JSON file, checked against a hand-written JSON Schema by a plain-Node
  checker wired into `npm run build` via `prebuild` — so the build refuses to proceed if a real
  page has no spec, or its spec names a mart or i18n key that does not actually exist. Issue #826,
  Phase B of the foundation-first plan (after #825 shell, #827 reviewer).

refs: >
  Issue #826 (CPO-authored, 2026-07-26): "Each page declares a spec (its blocks, the mart each
  block reads, its i18n label keys), validated by a schema so CI refuses to build an
  underspecified page. Sits on top of docs/content_architecture.md (the existing block-to-mart
  map) and the metric display contract." active_work.md's own scoping: "add ONLY a schema-
  validated page-spec contract... right-sized, NO autonomy" (adapted from the backtobayesics
  study, which itself oversold — 2 of ~50 pages actually built there). Design pressure-tested via
  a Plan sub-agent this session, then independently verified: `.github/workflows/**` is a
  hook-protected path (`.claude/hooks/task_contract_gate.py` line 66) and `site_v2/` is
  structural surface (line 88); `zod`/`zod-to-json-schema` exist in `site_v2/node_modules/` only
  as `astro`'s own transitive dependency (`package-lock.json` lines 1817-1819), not declared in
  `site_v2/package.json` — confirmed by reading both files directly.

scope_paths:
  - site_v2/src/specs/**
  - site_v2/scripts/**
  - site_v2/package.json
  - docs/content_architecture.md

impact_map: >
  Leaf/cosmetic short-form (site_v2/ is structural surface by path prefix, but this diff carries
  no dbt/warehouse read or write, no export-script change, no shipped-page-component change): adds
  two new leaf JSON spec files, one JSON Schema doc, one plain-Node checker script + its test
  suite (reads `dbt_project/models/5_marts/**/mart_*.sql` filenames for existence only — never
  parses or queries them), and a one-line `package.json` `prebuild` addition, plus a short doc-sync
  paragraph in `docs/content_architecture.md`. Blast radius: `npm run build` (both `ci-site-v2.yml`
  and the real `deploy-site-v2.yml`, since both invoke exactly `npm run build`, which auto-runs
  `prebuild`) gains a pre-build gate. A page whose spec is present and correct is completely
  unaffected — the two pages that exist today (team, fixture) get specs written in this same PR,
  verified green. A future page added WITHOUT a spec fails the build with a named error — the
  intended behavior, not a regression. No `.github/workflows/**` edit (protected, and unnecessary
  — `prebuild` covers both real build paths already).

decisions_taken: >
  Specs live under `site_v2/src/specs/` (not top-level `site_v2/specs/` or inside `src/pages/`) —
  `.claude/review_routing.json`'s own comment anticipates this ("bi-analyst-reviewer routes to ALL
  of site_v2/src/**... as well as the specs", CPO ruling 2026-07-22); Astro treats non-page files
  under `src/pages/` as endpoint candidates, so co-locating there would break the build (verified
  against `site_v2/node_modules/astro/dist/core/build/*.js`). Validation is hand-rolled plain
  Node/ESM, not a schema-validator library (`ajv`/`zod`) — the two checks that matter (mart file
  existence, i18n key existence) are cross-repo-reference checks no library performs anyway; the
  part a library would help with (shape/type checking) is four lines by hand; importing the
  `zod` already resolvable via `astro`'s own node_modules would be an undeclared phantom
  dependency, not a real saving. The i18n check is deliberately loose (a *listed* key must exist;
  a page need not exhaustively list every key its components use) — the exhaustive-completeness
  question is #827's job (rendered-page review), not CI's; CI is the cheap always-on mechanical
  floor against fabricated/renamed/removed keys. Block names are taken verbatim from
  `docs/content_architecture.md` §3's existing "Block" column — no new vocabulary introduced.
  The checker does not load/parse `page-spec.schema.json` at runtime (round-1 cto-reviewer finding
  — the objective's wording previously implied it did); the schema file is authoritative
  documentation + editor autocomplete, kept from silently diverging from the hand-rolled checker
  by an automated cross-check test (`check-page-specs.test.mjs`), not by loading it in the hot
  path. Round-1 bi-analyst-reviewer finding fixed: `fixture.spec.json`'s "Single fixture" block
  was mislabeled — `mart_team_momentum_window` is the "Form (recent)" drill-down mart per
  `content_architecture.md` row 73 ("+ `_window` drill-down"), not a real "Single fixture"
  (`mart_team_fixture_stats`/`mart_player_fixture_stats`) capability, which
  `RecentMatch.astro`'s own comment confirms is not built on this page ("the matchstats drill-down
  page isn't built"); the fabricated block is removed, its mart folded into "Form (recent)" where
  the doc actually locks it.

decisions_reserved:
  - None new. This is mechanical scaffolding matching #826's own stated scope.

done_when:
  - `cd site_v2 && npm run build` succeeds with both real specs (team, fixture) present and
    correct; `dist/index.html` + `dist/{de,en,fi}/index.html` exist.
  - `node --test scripts` (wired into `prebuild`) passes: unit coverage on `specPathFor`,
    `extractKeysFromEnBlock` (including the packed-multi-key-per-line regression), `validateSpec`
    (good spec, missing field, bad entity, bad mart, bad i18n key, multi-violation aggregation),
    and the schema/checker cross-check.
  - Deliberately broken in turn and confirmed to fail with a specific, correctly-attributed error,
    then restored to green: (a) a missing spec file, (b) a spec naming a nonexistent mart, (c) a
    spec naming a nonexistent i18n key. Multiple simultaneous violations are all reported in one
    run, not just the first.
  - The placeholder `site_v2/src/pages/[lang]/index.astro` is confirmed NOT required to have a
    spec (it does not import Layout.astro).
  - Review cycle: scope-auditor (always) + cto-reviewer (`site_v2/**`) + bi-analyst-reviewer
    (`site_v2/src/**`, its own routed territory per the 2026-07-22 ruling).
  - ONE commit; review.md hash-locked; pushed with an explicit refspec; PR opened referencing
    #826. CPO merges; I close #826 myself once merged confirmed via `gh`.

amendments:
  - 2026-07-26 (clean-tree stash-dance, mid round-1 review response): scope_paths widened from the
    literal `site_v2/scripts/check-page-specs.mjs` to `site_v2/scripts/**` — authority: cto-
    reviewer's own round-1 finding requiring a persisted automated test
    (`check-page-specs.test.mjs`) for the checker, which the literal single-file scope_paths did
    not cover.
