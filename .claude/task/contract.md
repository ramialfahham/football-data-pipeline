# Task contract — MR6 of the description-drift programme

objective: >
  Give dbt `description:` fields a reader, which is the root cause the whole programme exists to
  fix. Two changes: turn on `+persist_docs: {relation: true, columns: true}` so every description
  lands on the BigQuery table and column it describes, and publish `dbt docs generate` from CI so
  there is a browsable page.

  MR1-MR4 corrected the content and MR5 built the gate that keeps it correct. Neither gives the
  field a consumer. A field nobody reads has no feedback loop, which is why it became the cheapest
  place in the repo to dump narrative.

  It also unblocks #82 (MR7): a column that exists in BigQuery but is declared in no `.yml` is
  invisible to a YAML-based check, and catching it needs `target/catalog.json`, which exists only
  once `dbt docs generate` runs.

refs: >
  Authority: `.claude/task/escalations.log` — the 2026-08-20 programme entry (the CPO's diagnosis,
  the audit's numbers, the definition of a good description, the six-MR split and its ordering
  constraints), and THIS branch's 2026-08-21 entry, which records the CPO's protected-path
  approval. Plan file: `C:\Users\Rami\.claude\plans\cozy-orbiting-quail.md`; the programme plan is
  `jazzy-greeting-teacup.md`, Step 5.
  Branched from main `b378be5`. `!88` (MR5's second half) is OPEN — see decisions_reserved.

protected_override: >
  CPO, in chat 2026-08-21, verbatim "The docs only change when a model or a description changes,
  and that is exactly when this would fire. -> yes", recorded in `.claude/task/escalations.log`
  under `2026-08-21 feat/description-persist-docs` BEFORE this branch touched the file — GitLab #28
  is that an override can otherwise claim a ruling nobody can check.

  It authorises exactly ONE edit and nothing else: appending
  `dbt docs generate --static --target prod` plus an `artifacts:` block to the `data:build:main`
  job in `.gitlab-ci.yml`. No other change to that file, and no other protected path.
  The question put to him was BEHAVIOURAL — how often should the documentation rebuild — not a file
  path, because MR5's entry records that a path-shaped question failed three times running.

impact_map: >
  `persist_docs` changes the DDL dbt emits for EVERY model and EVERY seed, so the blast radius is
  the warehouse itself. This is the one MR in the programme that can break prod.

  1. BIGQUERY, WRITE PATH. dbt sets the relation description and each column description at build
     time. BigQuery HARD-REJECTS a column description over 1,024 characters and a relation
     description over 16,384; a rejection fails the model, and in `data:build:main` that fails the
     prod build. This is why MR6 is sequenced last.
     ⚠ RETIRED BY MEASUREMENT, not by assumption. Read off `target/manifest.json`, so the text is
     RENDERED and a docs block counts as what it resolves to rather than as its reference: 106
     relation descriptions, longest 601; 870 column descriptions, longest 588; zero over either
     limit; 9 of 9 docs blocks resolved. The measurement is deliberately independent of the gate,
     because the gate in main skips the length check on a bare `{{ doc() }}` reference.
  2. SEEDS, A NEW CONFIG BLOCK. There is no `seeds:` block in `dbt_project.yml` today. It must
     carry `+persist_docs` and NOTHING else — seeds have no `+schema` and ride `target.schema`
     (`macros/generate_schema_name.sql`), so adding one would silently relocate every seed, and in
     prod that is `dbt_analytics`.
  3. CI COST, ONE TIME. Changing `dbt_project.yml` changes every model's config, so `state:modified`
     should match all 97 models and this MR's `data:build:mr` will rebuild the whole `ci_*`
     warehouse once. Expected, and it is also what proves the model-column half of the verification.
     Confirm it from the job log rather than predicting it.
  4. CI COST, RECURRING. `dbt docs generate` runs a catalog query against BigQuery INFORMATION_SCHEMA
     once per push-to-main that touches `*data_paths_prod`. Metadata-sized. It is NOT added to
     `data:nightly` (the content comes from the repo, so a nightly re-publishes identical pages) and
     NOT to `data:build:mr` (its `ci_*` datasets hold only `state:modified+`, so the catalog would
     be partial and misleading).
  5. NOT TOUCHED: no model SQL, no seed CSV, no description text, no export, no site file. The
     numbers the pipeline produces are unchanged — only the metadata attached to them.

scope_paths:
  - dbt_project/dbt_project.yml
  - .gitlab-ci.yml
  # Added by amendment 1 — the pinning test platform-reviewer's round-1 FAIL was right about.
  - tests/test_persist_docs_policy.py
  - dbt_project/docs/engineering_standards.md
  - CLAUDE.md
  - .claude/task/contract.md
  - .claude/task/escalations.log
  - .claude/task/review.md
  - .claude/task/acceptance_evidence.md
  - .claude/active_work.md

decisions_taken: >
  CPO, 2026-08-20, approving "the whole plan" — all six MRs, with MR6 as `persist_docs` plus
  published docs.
  CPO, 2026-08-20, "Both" — turn on `persist_docs` AND publish `dbt docs generate` from CI, chosen
  over either alone or neither.
  CPO, 2026-08-21, the docs rebuild after each merge to main. See `protected_override`.

decisions_reserved:
  - #82 (MR7, the coverage gate) and #83 (the missing competition-classification dim) are NOT
    started here. #82 comes after MR6 because it needs this MR's `catalog.json`.
  - Whether `!88` merges before this MR is the CPO's, because he merges. The recommendation is
    recorded in `escalations.log` and in the handover: MR6 is what makes an over-long description
    build-breaking, and the gate in main is blind to a long shared docs block, which is exactly the
    hole `!88` closes. MR6 is safe either way — the measured over-limit count is zero — so this is
    a recommendation, not a blocker.
  - `snapshots:` is deliberately NOT given `persist_docs`. The block is dormant, dbt already
    reports it as an unused configuration path, and its own header instructs whoever lands the
    first snapshot to make it target-aware. Adding a key to a block that binds nothing would be
    speculative config. If the CPO wants uniformity instead, it is one line.
  - The two length bullets in `engineering_standards.md` §2 are NOT touched. `!88` rewrites exactly
    those lines; editing them here creates a conflict and buys nothing. MR6 adds a Readers note
    elsewhere in §2.

done_when:
  - `+persist_docs: {relation: true, columns: true}` set ONCE at the `models:
    football_data_pipeline:` level so it cascades to all five layers, not restated per layer.
  - A new top-level `seeds:` block carrying `+persist_docs` and nothing else. No `+schema`.
  - `dbt docs generate --static --target prod` plus an `artifacts:` block on `data:build:main`
    only, with no `allow_failure`.
  - PROVEN ON A DEV TARGET, never `dbt build` against prod: `dbt seed --select competition_types
    --target dev` then `bq show --schema` shows the relation description and all 5 column
    descriptions. (`competition_types` is a SEED — `dbt run` selects nothing and exits 0, which is
    the false-green the brief's own recipe would have produced.)
  - The models half proven too: `dbt run --select stg_apif__leagues --target dev` then `bq show`.
    Model COLUMN descriptions cannot be proven locally — no staging model has one (0 of 15,
    measured) and every model that does needs the whole chain in dev — so they are proven off this
    MR's own `ci_*` build, read from the log.
  - `dbt docs generate --static --target dev` produces `static_index.html` and a non-empty
    `catalog.json`.
  - THE HAZARD IS SEEN RED. Push one description past 1,024 characters, watch BigQuery reject it,
    revert. A passing check proves nothing (#904) — this is the repo's dominant failure.
  - `python -m pytest tests/` green at its measured baseline; the offline gates pass, read from
    their OUTPUT not their exit code.
  - Handover updated in the SAME commit as the code.
  - Added by amendment 1: `tests/test_persist_docs_policy.py` pins every invariant this MR
    establishes, and is SEEN RED per invariant before being trusted.

amendments:
  - >
    1. A PINNING TEST ADDED, because platform-reviewer FAILed round 1 and was right.
    THE FINDING: nothing in `tests/` referenced `persist_docs`, `docs generate`, `catalog.json` or
    `static_index` — verified, the grep returns zero files. So every invariant this MR establishes
    could be reverted with the whole suite still green: deleting `+persist_docs`, adding a
    `+schema` to the new `seeds:` block (the silent-relocation hazard the file's own comment warns
    about), removing the docs step, moving it to `data:nightly` or `data:build:mr` (both
    explicitly rejected by the CPO's override), or restoring `allow_failure`.
    WHY IT LANDS RATHER THAN BEING ARGUED WITH: this is the exact class
    `tests/test_materialisation_policy.py` and `tests/test_ci_data_job_invariants.py` already
    exist for, on the SAME two files, and both open by saying breaking them produces no red
    anywhere. The programme's own founding measurement is that 33 of 50 corrections were
    prose-only and 22 recurred, while every rule that got a machine check stopped recurring. A
    config change defended only by hand-run commands pasted into an evidence file is a prose-only
    correction wearing a lab coat.
    The original `done_when` list omitted a pinning test with no stated reason. That omission was
    the defect, not an accepted trade-off.
  - >
    2. NOT AN AMENDMENT TO SCOPE — a correction to platform-reviewer's SECOND finding, recorded
    because the correction is the useful part and the reviewer should see it.
    THE FINDING: `static_index.html` was measured at 6.6 MB against a dev catalog of 10 nodes / 78
    columns, while production is 106 relations / 870 declared columns, so the evidence measured
    something ~10x smaller than what will really be produced.
    THE PREMISE IS WRONG, and this is measured. `target/manifest.json` is 5,085,350 bytes and
    already contains ALL 97 models and 9 seeds — a manifest is a parse artifact and does not
    depend on what was BUILT, so the dominant JSON embedded in `static_index.html` was already at
    full production scale in that dev run. The dbt docs SPA bundle is a fixed cost. Only the
    catalog portion scales, at 47,511 bytes across 112 catalogued columns (78 in nodes + 34 in
    sources) — **~424 bytes per column**.
    ⚠ AN EARLIER DRAFT OF THIS AMENDMENT SAID ~609 bytes/column, dividing by the 78 node columns
    while the file also holds 34 source columns. Wrong denominator, and it disagreed with the
    figure in `acceptance_evidence.md`. Caught by platform-reviewer in round 2, which noticed the
    two artifacts quoting different rates for one measurement. It is recorded rather than quietly
    overwritten because it is the SAME defect MR5 shipped — three numbers across three artifacts
    for one decision — committed again inside the programme built to stop it. The conclusion was
    never rate-sensitive (both rates land two orders of magnitude under the limit), which is
    exactly why it survived a first reading.
    THE FAIR HALF OF THE FINDING STANDS: no estimate and no artifact-limit check existed anywhere
    on the branch. Both are now in `acceptance_evidence.md`.
