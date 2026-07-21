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

  CI note: on a PR this runs in the deferred singular-test step, where `ref('metric_catalogue')`
  resolves to MAIN's seed rather than the branch's (`dbt test` can only select test nodes, so the
  seed is never selected and `--favor-state` swaps it for the state relation). That is why a change
  to catalogue VALUES and a guard that depends on those values cannot land in the same PR — the
  values merge first, then the guard. Do not try to solve this with a CI workflow change.
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
