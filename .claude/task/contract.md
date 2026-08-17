# Task contract — #62 step 4: repoint the export at mart_competition_index

objective: >
  Give the competitions index page (#54, not yet built) a real, mart-backed JSON export. Add a new
  `fetch_competition_index()`/`shape_competition_index()` pair to `scripts/export_site_data.py`
  that queries `mart_competition_index` (live in prod since !65) and writes `competition_index.json`
  under a new `"competition_index"` entity type. This is #62 step 4; step 5 (the Astro page, its
  page-spec, the nav-item anchor swap) is a separate, later MR.
refs: GitLab #62 (step 4 of 5), #54 (page design), MR !65 (the mart, merged), MR !66 (a doc fix,
  merged)

scope_paths:
  - scripts/export_site_data.py
  - tests/test_export_site_data.py
  - docs/site_architecture.md
  - .claude/active_work.md

impact_map: >
  writers: `mart_competition_index` (read-only SELECT, no write) is built by `data:build:main`/
    `data:build:mr` from the model merged in !65. `scripts/export_site_data.py` itself is invoked
    two ways: `.gitlab-ci.yml:767` and `.github/workflows/deploy-site-v2.yml:65`, both
    `python scripts/export_site_data.py --entities teams,fixtures --out site_v2/src/data` — an
    EXPLICIT entities list that does not include "nav", "landing", "competitions" or any other
    existing entity type either. Adding `"competition_index"` to `ENTITY_TYPES` does not change
    what either CI job runs; the new path stays dormant until something explicitly asks for it via
    `--entities`. Local/manual invocation (`python scripts/export_site_data.py` with no
    `--entities` flag, or `main()`'s own default) DOES pick up every entry in `ENTITY_TYPES`,
    including the new one.

  downstream: NONE today. `grep -rn "competition_index" site_v2/src` returns zero hits — no Astro
    page, component or spec reads this file yet, because step 5 (the page that would) is not built.
    `competition_index.json` is a new, additive output; nothing existing reads it, and nothing
    existing stops reading anything it read before.

  layer_rules: this is the consumption layer (`scripts/export_*.py`), not a dbt model — no
    `check_layer_contract.py` surface. The new `shape_competition_index()` does select/project
    only (a keep-list, mirroring `shape_leaderboards`' `_LB_KEEP` pattern at
    `export_site_data.py:51-55`) — no ranking, no joining, no derived field, consistent with the
    repo's own audit findings (`docs/audits/2026-06_alignment_audit.md` F4/F6/F7) about what NOT to
    do in this file. `fetch_competition_index()` adds one `order by league_code` for a
    deterministic export diff, explicitly NOT the page's display order (`escalations.log`,
    2026-08-16: the mart carries facts, the page spec declares the ORDER BY) — a comment states
    this so step 5 doesn't mistake it for the real sort.

  deploy_order: none. This is a script change with no BigQuery write and no CI wiring change (see
    writers above) — nothing about existing deploys is affected. The new function can be verified
    by running it directly against prod (read-only SELECT, priced at 10,067 bytes) without going
    through CI at all.

  blast_radius: additive only. `ENTITY_TYPES` gains one new string; every existing entity type's
    code is untouched. `_registry_competitions()`, `fetch_nav()`/`build_nav()`, `_competitions_index()`
    (the small `{league_code: {name, slug}}` lookup feeding the fixture page and `TeamHeader.astro`),
    and `fetch_competition_payloads()` (the unrelated `"competitions"` entity type, per-league-season
    detail payloads for #47) are all read-only reference points for this task and are NOT modified.

decisions_taken: >
  This wires a mart the CPO already approved (!65) into the export layer using the file's own
  established pattern (a `shape_*` pure function + a `fetch_*` BigQuery function + one block in
  `export_all()`) — no new mechanism, no new CPO decision. The ordering stance (mart/export carry
  facts, page spec carries the ORDER BY) is the CPO ruling already recorded in `escalations.log`,
  2026-08-16 — restated here as an implementation constraint, not re-decided.
  NEW MECHANISM: none. RECURRING COST: none — one more `SELECT` against a 48-row table in a script
  that already runs.

decisions_reserved:
  - Whether/when `.gitlab-ci.yml`/`deploy-site-v2.yml`'s explicit `--entities teams,fixtures` list
    grows to include `competition_index` is deliberately NOT decided here — that is step 5's
    concern, when a page actually consumes the file. Wiring it into CI now would commit a file
    nothing reads.

done_when:
  - `shape_competition_index()` has a passing unit test (no BigQuery) mirroring
    `test_shape_leaderboards_groups_by_metric_key_and_orders_by_rank`'s pattern.
  - `python scripts/export_site_data.py --entities competition_index --out artifacts/site_data` run
    for real against prod (priced first) produces `competition_index.json` with all 48 competitions,
    the expected keys, and a resolved `region_label_en` on both a domestic and an international row.
  - `ruff` clean on the changed Python files.
  - Full `pytest` run stays green (no regression from the `ENTITY_TYPES` tuple change).
  - `docs/site_architecture.md`'s competitions-index row names `competition_index.json` /
    `mart_competition_index` instead of the stale `nav.json` claim.
  - `.claude/active_work.md` updated in the same commit, under 16,000 characters.

amendments: (none)
