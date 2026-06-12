# Review — data/afccl-id-verified — 2026-06-12

> Issue #426 / audit F23: AFCCL provider_league_id 17 verification. The builder
> queried RAW_APIF_LEAGUES (BigQuery) — id 17 returns "AFC Champions League Elite"
> (Cup), seasons 2016-2025 incl. current 2024/2025, so the ID is CORRECT and the
> "disable" branch of #426 does not apply. The diff updates only the AFCCL registry
> note to record that evidence + drop the stale "legacy ID" caveat; no field changed.
> Required reviewers for docs/competition_registry.yml: scope-auditor + data-engineer.

diff_sha256: 0ab1e54db51b2f9f1ee459e4f874978c70c6bae160b1c01d8030677ffb41a4ab

## scope-auditor
VERDICT: PASS
risks_checked:
- Cost-knob boundary: the contract reserves provider_league_id / ingest_active /
  history_seasons / cost knobs; the diff shows all structural fields (924-930)
  UNCHANGED — `ingest_active: true`, `provider_league_id: 17`, `history_seasons: 5`,
  `current_season: "2024"` untouched. The note phrase "ingest_active confirmed" is
  evidentiary, not a silent re-enable (the field was already true). No §10 decision
  taken: keeping ingest_active is the data-driven result of a successful verification,
  not a product/cost call.
- Registry/CI integrity + scope: only `docs/competition_registry.yml` changed (in
  scope_paths); the edit stays within the existing folded `>` notes block with no
  structural YAML change, so registry parse + check_registry_var_sync +
  check_competition_type_seed hold. The note records verifiable evidence (source
  RAW_APIF_LEAGUES, returned name + seasons), not an unsupported assertion.

## data-engineer-reviewer
VERDICT: PASS
risks_checked:
- Provider-ID evidence (four-wrong-IDs rule): the note cites the query source
  (RAW_APIF_LEAGUES), date (2026-06-12), returned name ("AFC Champions League Elite",
  Cup) and seasons through the current 2024/2025 — specific, internally consistent
  with the registry `name` and `competition_type: continental_club`, and sufficient to
  retire the "spot-check" caveat. The current-season presence rules out a defunct/
  reassigned id-17 entry. No ID-confusion vector remains.
- Silent cost/scope change: all cost/scope fields (provider_league_id, ingest_active,
  history_seasons, current_season, status, ingest_completeness_gate) are unchanged;
  the `notes` field is not read by sync_dbt_vars.py (which uses only league_code,
  status, competition_type), is not in the derived competition_registry.csv seed, and
  is not in dbt_project.yml vars — so no sync artefact is affected or missing.
- ID interpretation: verification path is RAW_APIF_LEAGUES (the ingested response for
  id 17 itself), not an external lookup that could confuse competitions; "AFC Champions
  League Elite" with active seasons maps unambiguously to AFCCL. Not a new competition,
  so the verify-competition-ingest post-merge gate (new-onboarding rule) does not apply.

## escalations
(none — both reviewers PASS.)
