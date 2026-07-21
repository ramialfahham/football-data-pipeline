# Task contract — TASK 0 part 2 of 2: the two guards that stop the meaning gaps coming back

> Written on a CLEAN tree (branch `feat/metric-layer-guards` off main @ 8f9c320, which is PART 1
> merged). Part 1 landed the seed VALUES; this lands the machine gates that make the gaps
> un-reintroducible. Together they complete the CPO's three-step TASK 0.
> See [[feedback-metric-catalogue-governance]] [[feedback-agent-guardrails]].

objective: >
  Install the two dbt guards TASK 0 requires, plus the `seeds/schema.yml` prose that describes them.

  (b) Widen the meaning-completeness guard to EVERY metric.
      `assert_team_metric_meaning_complete` -> `assert_metric_meaning_complete`, with the
      `entity in ('team','team and player')` predicate DROPPED, so it fails if ANY row has an empty
      `direction` or an empty `interpretation`. That team-only scope is precisely why 28 player rows
      sat empty and nothing complained. Renamed because the old name is what made a provisional scope
      look permanent.

  (c) Lock `direction` and `lower_is_better` together.
      NEW `assert_metric_direction_lower_is_better_agree` fails on EITHER mismatch
      (`lower_is_better=true` with a direction other than `lower_better`, and `lower_is_better=false`
      with `direction='lower_better'`) and on a NULL boolean. Both sides are checked deliberately: a
      one-sided guard would have passed on all 4 of the rows part 1 corrected.

  WHY THIS IS A SECOND MERGE, and why it can only run NOW. The PR-only CI step
  `dbt test --select test_type:singular --defer --favor-state --state /tmp/main-state` defers every
  node it did not select, and `dbt test` can only ever select TEST nodes, so the `metric_catalogue`
  seed is never selected there and `ref('metric_catalogue')` resolves to a manifest compiled from
  MAIN at the prod target. These guards therefore read MAIN's catalogue, not the branch's. That is
  fine now and only now: part 1 merged, its main-push build ran `dbt seed --target prod`, and prod's
  catalogue is correct. Running this PR before that build finished would have reproduced the same red.

refs: >
  Verified this session, at source and against live BigQuery:
  - Part 1 is merged: main @ 8f9c320 carries all 28 `interpretation` values and the 4
    `lower_is_better` corrections. `dbt_analytics.metric_catalogue` must show 0 blank-meaning rows
    and 0 direction disagreements before this PR is pushed — CHECK THIS, do not assume it.
  - Both guards were validated against BigQuery with `bq query --dry_run` (they compile) and run
    live: against the PRE-part-1 catalogue the meaning guard returned 28 rows and the lockstep guard
    returned exactly the 4 named rows; against the corrected catalogue both return zero. Non-vacuous.
  - `lower_is_better` loads from the seed as BOOLEAN (confirmed on the built table), so the lockstep
    guard needs no cast.
  - `dbt parse` and SQLFluff CANNOT run locally — both are broken (SQLFluff uses the dbt templater).
    CI is the gate. [[reference-dbt-singular-test-from-clause]]
  - The existing `{{ config(severity = 'error') }}` and `{{ config(tags=[...]) }}` usages in
    `dbt_project/tests/` are the precedent for a config block in a singular test.

scope_paths:
  - dbt_project/tests/**
  - dbt_project/seeds/schema.yml
  - .claude/active_work.md
  - .claude/task/**

impact_map: >
  writers: `dbt_project/tests/` — one test renamed and widened (its predicate loses the entity
    filter), one test added. `dbt_project/seeds/schema.yml` — PROSE only, the descriptions that name
    the old test or assert the retired team-only exemption. No seed VALUE, no dbt model, no export
    script, no workflow, no `site/`, no `site_v2/`.
  downstream — the warehouse: none. `dbt test` reads; it writes nothing. Zero rows move, zero numbers
    move, and no table is built differently.
  downstream — the live MVP: none. No seed value changes and no export runs.
  downstream — CI: two additional invariants now fail the build when violated. Both pass against the
    current catalogue, which is why they can land at all.
  downstream — `dbt docs generate`: the schema.yml descriptions are published as truth, which is why
    the prose ships WITH the tests rather than before or after them. Leaving prose that names a
    deleted test, or that claims player rows are exempt, would publish a false statement.
  layer_rules: tests and seed documentation. No layer boundary is touched.
  deploy_order: nothing to deploy. PART 1 MUST ALREADY BE MERGED AND ITS MAIN-PUSH BUILD COMPLETE.
  blast_radius: CI only.

decisions_taken: >
  1. The widened test is RENAMED rather than edited in place, because the name carried the false
     implication that team-only was intentional and permanent.
  2. The lockstep guard checks BOTH directions of the contradiction plus a NULL boolean. The NULL
     branch looks redundant against the column's existing not_null test and is kept deliberately:
     without it a NULL makes both comparisons NULL and the guard passes in silence on the very row it
     exists to catch.
  3. `seeds/schema.yml` prose ships in THIS PR, not part 1. Every line of it asserts something about
     the renamed or the new test, so in part 1 it would have described tests that did not exist.
  4. NO CI workflow change, and no `seed_only` tagging convention. That approach was designed,
     adversarially reviewed and then ABANDONED as three new moving parts (a protected-file edit, a
     convention whose omission fails silently-green, and a lint script to police it) to avoid simply
     ordering two merges. CPO 2026-07-21: *"I have the feeling that you don't know what you're doing
     and start overcomplicating things again."* Do not resurrect it. [[feedback-no-hacky-solutions]]

out_of_scope: >
  - Any seed VALUE. Part 1 landed those and this PR must not touch the CSV.
  - Widening `assert_no_uncatalogued_season_metric` beyond its two season models (issue #530).
  - Anything in `site/`, `site_v2/`, `.github/workflows/`, or any dbt model.
  - Two pre-existing holes, LOGGED not fixed: (a) `assert_metric_catalogue_unique_by_entity` reads
    main's seed in the deferred PR step, so a PR adding a duplicate metric row would pass it;
    (b) `load_catalogue` in `export_metric_definitions_json.py` keys the catalogue by `metric_id`
    alone while the grain is `(metric_id, entity)`. Neither is introduced here and neither is
    load-bearing today.
  - The player page design. That is the next task once this merges.

decisions_reserved: >
  (none)

done_when:
  - `assert_metric_meaning_complete` exists with NO entity predicate; `assert_team_metric_meaning_complete` is gone.
  - `assert_metric_direction_lower_is_better_agree` exists and checks both sides plus NULL.
  - `seeds/schema.yml` names neither the deleted test nor any entity exemption.
  - The data-build job is GREEN, and its log shows both guards PASSING rather than skipped.
  - scope-auditor + analytics-engineer PASS.
  - CPO merges; I never merge.

verification: >
  - BEFORE PUSHING: query `dbt_analytics.metric_catalogue` and confirm 0 blank-meaning rows and 0
    direction/`lower_is_better` disagreements. If prod is not yet reseeded, the PR will go red for
    the same reason as before. This is the one check that must not be skipped.
  - Re-derive both guards' predicates directly against the seed CSV: both return zero.
  - `bq query --dry_run` on both compiled predicates (dbt parse and SQLFluff are broken locally).
  - Read the actual CI run and confirm the two guards appear in the singular-test step and PASS.

amendments: (none)
