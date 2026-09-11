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
  construction.

  Companion guard: `assert_metric_direction_lower_is_better_agree` stops `direction` and the legacy
  `lower_is_better` boolean asserting different things about the same metric.

  Blank cells load from the seed as NULL or empty string depending on quoting, so guard both.

  CI note. On a merge request this guard reads the BRANCH's seed: `--favor-state` is absent from
  `data:build:mr`'s `dbt test` invocation, and `dbt seed --target "$DBT_CI_TARGET"` runs before it
  in the same job, so the BRANCH's `metric_catalogue` relation always exists in that target and
  plain `--defer` prefers a relation that exists over the deferred one. **Catalogue values and a
  guard that depends on them CAN land in the same merge request.** Do not split a change on the
  strength of the opposite (once true) rule.
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
