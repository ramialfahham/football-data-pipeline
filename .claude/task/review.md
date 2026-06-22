# Review — fix/raw-players-row-chunking — 2026-06-22

> Fix the RAW_APIF_PLAYERS >100 MB single-row load failure (surfaced on LIBER during the Phase 2a
> resume; UEL 81.8 MB / UCL 78.7 MB imminent). Chunk the per-team×season players snapshot into
> byte-bounded rows written in ONE atomic load job sharing one ingested_at; the two latest-snapshot
> readers (stg_apif__players, player_universe._query_universe) now keep all rows where
> ingested_at = max per league_code. Output-preserving for existing single-row data. Required
> reviewers: scope-auditor (always) + data-engineer (ingestion + data_contract.md) +
> analytics-engineer (dbt staging) + cto (tests). 4-step cycle, blinded.
>
> Round 1: data-engineer FAILed on (a) no committed sample-payload fixture, (b) ingested_at tie.
> Fixes: (a) committed real CWC /players fixture + 2 fixture tests; (b) docstring documents
> microsecond ingested_at + single-flight lock (a non-§10 factual resolution — isoformat() is
> microsecond precision, the reviewer assumed second). Round 2: data-engineer + cto re-reviewed the
> final diff → PASS; scope-auditor re-bound to the final hash → PASS. analytics-engineer's PASS is
> carried from round 1 — the dbt model (its only surface) is byte-identical in the final diff; the
> round-2 additions are a test fixture, two tests, and a bigquery.py docstring sentence, none of
> which touch dbt_project/**. No FAIL, no ESCALATE.

diff_sha256: 799f6d9c3a7a23a01532682c00c907d4f1d9d6888d025c4aadba458516cb54ad

## scope-auditor
VERDICT: PASS
risks_checked:
- Scope boundary on the final diff: every changed file is inside the contract's scope_paths —
  the four code files + dbt model are explicitly listed, the new `tests/fixtures/apif/players_cwc_sample.json`
  and the test edits fall under `tests/**`, `docs/data_contract.md` and `.claude/task/contract.md`
  are listed. No out-of-scope edit; the round-2 fixture/test/docstring additions introduced no
  scope drift (all within already-scoped trees).
- Decision-rights / NEW-mechanism: `load_json_payload_rows_to_bq` is a new loader function but it
  is pre-authorized in the contract's decisions_taken (targeted fix for the 100 MB row limit),
  documented in code + data_contract.md, and is not a unilateral rule extension or a product/metric/
  naming decision. Committing a trimmed real public-player test slice is routine test data, not a
  §10 data/privacy decision. No Appendix A anti-pattern (no over-engineering — a schema column was
  rejected for the simpler atomic-shared-timestamp approach; no hack-to-pass). `.claude/active_work.md`
  is in scope_paths but is the hash-excluded, review-exempt close-out handover written at commit
  time — an accepted deferral, not a scope/contract-integrity problem.

## data-engineer-reviewer
VERDICT: PASS
risks_checked:
- Prior finding (a) — committed sample-payload fixture — RESOLVED: `tests/fixtures/apif/players_cwc_sample.json`
  is a trimmed real CWC /players snapshot at the true wire shape
  ({league_code, response:[{team_id, season, players_payload:[{player, statistics:[...]}]}]}, accented
  names included to exercise the ascii-escape inflation that caused the overflow). Two tests exercise
  `chunk_players_response` against it and assert the chunked-row shape matches stg_apif__players'
  exact unnest path ($.response[].players_payload[].player.id). Satisfies the offline-test-against-
  committed-sample-payload rule.
- Prior finding (b) — ingested_at snapshot tie — RESOLVED: ingested_at is microsecond precision
  (datetime.now(timezone.utc).isoformat()) and ingestion is single-flight (lease lock admits one run
  at a time, minutes apart), so two distinct snapshots cannot tie; every tie is by construction the
  chunks of one atomic load job. A sequence/snapshot-id column would add nothing over this guarantee.
- Atomicity + consumer completeness: all chunks land in one all-or-nothing load_table_from_file job
  sharing one ingested_at, so the max(ingested_at) readers never see a partial snapshot. Confirmed
  no remaining RAW_APIF_PLAYERS reader uses row_number()=1 (both consumers updated;
  base_apif__players' row_number is a per-player-id dedup on top of staging, not a snapshot selector).
  The WRITE_TRUNCATE branch is unreachable from the production call site (squads.py always append=True).

## analytics-engineer-reviewer
VERDICT: PASS
risks_checked:
- Layer-contract compliance of the new QUALIFY: `qualify ingested_at = max(ingested_at) over
  (partition by league_code)` partitions on league_code only with no aggregation/group-by/join/distinct
  — structurally identical to the permitted latest-snapshot selection in layering.md §1_staging; the
  loader's atomic shared-timestamp guarantee is what makes "all rows of the latest snapshot" a
  selection rather than aggregation. (dbt surface unchanged in the final diff vs the round-1 reviewed
  version — round-2 additions touch only tests/ and a bigquery.py docstring.)
- Output-preserving + cross-chunk union: existing data has one row per league per run (distinct
  per-run timestamps), so ingested_at=max == the old row_number()=1 — no shipped-number change. The
  chunker places each team×season entry in exactly one chunk, so the lateral unnest across the
  multiple latest-snapshot rows produces the disjoint union with no duplication or loss; downstream
  base dedup keys (player_id / player_team_season) never collide across chunks of one run.

## cto-reviewer
VERDICT: PASS
risks_checked:
- Test fidelity / no false-green: the pure chunker tests prove no entry is dropped or reordered
  (order + team×season + player-id-set assertions would fail on drop or duplication), each chunk
  stays under budget, an oversize single entry is isolated, and an empty response still writes one
  row. The atomicity test asserts exactly ONE load_table_from_file call with all rows sharing one
  ingested_at and WRITE_APPEND — it would catch a refactor to per-chunk load jobs. Monkeypatching
  targets the name where it is used (sq.load_json_payload_rows_to_bq), so the real path is exercised.
- New real-fixture tests: run fully offline against the committed `players_cwc_sample.json`;
  the `Path(__file__).parent / fixtures / apif / ...` resolution is robust under pytest from any cwd;
  accented names are stored UTF-8 and measured via json.dumps(ensure_ascii=True), matching the loader
  exactly. Residual non-blocking gaps noted: the _players_max_row_bytes() ValueError/floor branch and
  the append=False loader branch are untested (not invariants of this fix); the per-entry byte budget
  excludes the ~100–200 byte row wrapper (immaterial against the 40 MB default / 2.5x headroom).

## escalations
(none)
