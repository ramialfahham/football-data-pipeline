# Task contract — fix stale "no reader" claims in layering.md for dim_country/dim_region

objective: >
  `dbt_project/docs/layering.md` records dim_country/dim_region (#69) as a documented exception to
  the layer-contract rules requiring reuse/rollup consumers before a table earns `dim_` status,
  because at the time they shipped with zero readers. MR !65 (merged 2026-08-17, #69 step 5 + #62
  step 3) gave them real readers the same day: four `relationships` tests and
  `mart_competition_index`. The doc's "no reader at all" / "zero consumers" claims are now false.
  Fix them in place; the historical record of the exception itself stays, only the still-current-
  ness of "no reader" is corrected.
refs: GitLab #69, #62, MR !65 (already merged)

scope_paths:
  - dbt_project/docs/layering.md

decisions_taken: >
  No new CPO decision. This corrects a factual claim in documentation to match a change already
  reviewed, approved and merged in !65 — the exception itself (that these dims were allowed to
  ship ahead of a consumer) is CPO-ruled and already recorded in `escalations.log`
  (2026-08-17, `feat/69-country-region-dims`); this task does not revisit that ruling, only the
  doc's now-stale "still has no reader" wording.
  NEW MECHANISM: none. RECURRING COST: none.

decisions_reserved:
  - none: a doc correction against an already-merged, already-reviewed fact.

done_when:
  - Both stale "no reader"/"zero consumers" claims for dim_country/dim_region in layering.md are
    corrected to state they are now read, without erasing the historical record of why the
    exception was granted.
  - No other content in the file changes.

amendments: (none)
