# Review — feat/dim-team-competition-season-mapping — 2026-06-17 (Phase 1: team membership dim)

> Phase 1 of the dim_team entity/affiliation split: NEW core relationship (mapping) dim
> dim_team_competition_season_mapping (team↔competition↔season membership derived from
> fixtures, incl. scheduled). Required reviewers (routing for the staged dbt_project/**
> paths): scope-auditor (always) + analytics-engineer-reviewer. One §10 governance-
> classification question arose in review and was ruled by the CPO (2026-06-17, recorded
> below + escalations.log).

diff_sha256: 4296c012ce74ca7db51b8de378f08eebb3b249d3367f0dcb4f319c7e76cf3e2f

## scope-auditor
VERDICT: ESCALATE
risks_checked:
- Scope: all five staged hunks are within the contract's scope_paths (the new model + test,
  core.yml, layering.md, contract.md); no edit outside the allowlist.
- Deferrals intact: Phase 2 (dropping dim_team.league_code, repointing mart_team_market_value,
  refactoring mart_team_season) does NOT appear in the diff — net-new dim only, nothing repointed.
- Docs match code: core.yml + layering.md describe the model as implemented (after the team_sk
  SK-description fix); the contract.md change is a legitimate new-task contract (never review-exempt).
question: The contract records today's design choices as "CPO-approved this conversation" but no
  matching entry existed in escalations.log (the record of CPO rulings). Do up-front design
  approvals need logging there too, or is the contract's decisions_taken the sufficient record?
CPO ANSWER: Path A — LOG IT (CPO 2026-06-17, this conversation). Up-front CPO design approvals are
  recorded in escalations.log alongside review-time rulings; the 2026-06-17 entry now captures the
  D1–D7 design approvals + this E1 ruling.

## analytics-engineer-reviewer
VERDICT: PASS
risks_checked:
- Layer placement: the model refs only base_apif__fixtures_next (a 2_base view) — no stg_*/mart_*
  ref, no raw JSON parsing, no union_all macro; the CI check_layer_contract rules for 3_core hold.
- Grain uniqueness: UNION DISTINCT in team_sides + GROUP BY (league_code, season, team_sk) in
  memberships enforces the declared grain BEFORE the surrogate; unique_combination_of_columns +
  unique on the SK double-cover at build (grain is enforced, not assumed via the 1:1 invariant).
- Key conformance: team_sk = cast(team_id int64), league_sk = cast(league_api_id int64),
  season_sk = generate_surrogate_key(league_api_id, season) all match dim_team / dim_league /
  dim_competition_season (and fct_fixture's identical season_sk derivation, whose relationships
  test passes in prod) by value.
- Consistency test is a genuine cross-model invariant (mapping vs fct_fixture, a separate model),
  not a tautology; the join-path regression is covered by the team_sk→dim_team relationships test.

## escalations
- question: do up-front CPO design approvals (contract decisions_taken) need an escalations.log
  entry, or is the contract sufficient?
  CPO ANSWER: Path A — LOG IT (CPO 2026-06-17). Up-front approvals are logged alongside review-time
  rulings; recorded in the 2026-06-17 escalations.log entry (D1–D7 design approvals + this ruling).
