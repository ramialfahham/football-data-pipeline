# Task contract — restore the exactly-one-featured-season DQ test (#886)

> Written on a clean tree before any file was touched. Branch `feat/886-featured-season-dq-test`
> from `main` at `79317d3`. No protected path in scope, so no `protected_override`. No
> `dbt_project/models/**`, `ingestion/**`, `scripts/export_*.py` or `site*/` path in scope, so
> `impact_map` is not gate-required; a one-line evidenced short-form is given anyway.
> No `site_v2/src/` path in scope, so no `acceptance_criteria`.

objective: >
  Close out #846's acceptance criterion 4 by restoring the test that was written, reviewed and
  PASSED there, then split out on the CPO's ruling because prod did not yet have the column it
  reads. Prod has it now.

  `is_featured_season` marks the one season an entity's page opens on. "Never two" already holds by
  construction (`row_number() = 1`) and `not_null` on the column shipped with #846. The half still
  uncovered is "never none", which a future rewrite of the window expression could introduce
  silently. This test is what makes that loud.

refs: >
  #886. Restores `dbt_project/tests/assert_one_featured_season_per_entity.sql` from `5479ef5^`
  UNCHANGED — the exact file `analytics-engineer-reviewer` passed in #846 (PR #884, round 3).
  Precondition met: main-push `ci-data-build` completed successfully after #884 merged, so prod's
  `mart_team_profile` and `mart_player_profile` carry the column.
  NOT in this task: #887, the CI gap that forced the split.

scope_paths:
  - dbt_project/tests/assert_one_featured_season_per_entity.sql
  - dbt_project/models/5_marts/shared/shared.yml
  - .claude/task/contract.md
  - .claude/task/review.md
  - .claude/task/review_input.patch
  - .claude/task/escalations.log
  - .claude/active_work.md

impact_map: >
  Short-form, and honest about why it is short: this adds a TEST, not a model. No model, no column
  and no value changes, so there is no lineage to trace and no blast radius to measure.
  `dbt ls --select mart_team_profile+ --resource-type model` and the same for
  `mart_player_profile+` each still return only themselves, so nothing downstream exists to break.
  What DOES change is a gate: the test can now fail a build that previously passed. That is the
  point of it, and the reason it is safe to add now is that it already ran green against real data
  in #884 (`ci_marts.mart_team_profile` 12.7k rows, `ci_marts.mart_player_profile` 168.5k rows).

decisions_taken: >
  Restoring a previously reviewed file unchanged, under an existing CPO ruling. The ruling
  ("do 1 now", 2026-08-02) deferred this test to a follow-up PR; this is that PR. Acceptance
  criterion 4 of #846 was never reworded, so nothing is being reinterpreted here.

  Two `shared.yml` comments say the explicit assertion "is #886 — deferred". They become wrong the
  moment this lands, so they are corrected in the same diff. That is the standing rule that a
  correction replaces rather than accumulates, applied to the thing this change makes stale.

  THRESHOLD DECLARATIONS. NEW MECHANISM: none — a singular test is an existing resource type and
  `dbt_project/tests/` already holds 28 of them. RECURRING COST: none — it runs inside the existing
  `dbt test --select test_type:singular` step, adding one query to a suite that already runs.

decisions_reserved:
  - none: this restores a file that was already written, reviewed and PASSED in #884, byte-for-byte
    unchanged, now that the precondition it was waiting on holds. If a reviewer finds it should
    differ from the version that passed, that is a finding to raise rather than a decision I make.
  - #887 may later change how this test is invoked on a PR. That is its own governance task and does
    not alter what this test asserts.

done_when:
  - `git diff 5479ef5^ -- dbt_project/tests/assert_one_featured_season_per_entity.sql` is empty,
    proving the restored file is the reviewed one and not a rewrite.
  - `dbt ls --select test_type:singular` lists `assert_one_featured_season_per_entity` again.
  - `dbt parse` clean; `sqlfluff lint` clean from the repo root, full rule set.
  - No `shared.yml` comment still describes the assertion as deferred.
  - `ci-data-build` green on the PR, which is the first time this test runs against prod's marts
    carrying the column.

amendments: (none)
