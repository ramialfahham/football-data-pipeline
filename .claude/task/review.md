# Review — feat/109-store-failures-and-severity — 2026-09-19

diff_sha256: a7dec0102a190830aa0f5a9a4e07cb3ee66b3d55bffa26bcd2c8d2a7db95d0ae

rounds: 1

## scope-auditor
VERDICT: PASS
risks_checked:
- Scope: all 49 touched `.sql` files sit directly under `dbt_project/tests/`, matching
  `scope_paths: dbt_project/tests/*.sql`; only `.claude/task/contract.md` is touched otherwise, also
  in scope. No model, yml or Python file appears in the diff.
- Config form: every hunk either adds `store_failures = true` inside an existing `config(...)` as a
  new key or adds a standalone `{{ config(store_failures = true) }}` where none existed. No hunk
  removes or overwrites a `severity`, `tags` or other config key; every config line is additive.
- Severity flips: the three `warn` flips each carry a one-line WHY and apply §3.3's literal test
  ("the condition is correct but worth seeing → warn"), not an analogy (Appendix A3 held). The seven
  `*_covers_active_competition_var` tests and every other `error` test are untouched, consistent
  with the contract's rationale.
- `decisions_taken` / `decisions_reserved`: no §10 class is taken; mechanical application of
  §3.3/§3.4 already in `engineering_standards.md` (!201); `decisions_reserved: none` defers the
  per-line ruling to the merge of the 54-line MR-head table, the documented mechanism.
- Recurring-cost / new-mechanism tripwire: declared with a number (~$0.15/month, 49 extra small
  tables per run); the mechanism is the one 5 tests already use; no new dataset, feature or schedule.
- Secrets sweep of all 49 hunks and the contract diff: nothing credential-shaped.
- Impact map: only `dbt_project/tests/**` touched, not the structural surface; none required.

## analytics-engineer-reviewer
VERDICT: PASS
risks_checked:
- All 54 files under `dbt_project/tests/*.sql` carry `store_failures` exactly once; no duplicates,
  no misses.
- Placement: every added config sits after the `{# #}` or `--` header and before the SQL, or is
  merged into an existing `config(...)` with a comma (the three multi-line blocks and the
  `-- depends_on:` file checked) — valid Jinja in each case.
- No test lost `severity`, `tags` or any other key; no SQL body line changed — every hunk touches
  only the config line plus, where none existed, one blank line.
- `severity = 'warn'` count is exactly 4, matching `done_when`.
- The three flipped tests read in full: each compares an override seed row against the pre-override
  provider value and fires only when the override is identical to or orphaned from it; since
  `coalesce(override, provider)` shows the same name either way, no fan-visible value changes on a
  dead row — §3.3's question holds.
- Every other singular test scanned for a correct-but-notable state that should also flip (Home
  leaderboard leader, top-teams leader, competition name, event loss, stale live, slug alphabet):
  each asserts a defect a fan would see; no further candidate.
- Table-name collision: one flat directory, no two tests share a stem, no audit-table collision.
- `generate_schema_name.sql` and `dbt_project.yml`: no project-level `tests:` block, no schema
  override added; the audit-dataset naming rides the existing target prefix — no new mechanism.
- Recurring cost: `store_failures` writes the compiled test query as a table, then counts that small
  table; "the extra billed work is the count" matches the mechanism and is not an understatement.

## escalations
(none)
