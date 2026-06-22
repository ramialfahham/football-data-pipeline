# Review — fix/raw-players-per-team-season-rows — 2026-06-22

> Fix RAW_APIF_PLAYERS exceeding BigQuery's 100 MB per-row limit (LIBER/UEL/UCL failed) by
> re-graining to one small row per (team, season), MERGE-ON-WRITE (append the run's rows +
> delete superseded prior rows for those keys) — the RAW_APIF_FIXTURE_DETAILS pattern. Staging
> reads all rows faithfully (no qualify; layer-legal for an upsert table); current-per-entity is
> deduped in base. Existing data migrated by a dry-run-default, idempotency-guarded, set-identity-
> checked re-shape script. End-to-end blast radius traced: only dim_player (identity, preserved) +
> dim_player_team_season_mapping → mart_roster (affiliation, preserved); the player performance
> chain is match-level (fct_fixture_player_stats) and untouched. Numbers preserved (413,755).
>
> Round 1 FAILED (3 reviewers): unbounded append growth + read-all-only-for-skip-if-present, stale
> stg YAML, re-shape non-idempotent + count-only integrity, quota-cut completeness gap. All fixed:
> merge-on-write (bounded/upsert), YAML corrected, idempotency guard + EXCEPT set-identity check,
> PARTIAL warning. Round 2: all four reviewers PASS. No FAIL, no ESCALATE. Required reviewers:
> scope-auditor + data-engineer (ingestion + data_contract) + analytics-engineer (dbt staging) +
> cto (script + tests).

diff_sha256: f92db170c0fa8ba80b436ebdc88305fad6d1d9c0c83e90a1f8f1bb67ff388722

## scope-auditor
VERDICT: PASS
risks_checked:
- Scope + amendments: every changed file is within scope_paths — `stg_apif__generic.yml` is covered
  by the amended `dbt_project/models/1_staging/api_football/**`, recorded in amendment (2) with CPO
  authority ("Implement"); `scripts/diagnostics/**` by amendment (1). No out-of-scope edit, no scope
  drift beyond the players 100 MB fix + the review findings. The grain change is a data-architecture
  decision in decisions_taken (not a §10 product/metric/naming class). No Appendix A: merge-on-write
  mirrors RAW_APIF_FIXTURE_DETAILS (proportionate, not gold-plating); the abandoned chunking/dual-path
  cruft is absent.
- Transactionality boundary (noted, non-blocking): the loader's INSERT and DELETE are two BQ calls,
  so a mid-run DELETE failure could leave a transient duplicate (same key, different ingested_at).
  Mitigated end-to-end — base (`base_apif__player_team_season`, `base_apif__players`) dedups by entity
  keys, so no duplicate player-team-season escapes to marts; data_contract.md documents base dedup as
  robust to transient duplicates. Follow-up worth codifying: the merge-on-write read-all staging rule
  in layering.md (currently justified by parity with fixture_details).

## data-engineer-reviewer
VERDICT: PASS
risks_checked:
- Unbounded growth (prior FAIL) — RESOLVED: the loader is merge-on-write; `_delete_superseded_player_rows`
  deletes prior rows for exactly the written keys with `ingested_at < @before` (strict; the just-inserted
  rows at @before are never touched), so the table holds one row per (league, team, season) — bounded.
  Quota-cut safe: un-fetched keys are not in written_keys, so their prior rows survive. WRITE_APPEND
  confirmed (no WRITE_TRUNCATE path reachable). Consistent with RAW_APIF_FIXTURE_DETAILS.
- Quota-cut completeness gap (prior FAIL) — RESOLVED: a quota cut sets quota_cut on both loop breaks and
  logs a "PARTIAL — quota exhausted" warning after the write block, outside the try/except (a BQ failure
  cannot suppress it); covered by test_quota_cut_logs_partial_warning.
- Re-shape safety (prior FAIL) — RESOLVED: idempotency guard no-ops if no bloated rows remain; the
  integrity check is SET-IDENTITY (EXCEPT both ways), aborting before DELETE — a NULL-cast cannot mask a
  dropped player; committed sample-payload fixture + offline loader test satisfy the sample-payload rule.

## analytics-engineer-reviewer
VERDICT: PASS
risks_checked:
- Stale stg YAML description (prior FAIL) — RESOLVED: `stg_apif__generic.yml` now states merge-on-write
  one-row-per-(team,season), read-all (no qualify), current-per-entity assembled in base — matching
  layering.md §1_staging and the actual model.
- Read-all legality + bounded (prior FAIL) — RESOLVED: the loader is merge-on-write (one row per key,
  upsert, bounded), exactly like RAW_APIF_FIXTURE_DETAILS whose staging also reads faithfully without a
  qualify — so read-all staging is layer-legal and not unbounded. Verified base dedup:
  `base_apif__player_team_season` QUALIFY partitions on (league_code, player_id, team_id, season_year)
  order by raw_ingested_at desc, and `base_apif__players` on player_api_id (source_priority asc,
  raw_ingested_at desc) — correct current-per-entity, robust to any transient migration-window duplicate;
  numbers preserved (re-shape reproduces 413,755). One row per key ⇒ no not_null/timeout volume risk.

## cto-reviewer
VERDICT: PASS
risks_checked:
- Re-shape idempotency gap (prior FAIL) — RESOLVED: `_BLOATED` (rows with response length > 1, < @ts)
  is the first action in main() and returns 0 after migration, so a second run no-ops before any
  INSERT/DELETE. Guard fires before all writes.
- Integrity check count-only (prior FAIL) — RESOLVED: `_KEY_DIFF` is EXCEPT DISTINCT both directions
  (pre_not_post + post_not_pre), aborting before DELETE on any nonzero diff — catches drop/substitution,
  not just cardinality. DELETE `ingested_at < @ts` cannot touch the just-inserted @ts rows; parameterized
  throughout; dry-run default.
- Test quality: test_writes_one_row_per_team_season_from_real_payload asserts the merge-delete is called
  with the written keys and the same ingested_at; test_quota_cut_logs_partial_warning covers the PARTIAL
  path; all tests fully offline (_CapturingClient + monkeypatched delete), real loader path exercised, no
  false-green from over-mocking.

## escalations
(none)
