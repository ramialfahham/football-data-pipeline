# Task contract — Fix RAW_APIF_PLAYERS >100MB single-row load failure (players snapshot chunking)

objective: >
  Fix the loader defect that made the LIBER /players load fail during the 2026-06-22 Phase 2a
  resume run: `load_squad_players_batch` (loads/squads.py) accumulates ALL team×season player
  responses for a league into ONE payload dict and writes it as a SINGLE BigQuery row, which
  exceeds BQ's 100 MB per-row JSON limit for large-roster deep leagues. Measured blast radius:
  LIBER's full 8-season snapshot >100 MB (load rejected, "Rows: 1; errors: 1; Row size larger
  than 104857600"); UEL already 81.8 MB and UCL 78.7 MB as single rows — both will overflow on
  their next deep run. Sibling tables (SQUADS/PROFILES/TEAMS) are all <2 MB → NOT affected; the
  fix is scoped to RAW_APIF_PLAYERS only.

  Fix: chunk the accumulated players `response` into size-bounded payload rows and write them in
  ONE atomic load job sharing a single `ingested_at`; update the TWO "latest snapshot per league"
  readers of RAW_APIF_PLAYERS to read all rows of the latest snapshot (ingested_at = max per
  league_code) instead of row_number()=1.

refs: >
  This conversation 2026-06-22 (CPO: "investigate the bugs thoroughly and fix now"). Surfaced by
  the Phase 2a resume run /tmp log: "players BQ LIBER: 400 ... Row size is larger than 104857600".
  Root cause: ingestion/api_football/loads/squads.py:24-65 + bigquery.py:131-201 (load_json_to_bq
  writes one row). Consumers: dbt stg_apif__players.sql + loads/player_universe.py:_query_universe.
  Design contract from tests/test_player_squads_catchup.py:153-157 (latest-snapshot-per-league;
  a partial write masks the prior complete one — hence the single ATOMIC load job).

decisions_taken: >
  - Chunk-the-response (keep the (league_code, payload, ingested_at) schema + the
    {league_code, response:[...]} payload shape; only the NUMBER of rows per snapshot changes).
    Chosen over per-entity rows (schema change) and trimming (data loss). Least invasive correct fix.
  - Atomicity: all chunks of one run land in a SINGLE load_table_from_file job (all-or-nothing) and
    share one ingested_at — so the "ingested_at = max per league_code" readers see the COMPLETE
    chunked snapshot or none of it; a partial snapshot is never visible. This preserves the existing
    latest-snapshot-per-league contract.
  - Output-preserving for existing data: every league currently has at most one row per run
    (distinct per-run timestamps), so ingested_at=max == today's row_number()=1 — NO shipped number
    changes for current single-row snapshots. Multi-row reads only occur once chunked data lands.
  - Chunk threshold measured as ascii-escaped JSON bytes (matching the loader's
    json.dumps(ensure_ascii=True) serialization, which inflates accented LATAM names vs
    TO_JSON_STRING — why LIBER overflowed). Default ~40 MB/row (headroom under 100 MB), env-tunable.
  - NOT in scope: CAFCL's 440 missing FIXTURE_STATISTICS (VERIFIED provider coverage limit — 0 stat
    blocks, no errors; correct permanent-empty handling, not a defect). Sibling player tables (safe).
    The pre-existing quota-cut partial-snapshot behaviour of the players loader (unchanged here).

scope_paths:
  - ingestion/api_football/bigquery.py
  - ingestion/api_football/loads/squads.py
  - ingestion/api_football/loads/player_universe.py
  - dbt_project/models/1_staging/api_football/stg_apif__players.sql
  - tests/**
  - docs/data_contract.md
  - .claude/active_work.md
  - .claude/task/**

done_when:
  - load_squad_players_batch chunks its response and writes via a new atomic multi-row loader
    (bigquery.py) that shares one ingested_at across all chunk rows; 1-chunk leagues still write
    one row (back-compat).
  - stg_apif__players.sql AND player_universe.py:_query_universe both select the latest snapshot
    as "ingested_at = max(ingested_at) over (partition by league_code)" with a WHY comment.
  - A pure unit test for the chunker (preserves all entries in order; each chunk under threshold;
    >=1 chunk incl. empty; an oversize single entry gets its own chunk) + a loader/atomicity test
    (one load job, shared ingested_at, league_code stamped) following the existing test style.
  - validate-local passes (ruff/black/pytest + dbt parse + sqlfluff on the changed model).
  - data_contract.md notes the chunked-snapshot model for RAW_APIF_PLAYERS (folded into the
    existing RAW/merge section; no new doc).
  - Full review cycle (data-engineer + analytics-engineer + scope-auditor) PASS; ONE substantive
    commit; PR opened for the CPO to merge. active_work.md handover updated at close-out.
