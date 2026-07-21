{#
  Lockstep guard (metric layer): `direction` and the legacy `lower_is_better` boolean describe the
  same property of the same metric, so they must never assert different things. The test FAILS
  (returns rows) for any metric where they disagree.

  Why it exists. `direction` (higher_better / lower_better / neutral) is the richer successor and the
  authority; `lower_is_better` is retained only because the live MVP export
  (`scripts/export_metric_definitions_json.py`) still reads it. Nothing checked that the two agreed,
  and by 2026-07-21 four rows contradicted each other (`cards_yellow`, `cards_red`, `cards_total`,
  `shots_on_goal_against` — each `lower_is_better = false` beside `direction = 'lower_better'`). Two
  columns saying opposite things about one metric is precisely the "surprising ambiguity" this layer
  must not contain. The four were corrected to follow `direction`, and this guard landed with the
  fix. (CPO 2026-07-21.)

  BOTH sides are checked on purpose. A guard that only caught `lower_is_better = true` beside a
  non-lower_better direction would have passed on all four of the rows that were actually wrong.

  `neutral` is a real direction with no better/worse pole, so it must pair with
  `lower_is_better = false` — asserting "lower is better" about a metric with no pole is itself a
  contradiction. The first branch covers that.

  Two defensive touches that are not redundancy. `coalesce(trim(direction), '')` stops a NULL or
  padded direction from making the comparison NULL and slipping a disagreement through silently
  (`accepted_values` on the column ignores NULLs, and `assert_metric_meaning_complete` is a separate
  test that could be failing in the same run). The `lower_is_better is null` branch is kept for the
  same reason: without it a NULL boolean makes both comparisons NULL and this guard passes in
  silence on the very row it exists to catch. `lower_is_better` loads from the seed as BOOLEAN
  (verified against the built table), so no cast is needed.

  CI note: on a PR this runs in the deferred singular-test step, where `ref('metric_catalogue')`
  resolves to MAIN's seed rather than the branch's (`dbt test` can only select test nodes, so the
  seed is never selected and `--favor-state` swaps it for the state relation). That is why the 4
  corrections this guard depends on merged FIRST, in their own PR, before the guard followed. Do not
  try to solve this with a CI workflow change.
#}

select
    metric_id,
    entity,
    lower_is_better,
    direction
from {{ ref('metric_catalogue') }}
where
    (lower_is_better and coalesce(trim(direction), '') != 'lower_better')
    or (not lower_is_better and coalesce(trim(direction), '') = 'lower_better')
    or lower_is_better is null
