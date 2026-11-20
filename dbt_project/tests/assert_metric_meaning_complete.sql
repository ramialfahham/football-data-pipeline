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

  Blank cells load from the seed as NULL or empty string depending on quoting, so guard both.

  CI note. On a merge request this guard reads the BRANCH's seed: a changed `metric_catalogue` is
  selected by the lineage build in `data:build:mr` (`state:modified+` and the changed seed's path),
  and dbt never defers a node it selects. **Catalogue values and a guard that depends on them CAN
  land in the same merge request.**
  ⚠ The CI target is named per merge request (`ci_mr<IID>_<SHA>`), so this seed lands in that
  merge request's own dataset and no other branch can read or overwrite it; the naming is pinned in
  `tests/test_ci_data_job_invariants.py`.
#}
{{ config(store_failures = true) }}

select
    metric_id,
    entity,
    direction,
    interpretation
from {{ ref('metric_catalogue') }}
where
    direction is null or trim(direction) = ''
    or interpretation is null or trim(interpretation) = ''
