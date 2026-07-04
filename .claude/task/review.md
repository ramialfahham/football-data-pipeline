# Review — feat/player-yoy-full-season-reference — 2026-07-04

> G3 Lock artifact. dbt-only enrichment of the already-wired player YoY block
> (`int_player_profile__yoy`, #638): adds a `prev_full` CTE surfacing the prior season's
> FULL-season totals as a context anchor (6 new columns: `appearances_prev_full` + 5
> `*_prev_season_full`), surfaces them in `mart_player_profile`, and adds one invariant DQ
> test (full >= pace-matched). No metric_catalogue change, no export edit (auto-carries via
> `select *` + `_strip_identity`), no new model. Plan CPO-approved via ExitPlanMode.
> Required set (routing): scope-auditor (always) + analytics-engineer-reviewer (`dbt_project/**`).
>
> Round 1 (hash 8bec99fa) — scope-auditor **PASS** + analytics-engineer-reviewer **PASS**; the
> analytics-engineer flagged one NON-blocking nit: the 6 new simple `prev_full.*` columns sat
> AFTER the calculated `_delta_yoy` expressions in the final SELECT, breaking the
> simple-then-calculated order the sibling `int_team_profile__yoy` follows (a latent SQLFluff
> ST06 risk — ST06 fires on `int_*` models per #621, and CI-only since SQLFluff can't run
> locally). Fix: reordered the simple `prev_full.*` columns ahead of the calculated deltas
> (pure reorder, identical logic). That changed the staged hash → BOTH reviewers re-run fresh.
> Round 2 (hash 0cc56033) — scope-auditor **PASS** + analytics-engineer-reviewer **PASS**; the
> analytics-engineer independently confirmed the SELECT is now ST06-compliant and matches the sibling.

diff_sha256: 0cc56033457d2557baf1c34fb2dab13596ba602f70fe4c16fae6c811a9a28955

## scope-auditor
VERDICT: PASS  (round 2 on the reordered hash; round 1 also PASS on hash 8bec99fa)
risks_checked:
- **Scope-path discipline.** All 4 staged files are within `scope_paths`: `.claude/task/contract.md`
  (`.claude/task/**`) + the 3 declared model files (`int_player_profile__yoy.sql`,
  `mart_player_profile.sql`, `int_player_profile.yml`). No edit beyond scope, no drive-by fix,
  no unauthorized change.
- **Decision rights (§10).** The two design choices are legitimately settled, not smuggled: (a)
  NO delta-vs-full is computed — the full figures are context only, aligned with the model's own
  header philosophy (a part-season vs a full season would mislead), recorded in
  `decisions_taken`; (b) naming `_prev_season_full` / `appearances_prev_full` was surfaced in the
  plan and CPO-accepted at ExitPlanMode. No metric invented, no metric_catalogue.csv change, the
  #638 5-metric set is preserved exactly — the new columns are uncatalogued windowed variants
  matching the existing `*_prev_season` / `*_delta_yoy` precedent. No product/UX or permanent
  decision that should have been the CPO's was taken here.

## analytics-engineer-reviewer
VERDICT: PASS  (round 2 on the reordered hash; round 1 also PASS on hash 8bec99fa)
risks_checked:
- **`prev_full` correctness / grain / fan-out.** `prev_full` mirrors `prev` (same `inner join cur`,
  same `season_api_year = cur_season - 1`, same `qualify row_number() over (partition by team_sk,
  player_sk, league_code order by match_number desc) = 1`) minus only the `<= appearances_cutoff`
  cap, so it deterministically returns the prior season's full-season row. `match_number` is a
  strict `row_number()` (int_player_season_record.sql:36), never tied, so the qualify picks exactly
  one row; both LEFT JOINs are 1:1 — the grain `(team_sk, player_sk, league_code, season_api_year)`
  is preserved (matches the unchanged `unique_combination_of_columns` test).
- **Invariant test soundness.** `full >= pace-matched` is algebraically guaranteed: every metric is
  a monotonic cumulative `sum() over w` (or `row_number()` for appearances), so a larger
  `match_number` never yields a smaller value. Proven that a `prev_full` row can never exist without
  a `prev` row (`prev`'s cap is satisfiable at `match_number = 1` whenever `cur` exists, since
  `appearances_cutoff >= 1`), so the `appearances_prev is null or (...)` guard cannot silently mask
  a real violation. Drift guard `assert_no_uncatalogued_season_metric` verified NOT to cover this
  model (its hardcoded 3-model list excludes `int_player_profile__yoy`) → no catalogue row needed.
  Layer contract clean (no `ref('mart_*')`, no hardcoded league_code); export auto-carry verified
  via `_strip_identity` (no export edit); final SELECT now ST06-compliant (simple columns before
  the calculated deltas), matching the sibling `int_team_profile__yoy`; no line > 120 chars.

## escalations
- None. No open escalations; no ESCALATE verdict raised.
