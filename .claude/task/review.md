# Review — feat/dim-coach — 2026-06-23

diff_sha256: 2b32c24a282c269586f5220fca26e23375c64e23e64a7552b02f864dba52236e

## analytics-engineer-reviewer
VERDICT: PASS
risks_checked:
- FK reachability for coach_sk -> dim_coach: both stg_apif__coaches and stg_apif__coach_career unnest
  the same $.response[] coach element of RAW_APIF_COACHES, so any coach with career stints always
  produces an entity row — the relationships test resolves. Cross-model columns all exist; the grain
  (coach_sk, team_api_id, start_date) is null-safe (base drops null coach_id/team_id/start_date).
- Staging not_null placement on provider-nullable fields: stg_apif__coach_career correctly carries NO
  not_null on team_id (provider-nullable — ~6k career stints have a null team.id, verified in RAW;
  faithful staging passes them, base filters them), mirroring the standings team_id pattern.
  stg_apif__coaches keeps not_null on coach_id (the entity grain key, 0 nulls verified). dim_coach has
  not_null on coach_sk + coach_name; soft team_sk link correctly has no relationships test.

## scope-auditor
VERDICT: PASS
risks_checked:
- Snapshot-rule §10 recorded correctly: read-all (not latest-per-league) for the complete-snapshot
  RAW_APIF_COACHES is in decisions_reserved + escalations.log (2026-06-23) with the CPO ANSWER ("all",
  entity preservation, 120-coach delta evidence); the code implements it and the stg header documents
  the exception. Additive only — no existing model/number changed; diff within scope_paths.
- Soft team_sk link integrity: dim_coach_team_mapping intentionally omits a strict FK on team_sk
  (career clubs exceed dim_team), preserving provider team_api_id + team_name for recovery; documented
  in the contract + core.yml. The enforceable FK (coach_sk -> dim_coach) IS tested. No coverage cut.

## escalations
- question: RAW_APIF_COACHES is complete-snapshot per (league, run). Staging snapshot rule —
  read-all (preserve every coach ever seen, all-time, mirrors dim_player/dim_team) vs
  latest-per-league (current only)? The two reviewers split; ~120-coach delta. (Put to the CPO with
  evidence, no anchoring.)
  CPO ANSWER: read-all / all-time — "all". dim_coach preserves every coach ever seen; the
  complete-snapshot latest-per-league default is deliberately not applied here. (escalations.log 2026-06-23.)
