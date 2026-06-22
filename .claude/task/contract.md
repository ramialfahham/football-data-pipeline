# Task contract — RAW_APIF_PLAYERS merge-on-write per (team,season) (all leagues backfillable)

objective: >
  Fix the players backfill so EVERY league — including the biggest (LIBER/UEL/UCL) — can be
  backfilled. Root cause: the loader crammed an entire league's players (all teams × all seasons)
  into ONE BigQuery row, exceeding BQ's 100 MB per-row JSON limit (LIBER failed on the 2026-06-22
  full-profile resume). Fix: store ONE small row per (team, season), merge-on-write — exactly the
  RAW_APIF_FIXTURE_DETAILS pattern (one row per fixture). No row approaches the limit, for any league.

decisions_taken: >
  - Grain: one row per (team, season); payload {league_code, response:[entry]} (one entry/row).
  - Loader (squads.py) is MERGE-ON-WRITE: append the run's per-(team,season) rows, then delete the
    superseded prior rows for exactly those keys → one row per (league, team, season), BOUNDED (not
    append-accumulating). Only re-written keys are touched, so a quota cut leaves un-fetched keys'
    prior rows intact (a partial-snapshot warning is logged). This makes it an idempotent/upsert
    table — the reviewers required idempotency to avoid unbounded growth.
  - Staging (stg_apif__players) reads ALL rows faithfully — NO latest-snapshot qualify (forbidden by
    check_layer_contract for a non-league partition; and a per-league qualify would drop entities) —
    and current-per-(player,team,season) is assembled in BASE (base_apif__player_team_season /
    base_apif__players already dedup by entity keys). This is layer-legal because the table is
    merge-on-write/upsert (one row per key), exactly like RAW_APIF_FIXTURE_DETAILS, whose staging
    also reads faithfully without a qualify.
  - player_universe._query_universe reads all rows (its own group by player_id dedups).
  - One-time migration via scripts/diagnostics/reshape_players_to_team_season.py (dry-run default):
    explodes each league's latest bloated snapshot into per-(team,season) rows and deletes the
    pre-migration rows. Idempotency guard (no-op if no bloated rows remain) + SET-IDENTITY check
    (EXCEPT both ways, not count-only) that ABORTS before deleting on any mismatch. Dry-checked:
    626 bloated rows -> 13,386 small rows, 413,755 player-team-seasons preserved exactly.
  - Supersedes PR #534 (chunking). #534 to be CLOSED.

blast_radius (end-to-end, traced): >
  RAW_APIF_PLAYERS feeds ONLY dim_player (identity; 1 of 3 sources) and
  dim_player_team_season_mapping -> mart_roster (affiliation). The player PERFORMANCE chain
  (fct_fixture_player_stats -> int_player_season__metrics / momentum / season-record / profile /
  match-log / leaderboards) is built from RAW_APIF_FIXTURE_DETAILS and is UNAFFECTED. Numbers are
  preserved end-to-end (re-shape reproduces 413,755; mart_roster + dim_player unchanged).

amendments: >
  2026-06-22 (1) — CPO "ok, do it": the fixture-details-style per-entity re-grain + reviewed
  re-shape script. Added scripts/diagnostics/** to scope.
  2026-06-22 (2) — CPO "Implement" after the end-to-end assessment + review FAIL: adopt merge-on-write
  (bounded loader, the reviewers' required idempotent/upsert), and broaden the dbt-staging scope to
  `dbt_project/models/1_staging/api_football/**` to fix the stale stg_apif__players description in
  stg_apif__generic.yml (analytics-engineer finding). Authority: this conversation.

refs: >
  Review FAIL (3 reviewers) on the prior append+read-all approach: unbounded growth + the §1_staging
  read-all exemption is for skip-if-present/upsert loaders. Pattern: loads/batch_fixtures.py
  (merge-on-write, one row per fixture). Root cause log: /tmp/phase2a_resume.log.

scope_paths:
  - ingestion/api_football/bigquery.py
  - ingestion/api_football/loads/squads.py
  - ingestion/api_football/loads/player_universe.py
  - dbt_project/models/1_staging/api_football/**
  - scripts/diagnostics/**
  - tests/**
  - docs/data_contract.md
  - .claude/active_work.md
  - .claude/task/**

done_when:
  - squads.py writes one merge-on-write row per (team, season) (append + delete-superseded-keys);
    quota cut logs a partial warning and leaves un-fetched keys intact.
  - stg_apif__players reads all rows faithfully (no qualify); base assembles current-per-entity;
    stg_apif__generic.yml description corrected. check_layer_contract.py passes.
  - reshape script: dry-run default, idempotency guard, set-identity (EXCEPT) abort-before-delete.
  - validate-local green (pytest + dbt parse + sqlfluff + layer-contract).
  - data_contract.md documents merge-on-write one-row-per-(team,season) for RAW_APIF_PLAYERS.
  - Full review cycle PASS; PR opened; re-shape run on prod RAW; CI (incl. data-build) green; CPO merges. #534 closed.
