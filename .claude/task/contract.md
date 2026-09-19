# Task contract — #109 step 3, MR A: store_failures on every singular test; severity by §3.3

objective: >
  Every singular test under `dbt_project/tests/` sets `store_failures = true` (engineering_standards.md
  §3.4: a red test leaves its rows in the warehouse, not a count), and every singular test's
  severity answers §3.3's one question — would a fan see a wrong number if this condition held.
  49 of 54 tests gain the config; 3 flip from `error` to `warn`. No model, no yml, no number on the
  site changes.

refs: >
  #109, "Step 3 — the mechanisms and the sweep", MR A: the plan approved in chat 2026-09-19 and
  recorded on the issue. The rules are §3.3 and §3.4 of `dbt_project/docs/engineering_standards.md`
  (merged in !201). The form is the one the 5 tests that already carry it use
  (`{{ config(store_failures = true) }}`, e.g. `assert_season_rates_inputs_covered.sql`). The audit
  dataset is created by dbt per target: `dbt_test__audit` on prod and `ci_mr<IID>_dbt_test__audit`
  on the MR target hold the 5 existing tables today (`bq ls`, 2026-09-19).

scope_paths:
  - dbt_project/tests/*.sql
  - .claude/task/contract.md
  - .claude/task/review.md
  - .claude/task/review_input.patch
  - .claude/active_work.md

decisions_taken: >
  §3.4 applied as written: `store_failures = true` on the 49 singular tests without it, added to
  the existing `config(...)` where one exists, as its own line where none does. §3.3 applied to the
  54 singular tests, one line per test in the MR head. The three flips to `warn`:
  `assert_country_name_overrides_still_needed`, `assert_league_name_overrides_are_corrections`,
  `assert_team_name_overrides_still_needed` — a dead override row does nothing, the fan sees the
  right name either way, and the test is the reminder to delete it. Every other singular test
  stays `error`, including the seven `*_covers_active_competition_var` tests: an active
  competition with no rows is a wrong page, not a correct state, and the accepted red on an
  onboarding MR (#76) is a missing signal, not a wrong severity. The generic tests are ruled by
  their column class (§3.1 → §3.3's table) and are not touched here.

  RECURRING COST, declared: with `store_failures` a test runs the same query as a CTAS into the
  audit dataset and then counts the small table. The extra billed work is the count, at
  BigQuery's 10 MB per-table minimum: 49 more tables per run of the singular suite (the nightly
  once, `data:build:main` twice, an MR pipeline once) plus the two `freshness_check` tests hourly —
  about 1 GB a day, about $0.15 a month. Storage is the failing rows only. No new mechanism: the
  materialisation, the dataset and the form are the ones step 2 and #150 already use.

decisions_reserved:
  - none: the plan on #109 names the 3 flips and the 7 that stay; the MR head carries the full
    54-line table for his check, and his merge is the ruling on any line of it.

done_when:
  - `grep -L "store_failures" dbt_project/tests/*.sql` prints nothing; `grep -l "store_failures = true" dbt_project/tests/*.sql | wc -l` is 54.
  - `grep -l "severity = 'warn'" dbt_project/tests/*.sql | wc -l` is 4 (the 3 flips plus `assert_team_season_games_not_short_of_standings`).
  - `.venv/Scripts/dbt.exe parse` green with a scratchpad profile; `python -m sqlfluff lint dbt_project/tests --templater jinja --dialect bigquery` reports nothing new against main.
  - `data:build:mr` green; after it, `bq ls ci_mr<IID>_dbt_test__audit` lists 54 tables.
  - The MR head lists all 54 singular tests with the §3.3 answer and severity, one line each.

amendments: (none)
