# Review — feat/player-endpoints-staging — 2026-06-15

> Machine-checked review artifact (G3). PR-a2: three generic staging models (squads,
> player_profiles, player_teams) + source/test declarations + a CPO-ruled layering.md rule
> addition (incremental-accumulation staging pattern). dbt-only; no protected paths. Required
> reviewers per review_routing.json for the staged paths (dbt_project/**): scope-auditor (always)
> + analytics-engineer-reviewer. Two iterations: iteration-1 returned analytics-engineer FAIL (two
> test findings) + both reviewers ESCALATE (the §10 layer-contract question); iteration-2 (cold
> re-review on the fixed diff, after the CPO ruled Path B) returned both PASS.

diff_sha256: 6503b48ce5be7ad6f8fa358b1c19cfe9c2558ddf228ba6ea2c5e557887f2a4d8

## scope-auditor
VERDICT: PASS
risks_checked:
- §10 resolution + scope: the incremental-accumulation deviation was escalated blinded and the
  CPO ruled Path B (escalations.log E1, 2026-06-15) — recorded in layering.md §1_staging under
  that authority, with the contract amended to add dbt_project/docs/layering.md to scope_paths
  (ordinary amendment; layering.md is not protected → no protected_override). Verified this is a
  recorded CPO ANSWER, not builder self-ruling; the layering.md edit codifies the ruled pattern
  without over-reach (names it, gates it on skip-if-present loaders, does not invent new
  mechanisms/cost gates).
- Scope-boundary + decisions_reserved + A1–A5: all seven changed paths within the amended
  scope_paths; staging-only (no base/core/marts, no ingestion, no protected paths); the reserved
  layering.md clarification is now CPO-ruled; no anti-patterns.

## analytics-engineer-reviewer
VERDICT: PASS
risks_checked:
- Incremental-accumulation rule coherence: layering.md §1_staging now documents complete-snapshot
  vs incremental-accumulation selection (step 1 + Allowed list); profiles/teams (skip-if-present)
  read all snapshots, squads (complete-snapshot) uses latest-per-league — models conform, and the
  CI check (check_layer_contract.py) permits omitting the qualify (it only forbids non-league_code
  partitions / distinct / group by / non-unnest joins). Chain of authority complete (contract
  amendment → escalations.log E1 → layering.md).
- Test-omission legitimacy: verified against precedent + real data — stg_apif__players omits a
  unique test on its roster grain and stg_apif__transfers documents nullable keys; squads has 10
  real dupes at (league_code,team_id,player_id) and player_teams has 995 null season_year, so the
  previously-requested unique/not_null tests would FAIL CI. Omitting them (faithful flatten, base
  dedups/filters) matches the generic-yml "unique only where a single snapshot is already unique"
  policy; the grain descriptions now document the dupes/nulls. JSON extraction + staging purity
  (no dedup/aggregation/cross-domain join; only lateral unnest) confirmed.

## escalations
- question (E1, raised blinded by both reviewers, iteration 1): Does staging RAW_APIF_PLAYER_PROFILES
  / RAW_APIF_PLAYER_TEAMS by UNION-ALL-snapshots (omitting layering.md's latest-snapshot step,
  because their skip-if-present loaders make them incremental-accumulation tables) constitute a §10
  layer-contract extension requiring CPO sign-off + a layering.md amendment (Path B), or is it a
  documentation clarification within builder authority (Path A)?
  CPO ANSWER: Path B (conversation, 2026-06-15; recorded escalations.log E1). Record the pattern as
  a recognized rule in layering.md with sign-off; contract amended to bring layering.md into scope.
  Resolved — layering.md updated accordingly; both reviewers PASS on the result.
