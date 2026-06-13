# Review — chore/retire-transfers — 2026-06-13

> Retire the transfers chain entirely (CPO ruling 2026-06-13, recorded in
> .claude/task/escalations.log): delete stg/base/core transfers models + the ingestion
> loader, remove the raw source + the dim_player transfers identity fallback, update docs,
> drop the dangling .env.example var. RAW_APIF_TRANSFERS dropped from BQ post-merge.
> Required reviewers: scope-auditor (always) + data-engineer-reviewer (ingestion/** +
> docs/data_contract.md) + analytics-engineer-reviewer (dbt_project/**).
> Iterations: iter-1 all FAIL — competition_runner docstring stale (all 3), .env.example
> dangling var (data-eng), data_contract "dropped" past-tense (data-eng), §10 ruling not
> recorded (scope-auditor); one spurious data-eng finding (a "sample-based test rule" that
> does not exist — REBUTTED, not actioned). Fixes: docstring + data_contract wording (in
> scope), .env.example via amendment A1, CPO ruling recorded in escalations.log.
> iter-2: data-eng + analytics PASS. iter-3: scope-auditor PASS (recorded-ruling check).
> All three verdicts below are against the same hash.

diff_sha256: b93070f691381c9ffc003c69bfede29af9250d0aec9c65547c12422fb9a6158f

## scope-auditor
VERDICT: PASS
risks_checked:
- §10 authorization (cost + destructive): verified the CPO ruling to retire transfers and
  DROP the RAW_APIF_TRANSFERS table is RECORDED in .claude/task/escalations.log (2026-06-13
  chore/retire-transfers entry) — it covers both the cost (stop the daily /transfers ingest)
  and the explicit destructive-drop ("BQ table dropped too → yes"), matching the contract's
  "CPO ruling 2026-06-13" attribution. Not a silently-taken decision.
- Behaviour-change honesty + post-merge sequencing: removing transfers_src drops transfer-only
  identities from dim_player — the contract names this deliberately and the rationale holds
  (fct_transfer, the only consumer, is deleted in the same PR; played players covered by
  fixture sources). The RAW_APIF_TRANSFERS drop is documented as a POST-MERGE step; no-writer
  code lands first, so the 04:00 UTC run cannot recreate it (ROUNDS precedent). Also confirmed:
  the "sample-based test rule (2026-06-12)" cited by an iter-1 reviewer does not exist
  (engineering_standards/working_agreement/development_workflow; no tests/fixtures) — rebuttal sound.

## data-engineer-reviewer
VERDICT: PASS
risks_checked:
- Ingestion writer elimination (no recreation): loads/transfers.py deleted; its import + call
  removed from competition_runner.py (phases now teams → injuries; docstring updated);
  settings.py drops API_FOOTBALL_TRANSFERS_MAX_PAGE; no remaining read of FETCH_TRANSFERS /
  TRANSFERS_USE_PAGE / TRANSFERS_MAX_PAGE; .env.example var removed. Grep of ingestion/**: zero
  transfers hits. No code writes raw_table("TRANSFERS") post-merge → the 04:00 run cannot
  recreate the table; the post-merge bq rm sequencing is sound.
- Raw source + data_contract consistency: sources.yml drops raw_apif_transfers (no staging
  reads it); the unified-table count eight→seven is arithmetically correct vs the 7 surviving
  rows; endpoints map, append-only prose, pagination note, plan-vs-product row and the Retired
  note ("dropped post-merge", mirroring ROUNDS) are all consistent — nothing still claims
  transfers is ingested. operations_guide transfers env-var sections removed.

## analytics-engineer-reviewer
VERDICT: PASS
risks_checked:
- FK integrity after transfer-only player removal: every player feeding the surviving
  ERROR-severity relationships tests (fct_fixture_player_stats.player_sk→dim_player,
  fct_fixture_event.player_sk→dim_player, dim_player_team_season_mapping.player_sk→dim_player)
  is sourced from fixture_players_src / fixture_events_src / stg_apif__players — the same paths
  that now exclusively compose dim_player. Transfer-only identities had exactly one consumer
  (fct_transfer, deleted here), so no surviving test can fail on a now-absent player. ci-data-build
  predicted PASS.
- Dangling-ref completeness + union integrity: grep across all .sql/.py/.yml finds zero refs to
  base_apif__transfers / stg_apif__transfers / fct_transfer / raw_apif_transfers (dbt parse
  compiles clean). base_apif__players union is 3 aligned CTEs with source_priority renumbered
  1/2/3 preserving precedence (players > fixture_players > fixture_events); header comment matches.
  Layer compliance holds.

## escalations
(none — iter-1 FAILs resolved: in-scope doc fixes, .env.example via amendment A1, and the §10
ruling recorded in escalations.log (not escalated — the ruling genuinely exists from this
session). The spurious "sample-based test rule" finding was rebutted (no such rule in the repo),
independently confirmed by data-engineer + scope-auditor. DQ proof (FK relationships) runs in
ci-data-build.)
