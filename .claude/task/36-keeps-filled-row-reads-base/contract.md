# Task contract — the filled-row test reads the settled base entity

objective: >
  `assert_team_keeps_its_filled_row` reads the provider attributes of the settled team from
  `base_apif__teams_global`, the model that settles them and that `dim_team` reads, and not from
  `dim_team`. The check stays as strict: a team settled on an empty row fails, the logo stays among
  the attributes that make a row filled, and the Chelsea case is unchanged. The change makes the
  test independent of what `dim_team` publishes as the logo, so the hosted-crest change (MR !516)
  does not turn the test red for a team whose only provider attribute is its logo.
refs: "#36, MR !516 (the pipeline job data:build:mr failed on this test with team 8103)"

scope_paths:
  - dbt_project/tests/assert_team_keeps_its_filled_row.sql
  - .claude/task/36-keeps-filled-row-reads-base/contract.md
  - .claude/task/36-keeps-filled-row-reads-base/review.md
  - .claude/task/36-keeps-filled-row-reads-base/review_input.patch

depends_on:
  - none: the change stands alone and merges before !516; on main today `dim_team.team_logo_url` equals the provider attribute, so the test passes before and after
shared_files:
  - none: no design baseline, chart manifest or chart pin changes

decisions_taken: >
  The coordinating session's message of 2026-11-22 rules the route: the check stays as strict as it
  is, the provider attributes are compared on the row where the settling happens
  (`base_apif__teams_global`), the logo is not dropped from the check and the Chelsea case is not
  weakened. No new dependency, no cost.

decisions_reserved:
  - "none: the change keeps the test's meaning and moves the model it reads"

approved_design:
  - none: no page output changes

done_when:
  - "`.venv/Scripts/dbt.exe parse --project-dir dbt_project` passes and the test passes in the merge request's data build."
  - "On the `ci_mr516_012094f0` build the test passes for team 8103 and still reports the Chelsea case when its filled row is removed."

amendments: (none)
