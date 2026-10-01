# Review — fix/staging-stage-runs-only-staging-tests — the prod build's staging stage runs no test that reads a later layer

diff_sha256: 5d39d24002eafaa23f45e623b8961e8c9f2111ceee2c47debfef20309ec49546

rounds: 2

## scope-auditor
VERDICT: PASS
risks_checked:
- Scope: the diff touches dbt_project/selectors.yml, tests/test_ci_data_job_invariants.py and the task artifacts, all in scope_paths; the test file's amendment names its authority (the CPO's go for this fix and the working agreement's §7).
- §10 and Appendix A: a selector narrowed and a pin test added; no metric, naming, UX, model, cost or cadence change, no new mechanism; the builder reading (all four later layers, not only base) is declared in decisions_taken.
- Recurring cost: one test moves from the staging stage to the downstream stage, which already runs it; query volume and cadence unchanged.
- Doc-sync: the documents that mention `--selector staging` show the command, not what it selects, so none goes stale.
- Coverage: the moved test is not removed; the downstream stage selects it and it still blocks the writes after it.

## analytics-engineer-reviewer
VERDICT: PASS
risks_checked:
- The failing mechanism: assert_base_player_stats_cleaned reads stg_apif__fixture_players and four base models, so dbt's eager selection put it in the staging stage against the previous build's base; excluding the 2_base, 3_core, 4_intermediate and 5_marts paths removes exactly that class of test.
- The moved test still runs after its parents and still blocks: the downstream selector (2_base to 5_marts, freshness_check excluded) selects it, and the trailing singular-test step runs it too.
- The tests that read staging and seeds only (the two override checks, test_stg_fixture_statistics_non_empty) keep no later-layer parent and stay in the staging stage.
- A freshness_check-tagged test reading staging and a later layer would run in neither build stage; there is none today.
- No other selector, model, seed or grain changes; the impact map names the only runner of the selectors, data:build:main, and that the nightly and the MR build do not use them.

## platform-reviewer
VERDICT: PASS
risks_checked:
- Round 1 FAIL: no test pinned the stage partition, so a revert would stay green until a merge's prod build failed. Round 2: test_the_staging_stage_excludes_every_layer_the_downstream_stage_builds asserts that data:build:main builds staging then downstream and that every path the downstream union builds is in the staging selector's exclude lists; traced red against main's selectors.yml, against a removed exclude, and against a single dropped layer (it names models/3_core), matching the builder's watched-red runs.
- Fail-closed: a plain assert with no skip; a layer added to downstream but not excluded from staging fails it, and a renamed job key raises.
- Selector syntax: the union-with-exclude form is the one the downstream selector already uses; the moved test keeps its write-blocking run in the downstream stage and its trailing run.
- Limit: the test pins the partition's YAML shape, not per-test placement (the 62-selected, one-dropped figure is the builder's dbt ls measurement); acceptable for a selector change, since a revert or a missed layer goes red before merge.

## escalations
(none)
