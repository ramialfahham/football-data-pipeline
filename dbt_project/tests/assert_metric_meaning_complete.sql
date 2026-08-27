{#
  Meaning/context completeness guard (metric layer). The metric_catalogue is the authoritative
  source of each metric's meaning, so EVERY metric — team, player, or both — must carry BOTH a
  performance `direction` and an `interpretation` — the seed of the website's good/bad reading and
  auto-narrative. The test FAILS (returns rows) for any metric missing either.

  Scope = every row, DELIBERATELY. This guard used to be team-scoped
  (`assert_team_metric_meaning_complete`, `entity in ('team', 'team and player')`), and that
  narrowing is exactly why 28 player rows sat with a blank `interpretation` while nothing complained
  — the guard could not see them. The catalogue-wide direction sweep populated `direction` on every
  row, and the player `interpretation` sweep filled the remaining 28, so the exemption has no
  justification left. Do NOT reintroduce an entity predicate: an exemption here is invisible by
  construction. (CPO 2026-06-29; broadened to every entity 2026-07-21.)

  Companion guard: `assert_metric_direction_lower_is_better_agree` stops `direction` and the legacy
  `lower_is_better` boolean asserting different things about the same metric.

  Blank cells load from the seed as NULL or empty string depending on quoting, so guard both.

  CI note, REWRITTEN 2026-08-27 under #92 — the previous version of this paragraph is now false in
  every particular, and it is kept in git rather than paraphrased. It said: on a PR this runs in the
  deferred singular-test step, where `ref('metric_catalogue')` resolves to MAIN's seed rather than
  the branch's, because `--favor-state` swaps it for the state relation; that a change to catalogue
  VALUES and a guard depending on those values therefore cannot land in the same PR; and — the line
  that mattered — "Do not try to solve this with a CI workflow change."

  It was solved with a CI workflow change, with the CPO's approval. `--favor-state` is gone from
  `data:build:mr`'s `dbt test` invocation, and `dbt seed --target "$DBT_CI_TARGET"` runs before it
  in the same job, so the BRANCH's `metric_catalogue` relation always exists in that target and
  plain `--defer` prefers a relation that exists over the deferred one. **This guard now reads the
  branch's seed, so catalogue values and a guard that depends on them CAN land in the same PR.** Do
  not split a change on the strength of the old rule.
  ⚠ There is no shared `ci` target any more: the CI target is named per merge request
  (`ci_mr<IID>`), so this seed lands in that merge request's own dataset and no other branch can
  read or overwrite it.
  ⚠ Also still true: `--favor-state` remains on the sibling `dbt build` invocation, deliberately.
  Both that asymmetry and the per-merge-request naming are pinned in
  `tests/test_ci_data_job_invariants.py`.
#}

select
    metric_id,
    entity,
    direction,
    interpretation
from {{ ref('metric_catalogue') }}
where
    direction is null or trim(direction) = ''
    or interpretation is null or trim(interpretation) = ''
