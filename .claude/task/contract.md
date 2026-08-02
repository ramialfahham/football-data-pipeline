# Task contract — prune the latest-payload read (#890)

> Written on a clean tree before any file was touched. Branch `fix/890-prune-latest-payload-read`
> from `main` at `4899025`. No protected path in scope, so no `protected_override`.
> `ingestion/**` is the structural surface, so `impact_map` is required and present.
> No `site_v2/src/` path in scope, so no `acceptance_criteria`.

objective: >
  `read_latest_payload_json` returns ONE row and scans the entire history of the raw table to do it.
  The raw tables are partitioned by `ingested_at` and clustered by `league_code`, so the league
  filter prunes correctly, but `ORDER BY ingested_at DESC LIMIT 1` cannot prune partitions: to rank
  rows BigQuery must read every partition, on the widest column in the warehouse.

  Measured by dry run (free, exact) against `RAW_APIF_TRANSFERS`, league BL1:
    current  `SELECT payload ... ORDER BY ingested_at DESC LIMIT 1`      -> **6.634 GiB**
    step 1   `SELECT MAX(ingested_at) ... WHERE league_code = @lc`       -> **0.013 MiB**
    step 2   `SELECT payload ... AND ingested_at = @ts`                  -> **2.95 MiB**
    total after the fix                                                   -> **2.96 MiB**
  A **2,290x** reduction per call, and there are ~10,300 such calls per 35 days ($21.47, the single
  largest line in the bill).

  The cost also grows with UPTIME rather than with data: one more partition exists every day the
  pipeline runs, so this query gets permanently more expensive even if nothing new is ingested.

refs: >
  #890. Sibling of #892 (the same defect in the dbt staging models) and part of the #547 program.
  NOT in this task: #892, and the `1_staging` models generally.

scope_paths:
  - ingestion/api_football/bigquery.py
  - tests/test_latest_payload_read.py

impact_map: >
  writers: none. This is a READ path; nothing about what is ingested or stored changes.

  downstream: 5 call sites, enumerated with grep rather than from memory —
    `ingestion/api_football/completeness.py:125,192`
    `ingestion/api_football/ingest_plan.py:113,125`
    `ingestion/api_football/loads/fixtures.py:117`
    `scripts/compare_fixture_statistics_live.py:41`
  plus `tests/test_fixtures_cache_skip.py`, which monkeypatches the name at 101 and 175 and
  therefore does not exercise the query at all. Every caller wants "the newest payload for this
  league" and none inspects the SQL, so the contract they depend on is the RETURN VALUE, which is
  unchanged.

  layer_rules: this is ingestion, not dbt, so `check_layer_contract.py` does not apply. The raw
  landing contract (`docs/data_contract.md`) is untouched: no table, column, schema or write path
  changes.

  deploy_order: none. A read-only change with no migration; the next nightly picks it up. It cannot
  half-apply, because it is one function.

  blast_radius: the VALUE returned must be identical, and that is the whole risk. Two behaviours
  must be preserved exactly: (1) a table with no rows for the league returns None, and (2) where
  several rows share the newest timestamp, one payload is returned rather than an error. What
  changes is only how many bytes BigQuery reads to find it. The failure mode if the timestamp
  lookup and the payload read disagree is a returned None where a payload exists, which would make
  the ingest re-fetch from the API rather than reuse the cache — visible as extra API calls, not as
  wrong data.

decisions_taken: >
  **AUTHORITY. CPO, 2026-08-02, in session: "merged, do 890"** — a direct instruction to do this
  issue, given after merging #891. It sits under the standing ruling that opened the cost work,
  **"Fix it and ensure that this will not happen again in the future."** Both are in
  `escalations.log`; the second was recorded with #547 and the first is appended with this task.

  **Why this is agent-executable rather than a §10 cost decision.** §10 reserves "cost, schedule,
  scope: API budget, history depth, run cadence, widening a task". This changes none of them. It
  does not touch what is ingested, how often, or how much history; it makes one existing read scan
  fewer bytes for an identical result. The RECURRING COST declaration below is NEGATIVE, and it is
  declared so `cto-reviewer` can see it, not because a reduction needs approval. Stating this
  plainly because the first version of this contract declared the threshold and named no authority
  at all, which `scope-auditor` correctly failed.

  Two round trips rather than one query, and that is measured, not stylistic. The single-query form
  `WHERE ingested_at = (SELECT MAX(ingested_at) ...)` was dry-run and scans the **same 6.634 GiB**:
  BigQuery does not prune partitions on a subquery predicate. So the two-step read is the only shape
  that actually prunes, and the first step costs 13 KB.

  The SQL moves from f-string interpolation to query PARAMETERS. The timestamp has to be a parameter
  for the fix, and leaving `league_code` interpolated in the same rewritten statement would be worse
  than fixing it; league codes come from the registry rather than user input, so this is hardening
  in a line already being rewritten, not a new concern.

  THRESHOLD DECLARATIONS. NEW MECHANISM: none. No new dependency, service, table or workflow step;
  the same client issues one extra small query. RECURRING COST: **strongly negative, and measured
  rather than asserted** — 6.634 GiB to 2.96 MiB per call, on ~10,300 calls per 35 days. Figures
  from `bq query --dry_run`, which bills nothing, and reproducible with `scripts/report_bq_cost.py`.

decisions_reserved:
  - Whether the same two-step shape should be pushed into the dbt staging models is #892, decided
    there. The classes differ: some raw tables are skip-if-present accumulations whose staging MUST
    read every snapshot, and pruning those would silently drop entities.
  - Nothing else is open. The return contract is unchanged, so no caller has to be consulted.

done_when:
  - `python -m pytest tests/test_latest_payload_read.py` passes, covering: the pruned two-step path,
    the empty-table None, the `ingested_datetime` variant, the no-timestamp-column fallback, and
    that the payload query carries an equality predicate on the partition column (the property that
    makes it prune).
  - `python -m pytest tests/` green overall, including the existing `test_fixtures_cache_skip.py`.
  - A dry run of the emitted SQL confirms the scan is megabytes rather than gigabytes.

amendments: (none)
