# Review — test/fct-fixture-fk-guard — 2026-06-19

> PR2 of 2: restore the three suppressed `fixture_sk -> fct_fixture` FK relationship tests on the fanout
> facts (fct_fixture_player_stats / _team_stats / _event) + correct the misleading "No FK test:
> current-season snapshots only" descriptions. This is the durable guard for the idle-mode completeness
> bug, un-blocked by PR1 #514 + the zero-API recovery (0 orphans warehouse-wide; the 3 restored tests run
> green — `dbt test` on the models returned 29 PASS / 0 ERROR). Required reviewers for the staged paths:
> scope-auditor (always) + analytics-engineer-reviewer (dbt_project/**). diff_sha256 covers core.yml + contract.md.

diff_sha256: 7f4e9267fc2325800506c4327acefe7f3b6e6a68c689421516dedc5955a3c072

## scope-auditor
VERDICT: PASS
risks_checked:
- FK relationship test under the append-complete-snapshot contract: the diff restores the referential-integrity guard that was deliberately suppressed to mask the idle-mode bug; severity is error (hard-fail) and it targets the correct key (fanout fixture_sk -> fct_fixture.fixture_sk) across all three fanout facts. Data is consistent post-recovery (0 orphans); a future orphan would hard-fail and block merge. In scope (core.yml + task artifacts only); undoes a masked-test anti-pattern without weakening any other test.
- Description accuracy + no silent §10: the new description replaces the misleading "current-season snapshots only / No FK test" text with an accurate statement of the carry-forward invariant (PR #514) — a technical clarification, not a metric/product/naming decision. CPO-directed ("PR2 now"); decisions_reserved limited to the build-detail test-form choice. No external doc inventory requires updating.

## analytics-engineer-reviewer
VERDICT: PASS
risks_checked:
- Rebuild-order coupling (incremental fanout vs full-refresh fct_fixture): the `relationships` test fires at warehouse-query time, not DAG build time, so it is not flaky under a normal `dbt build`; the only failure mode is a partial build that omits fct_fixture (operator error), and the carry-forward precondition is now documented in the description (PR #514). Not a data defect.
- Referential direction + field-name correctness: `fct_fixture.fixture_sk` is `fixture_api_id` cast to INT64 with `not_null, unique`; all three fanout facts carry `fixture_sk` on the same domain; each restored `relationships` block resolves `field: fixture_sk` to the correct parent grain key. Layer-contract clean (core→core relationship test is sanctioned by layering.md Testing Guidance). No previously-active test weakened or removed.

## escalations
(none)
