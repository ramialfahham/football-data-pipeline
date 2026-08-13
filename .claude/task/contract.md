# Task contract — #33 item 15: stop ingesting /injuries

objective: >
  `RAW_APIF_INJURIES` is the **LARGEST raw table at 1.975 GiB** (raw totals 5.35 GiB) and
  **nothing reads it**: no `sources.yml` declaration, no dbt model, no script, no export. It is
  written every night for no consumer.

  This removes the ingest — the loader, its phase in the competition runner, its tests, and its
  entries in the data contract. It does NOT delete the BigQuery table; that is a separate,
  confirmed action after merge (see `done_when`).

  ⚠ THIS ENDPOINT WAS ALREADY REMOVED ONCE FOR THIS EXACT REASON AND CAME BACK — `401c1cc`
  (2026-05-10) removed it because it "had no consumer downstream"; `983d12c` (2026-05-26)
  re-added it sixteen days later naming no consumer. Recorded in `escalations.log`; the loop is
  the reason this contract states what would make the removal wrong.
refs: >
  GitLab #33 item 15. CPO ruling "yes" (2026-08-12) and the premise check (2026-08-13) are both
  in `.claude/task/escalations.log`.

scope_paths:
  - ingestion/api_football/loads/injuries.py
  - ingestion/api_football/loads/competition_runner.py
  - ingestion/api_football/http_client.py
  - tests/test_injuries_coaches.py
  - tests/test_coaches.py
  - tests/test_incomplete_fetch_no_supersede.py
  - docs/data_contract.md
  - scripts/drop_injuries_raw_tables.py
  - .claude/task/contract.md
  - .claude/task/escalations.log
  - .claude/task/review.md
  - .claude/task/review_input.patch

impact_map: >
  REQUIRED — `ingestion/**` is the structural surface, and a raw writer is being removed.

  writers: `ingestion/api_football/loads/injuries.py::load_injuries` is the ONLY writer of
    `RAW_APIF_INJURIES`, called from exactly one place —
    `loads/competition_runner.py:126-127`, inside `run_cheap_phases`.

  readers: **NONE, and this is the whole basis of the change.**
    · `grep -n "injuries" dbt_project/models/1_staging/api_football/sources.yml` -> no match, so
      there is no dbt source node and nothing downstream can `ref()` it.
    · The only `injur` hits anywhere under `dbt_project/models/**` are `has_coverage_injuries` in
      `stg_apif__leagues.sql:88`, `base_apif__leagues.sql:23,62` and
      `dim_competition_season.sql:25`. That column is parsed from the **`/leagues`** payload
      (`$.coverage.injuries`) and is UNRELATED to `RAW_APIF_INJURIES`. ⚠ It MUST survive this
      change untouched — removing it would break `dim_competition_season`.
    · No `scripts/export_*.py` and no `site_v2` file mentions injuries.

  downstream: there is no lineage to trace, because there is no source node — nothing to run
    `dbt ls` against. That absence IS the evidence, and it is why this removal is safe in a way
    dropping a consumed table would not be.

  layer_rules: none engaged. No model file is touched, so `check_layer_contract.py` has nothing
    to judge. `sources.yml` is not edited because the table was never declared there.

  deploy_order: nothing breaks at any point — the nightly simply stops calling one endpoint. No
    backfill, no `--full-refresh`, no migration ordering. ⚠ THE NIGHTLY RUNS AN IMAGE, so merging
    does not deploy this; it needs
    `gcloud run jobs deploy fdp-nightly --source . --region europe-west1` from `main`.

  blast_radius: **no number in any mart, model or page changes**, because nothing consumes the
    table. What changes is the nightly: measured on the 2026-08-13 run, the injuries phase ran
    for 26 competitions at ~9s each — roughly 4 minutes — at one API call per competition per
    season.

decisions_taken: >
  CPO ruling, in-thread 2026-08-12: **"yes"**, to "Shall I do both — item 9 + 10 as planned, and
  drop `/injuries` as a second task?" Recorded in `escalations.log` before this contract, along
  with the 2026-08-13 premise check.

  THE PREMISE CHECK CHANGED WHAT IS KNOWN WITHOUT CHANGING THE RULING. `/injuries` was removed on
  2026-05-10 for having no consumer and re-added on 2026-05-26 with none stated. Coaches, added in
  the same commit, DID get a consumer (`dim_coach`); injuries is the half that never did. That
  makes this a correctly-removed endpoint that came back unexplained, rather than a feature
  awaiting a downstream build — which is the reading that would have made removal wrong.

  # THRESHOLD DECLARATIONS
  RECURRING COST — **reduces, on three axes, all measured**: 1.975 GiB of BigQuery storage once
    the table is dropped (the largest single raw table); ~4 minutes of the nightly; and one API
    call per competition per season against a daily quota.
  NEW MECHANISM — no. Code and docs are removed; nothing is introduced.
  GUARD LOOSENED — **no**, and the distinction matters: `TestLoadInjuries` is deleted, but a test
    whose subject no longer exists is not a guard. No assertion about surviving behaviour is
    weakened, and `TestLoadCoaches` is preserved in full.
  SHIPPED NUMBERS — no. Nothing reads the table.

decisions_reserved:
  - Whether `/injuries` should ever be ingested again. If a player-availability surface is
    planned, this removal is the wrong call and the CPO should say so — the endpoint would then
    be left alone rather than removed and re-added a third time. Searched: no open issue names
    injuries as a consumer, and the player-page design (#753) does not reference it.
  - Deleting the `RAW_APIF_INJURIES` table itself. Covered in principle by the same ruling but
    deliberately NOT in this diff: it is irreversible past BigQuery's 7-day time travel, so it is
    a separate confirmed action after merge.
  - The nine legacy `RAW_WC26_APIF_*` tables (1 row each, untouched since 2026-05-24) are a
    different cleanup and are not touched here.

done_when:
  - `ingestion/api_football/loads/injuries.py` is deleted, and a repo sweep finds no surviving
    reference to it or to `RAW_APIF_INJURIES` outside deliberate history.
  - `pytest tests/ -q` exits 0 (baseline on this branch's base, main @ 557a26a: 798 passed,
    1 skipped).
  - `ruff --config .ruff-ci.toml ingestion/ tests/ scripts/` exits 0.
  - ⚠ VERIFIED BY RUNNING, not by reading: the competition runner still executes its remaining
    phases in order with the injuries phase gone, and `run_cheap_phases`' docstring phase list is
    checked against the code so the two cannot disagree.
  - ⚠ `has_coverage_injuries` survives untouched in all three models. It is the one thing in the
    repo whose name matches and MUST NOT be removed; asserted by grep and by the full suite.
  - `docs/data_contract.md` no longer declares `RAW_APIF_INJURIES` in any of its four places.
  - POST-MERGE, and NOT satisfiable from this branch: redeploy the nightly image from `main`,
    confirm the next run logs no `phase=injuries`, then run
    `python scripts/drop_injuries_raw_tables.py --dry-run` and perform the real drop only after
    the CPO confirms the listed tables.

amendments: (none)
