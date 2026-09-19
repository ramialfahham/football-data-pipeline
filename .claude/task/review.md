# Review — feat/109-store-failures-and-severity — 2026-09-19

diff_sha256: 0feacb6e28c5771de090785ace36c126896472d2a163974d90f491359be71261

rounds: 3

Round 3 (delta): the contract's cost paragraph and `done_when` corrected — the two `freshness_check`
tests run only in the nightly's unfiltered `dbt build`, `fdp-freshness` is a Python metadata
sentinel (verdict then: FAIL by the warehouse reviewer at round 2, resolved here); the cost is
under 1 GB a day. No `.sql` changed since round 1. The handover and the tracker snapshot are in
scope, read from disk, excluded from the patch by routing.

Round 2 (delta): `docs/tracker/gitlab_snapshot.md` added to `scope_paths` (the standing snapshot
rule); `done_when` 54 → 52 tables for the MR job (`--exclude tag:freshness_check`). Pipeline
2863729019 green: `PASS=51 WARN=1 ERROR=0`, 52 audit tables in `ci_mr211_dbt_test__audit`.

## scope-auditor
VERDICT: PASS
risks_checked:
- Round 3: the correction touches only the cost sentence and one `done_when` clause; checked
  against `deploy/nightly/entrypoint.sh:53-55` (unfiltered `dbt build --target prod`, the comment
  "freshness_check is deliberately NOT excluded") and `scripts/check_raw_freshness.py` (no dbt);
  the amendment cites a reviewer finding, not a CPO quote, and says the first commit message still
  carries the stale sentence rather than rewriting history; the cost went down and is still a
  number; no scope path, attribution or §10 decision added.
- Round 2: the scope addition matches `CLAUDE.md`'s standing snapshot rule; the 52 matches the
  `--exclude tag:freshness_check` on `data:build:mr`; `decisions_taken` / `decisions_reserved`
  unchanged; `.claude/active_work.md` read from disk attributes only the 2026-09-19 plan approval
  and the named merges to the CPO.
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
- Round 3: the round-2 finding (the contract said the two `freshness_check` tests run hourly under
  `fdp-freshness`) is resolved — the corrected paragraphs match `deploy/nightly/entrypoint.sh:53-55`
  and `deploy/nightly/README.md:198-219` (`--command python --args scripts/check_raw_freshness.py`);
  "excluded from every CI dbt job" holds: `.gitlab-ci.yml:727`, `:784`, `:844` carry the exclude and
  `dbt_project/selectors.yml`'s `downstream` selector bakes it in; the cost figure is consistent
  at order of magnitude; the amendment's attribution is what round 2 found.
- Round 2, the finding: `fdp-freshness` runs no dbt; the two tagged tests' only writer is the
  nightly's unfiltered build, once a day, not hourly — a caller identified by its name, the trap
  `CLAUDE.md` names for `github-actions-dbt@…`.
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
