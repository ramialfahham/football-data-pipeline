# Review — feat/886-featured-season-dq-test — 2026-08-02

branch: feat/886-featured-season-dq-test
diff_sha256: 9af1ff3087a7f1dc320f7c2fc8bbd764610653b372fa25da84eba2494021adaf
# One-commit branch, so `--staged-hash` and the cumulative `origin/main...HEAD` hash coincide. They
# diverge on a second commit; take it from `check_task_artifacts.py --base origin/main` if one is
# ever needed here.

rounds: 1

## scope-auditor
VERDICT: PASS
risks_checked:
- All three changed paths are covered by `scope_paths`: `contract.md`, `shared.yml` and the restored
  test. No out-of-scope edit.
- The claimed authority is an EXISTING ruling, not a new one. Verified the CPO's "do 1 now"
  (2026-08-02) in `escalations.log` and that it says what the contract says: the automated half
  lands in #886 once prod carries the column. This is #886.
- No §10 decision is taken. Restoring a test that implements a locked, approved criterion is
  mechanical implementation of a decision already on the record, not a new one.
- Threshold declarations are accurate: a singular test is an existing resource type with 28 already
  in `dbt_project/tests/`, and it runs inside the existing `test_type:singular` step rather than
  adding a scheduled invocation.
- The `shared.yml` comment edits remove stale "deferred to #886" text rather than adding a second
  version alongside it, which is the standing rule that a correction replaces.
- `decisions_reserved: none` is honest: any disagreement about whether the test should differ from
  the version that passed in #884 is a reviewer finding, not a builder decision.
- The `impact_map` short-form is supported by pasted evidence rather than asserted from memory.
- Appendix A: no spot-fix without a map, no coverage cut, no assert-before-measure. A guard is
  restored after its precondition was met.

## analytics-engineer-reviewer
VERDICT: PASS
risks_checked:
- The test SQL is valid BigQuery and catches both halves: `countif(is_featured_season)` grouped per
  entity with `where featured_seasons != 1` flags zero and two alike. Selecting
  `cast(team_sk as string)` alongside `group by team_sk` is legal, since the expression is built
  purely from the grouped column.
- `is_featured_season` can never be NULL: it is `row_number() over (...) = 1`, a boolean comparison
  against a window function that never returns NULL, so `countif` behaves as a strict boolean count.
  Consistent with the `not_null` tests already on both marts.
- The `union all` cannot hide a failure through key collision: each side is pre-aggregated and
  carries its own `entity_kind` literal, and no join or dedup happens after the union that a
  numerically identical `team_sk`/`player_sk` could defeat.
- "Two" is additionally guarded upstream by the pre-existing
  `dbt_utils.unique_combination_of_columns` on `(team_sk, season_sk)` and `(player_sk, season_sk)`.
- The "RECURRING COST: none" declaration is accurate: `ci-data-build.yml` already runs
  `dbt test --select test_type:singular` on both the PR and main-push paths, so the test rides an
  existing step.
- Both corrected `shared.yml` comments now describe what actually guards the column, and no stale
  "deferred" language remains anywhere in the file.
- The leaf-mart claim holds: no `ref()` to either profile mart exists anywhere under
  `dbt_project/models/`, so nothing downstream can break.
- The byte-identity claim could not be re-executed from a read-only toolset, so it was cross-checked
  against `escalations.log`, which independently corroborates the same SQL, the same row counts and
  the same ruling. No contradiction found in the repo.

## escalations
(none)
