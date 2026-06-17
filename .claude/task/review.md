# Review — feat/dim-team-pure-entity — 2026-06-17 (Phase 2: drop the dim_team stamp)

> Phase 2 of the dim_team entity/affiliation split (Phase 1 = PR #488, merged). Drops
> dim_team.league_code (the provenance stamp) → dim_team is a pure entity; repoints the one
> consumer (mart_team_market_value) onto the Phase-1 mapping dim. Required reviewers (routing
> for the staged dbt_project/** paths): scope-auditor (always) + analytics-engineer-reviewer.
> No §10 escalation: the only §10-adjacent point (the mart's WC set goes 23→48) was CPO-
> pre-approved and is structural-only (mart unexported, value data empty).

diff_sha256: 63e90e9242cb773deefdf0ad54ed3b8bbc55c5b4983c251ae7873ec564759aa8

## scope-auditor
VERDICT: PASS
risks_checked:
- No undiscovered consumers: searched all dbt layers (staging→marts) + export scripts for
  dim_team.league_code / where league_code='WC'; found zero outside the repointed mart, so the
  decisions_reserved "stop if another consumer exists" trigger does not fire.
- Scope + deferrals intact: the season-rollup enhancement and base_apif__teams_global are NOT
  touched (both in decisions_reserved); all five staged hunks are within scope_paths.
- §10 boundary on the mart: the 23→48 WC-set change is §10-adjacent but the contract records CPO
  approval (decisions_taken item 2) and it is structural-only — mart not exported (no script ref),
  value data empty; the existing shared.yml tests (unique team_sk, accepted_values ["WC"]) still hold.

## analytics-engineer-reviewer
VERDICT: PASS
risks_checked:
- No dangling reference: all 19 dim_team consumers across 3_core/4_intermediate/5_marts checked —
  every league_code they carry comes from a fact/intermediate CTE (fct_fixture, int_legs__team_match,
  fct_standings, …), never the dim_team CTE; mart_team_market_value (the only prior reader) is fully
  repointed. No surviving dim_team.league_code reference → the BQ build will not break.
- No fan-out: wc_teams does select distinct team_sk before the 1:1 inner join to dim_team and the
  1:1 left join to int_team__market_value_latest; grain one-row-per-team_sk preserved (the shared.yml
  unique test on team_sk still passes).
- Repoint correctness: output schema preserved (same columns/order incl. literal 'WC' as league_code);
  the WC set is derived from the mapping (distinct team_sk, league_code='WC'); the core.yml dim_team
  edits (removed league_code column/test, new description) and the layering.md note match the model.

## escalations
(none)
