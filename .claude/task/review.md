# Review — feat/player-endpoints-ingest — 2026-06-15

> Machine-checked review artifact (G3). PR-a1: player-endpoint ingestion CODE
> (profiles + teams + squads loaders + per-player universe + orchestrator wiring +
> data_contract docs). No dbt models, no protected paths. Required reviewers per
> review_routing.json for the staged paths (ingestion/** + docs/data_contract.md):
> scope-auditor (always) + data-engineer-reviewer. Two iterations: iteration-1 returned
> scope-auditor ESCALATE (global-phase = new mechanism?) and data-engineer FAIL (3
> findings); iteration-2 (cold re-review on the fixed diff) returned both PASS.

diff_sha256: 3a92ae8755146bdc9abc96ec5cb12602714749dc5db991544acdb35e51247cd1

## scope-auditor
VERDICT: PASS
risks_checked:
- NEW-mechanism §10 check on the global per-player phase (Phase 5): applied the §11 premise
  check against the full orchestrator — Phase 2 (`run_batch_fixture_fanout_and_persist`) is a
  pre-existing global cross-competition phase, so the per-player global phase is a precedented
  application of an existing pattern, AND it is the forced implementation of the CPO-approved
  per-player bio axis (escalations.log R2). Premise "new mechanism" does not hold → not a §10
  escalation; in scope.
- Scope-boundary + decisions_reserved: all nine changed paths are within the contract's
  scope_paths; no dbt models, no protected paths, no contract amendment; no derive/transform in
  this PR; backfill DISPATCH not taken (reserved). Anti-patterns A1–A5 absent (no metrics, no
  product fabrication, no rule over-extension, no consumption shortcut, no frontend logic).

## data-engineer-reviewer
VERDICT: PASS
risks_checked:
- BQ JSON-extraction SQL in `player_universe.py` (`_query_universe`) verified against the
  production `stg_apif__players.sql`: identical paths (`$.response[*]` team_block →
  `$.players_payload[*]` player_el → `$.player.id`), latest-snapshot-per-league via
  `qualify row_number()`, season>=min_season filter — no JSON-path mismatch / silent-gap risk.
- Cost/quota safety: every loop honours `errors_quota._http_quota_exhausted` (league + item
  level) and a per-endpoint `API_FOOTBALL_SKIP_*` env var; `append=True` only (no WRITE_TRUNCATE
  on a data table); skip-if-present anti-join (`_existing_player_ids`, NotFound→empty on first
  run) keeps ongoing runs cheap and lets the quota-guarded backfill resume — matches the approved
  cost model.
- Contested "CPO rule 2026-06-12 / sample-payload tests": independently verified it appears ONLY
  in the data-engineer-reviewer's own brief, NOT in working_agreement.md or engineering_standards.md;
  `tests/fixtures/apif/` is absent for every existing loader (incl. the transfers/squads precedents
  this PR mirrors); #415 (F21) is the OPEN backlog item to create that framework — the gap
  pre-exists and is #415's, not this PR's. New loaders are covered by `test_ingestion_loads_smoke.py`.
- Empty-response guard + doc count: `player_squads.py` returns before the BQ write when the
  response is empty (consistent with the global loaders' per-league `continue`, stricter than the
  transfers precedent); both `eight`→`eleven` occurrences in data_contract.md corrected.

## escalations
(none — the iteration-1 scope-auditor ESCALATE was resolved within the cycle: the iteration-2
scope-auditor proxy applied the §11 premise check and found the "new mechanism" premise false.)

## non-blocking follow-up (carried to PR-a2)
- data-engineer noted the per-table landing-payload shapes (`{player_id, profile_payload}` /
  `{player_id, teams_payload}` / `{team_id, squad_payload}`) are not yet in the data_contract
  landing-zone section that documents the other loaders' reshaped payloads. Belongs with PR-a2
  (where the staging models parse those shapes); not added here to keep reviewed==committed.
