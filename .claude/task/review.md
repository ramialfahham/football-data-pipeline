# Review — feat/metric-layer-guards (TASK 0 part 2, THE GUARDS) — 2026-07-21

> Part 2 of 2. Part 1 (#681, the seed VALUES) is MERGED at main @ 8f9c320. This commit adds the two
> guards that make the meaning gaps un-reintroducible, plus the `seeds/schema.yml` prose naming them.
> Required reviewers per `.claude/review_routing.json`: scope-auditor (always) ·
> analytics-engineer-reviewer (`dbt_project/**`). Both PASS, first round.
> `football-analytics-expert-reviewer` is NOT required here: it routes on
> `dbt_project/seeds/metric_catalogue.csv`, which this commit does not touch.

diff_sha256: 68a20c95f7af1512f9cf5af5aad005bfcddbc98742c20fc4fa3a8142e326a17d

## scope-auditor
VERDICT: PASS
risks_checked:
- Entity-predicate removal is structural and complete. The old test carried `entity in ('team', 'team and player')`, which exempted player-only rows and is exactly why 28 sat empty. The new `assert_metric_meaning_complete` has ZERO entity filtering in its WHERE clause, so the exemption is unreintroducible without an obvious edit. Verified the old file is DELETED, not kept alongside — it appears in the patch as a deleted file.
- The widened guard fails on a blank `direction` OR a blank `interpretation`, for ANY entity; both branches present, joined by OR, no entity reference anywhere in the file.
- Bidirectional contradiction checking is implemented, not one-sided. Three branches: `lower_is_better and direction != 'lower_better'`, `not lower_is_better and direction = 'lower_better'`, and `lower_is_better is null`. A one-sided guard would have PASSED on all four rows part 1 corrected (`cards_yellow`, `cards_red`, `cards_total`, `shots_on_goal_against`), which is the trap the docstring names. The NULL branch is justified by SQL three-valued logic: without it a NULL boolean makes both comparisons NULL and the guard passes in silence.
- Residue of the ABANDONED CI approach: NONE survives. Grepped the whole repo for `seed_only`, `check_seed_only_test_tags`, and any `.github/workflows/` change. The only occurrences are prose in the contract and handover explaining that the approach was rejected and must not be resurrected.
- No seed VALUE is touched. `dbt_project/seeds/metric_catalogue.csv` is not in the diff; part 1 owns it.
- Config-as-code: `seeds/schema.yml` names the new tests by their real names, no longer names the deleted `assert_team_metric_meaning_complete`, and no longer asserts any entity exemption ("there is no entity exemption"). Nothing false is published through `dbt docs generate`.
- Handover honesty: part 1 is recorded as MERGED (#681) and part 2 as THIS branch, with the ordering constraint and the abandoned-approach warning intact for a cold chat.
- Every changed file is inside `scope_paths`.

## analytics-engineer-reviewer
VERDICT: PASS
risks_checked:
- Full 78-row hand-walk of `dbt_project/seeds/metric_catalogue.csv` on main, not a sample: `lower_is_better` and `direction` agree on all 78 including the 4 corrected rows and both `neutral` rows (`sot_rank_gap`, `contribution_share`, correctly paired with `lower_is_better=false`); no row has a blank `direction` or `interpretation`. Both new predicates return ZERO rows against the real current catalogue.
- Three-valued-logic trace on the lockstep guard: a NULL `lower_is_better` makes branches 1 and 2 evaluate NULL/FALSE, but branch 3 is unconditionally TRUE, so the OR chain always fires. No silent pass. The `lower_is_better is null` branch is redundant against the column's `not_null` test only at whole-build level; for this test in isolation it is not, so it is justified defence in depth rather than noise.
- Padding/case defence traced as a counterfactual: without `coalesce(trim(direction), '')` a padded `" lower_better "` beside `lower_is_better=false` would NOT be flagged, because literal string inequality masks the real mismatch. The trim is substantive, not decoration. Mis-cased values are caught independently by the column's `accepted_values` test, so case sensitivity here is consistent with the rest of the suite.
- The CI-mechanism claims in BOTH docstrings were cross-checked against `.github/workflows/ci-data-build.yml:132-138` and `:187-227` rather than accepted. The mechanism is accurate: `dbt test` only ever selects test nodes, so the seed is unselected and `--favor-state` forces it to the state manifest compiled from main at the prod target, regardless of what `dbt seed --target ci` just wrote. An inaccurate comment inside a guard would be worse than none; these hold.
- Config-as-code: `seeds/schema.yml` lists exactly the three metric-catalogue guards that actually exist in `dbt_project/tests/`, names no deleted test, and claims no player exemption. Grepped `dbt_project/docs/*.md` for stale references to the old name — none outside historical task files.
- SQLFluff style judged against the nearest sibling group (`assert_metric_catalogue_expr_resolvable`, `assert_metric_catalogue_unique_by_entity`, `assert_no_uncatalogued_season_metric`): lowercase keywords, `!=` not `<>`, `where` on its own line with indented `and`/`or`, no config block — consistent. Both have a proper FROM clause, avoiding the known FROM-less-WHERE trap. Local lint could not run (the dbt templater is broken), so CI remains the gate.
- Scope and residue: changed files match `scope_paths` exactly; no `seed_only` tag and no workflow edit survive anywhere; `metric_catalogue.csv` untouched.

## escalations
(none)
