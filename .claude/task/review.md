# Review — fix/73-no-mr-bootstrap-ingest — 2026-08-16

diff_sha256: 27c4d6d58890fc7629a98ad1bfc594d5c47a409d5085bc78c8674c2babc8e3bd

rounds: 2

## scope-auditor
VERDICT: PASS
risks_checked:
- Confirmed the round-1 guard-narrowing is fully reverted: the only `--exclude tag:freshness_check` present is an unchanged context line, no `prod_state` tag or per-job test exclusion appears anywhere in the diff, and zero paths under `dbt_project/` are touched.
- `scope_paths` vs changed files: diff touches `.claude/task/contract.md`, `.claude/task/escalations.log`, `.gitlab-ci.yml`, `tests/test_ci_data_job_invariants.py`. The latter three are listed in the round-2 `scope_paths`.
- Attribution of the accepted four-test-failure consequence is consistent across all three artifacts (contract impact_map, the `.gitlab-ci.yml` comment, escalations.log): all say CPO 2026-08-16, not the builder.
- escalations.log honesty: the entry names all three reviewer grounds verbatim including "the scope claim was FALSE. I wrote 'today exactly one' test. There are EIGHT... FOUR fail by construction". It does not launder the round-1 failure.
- `protected_override` cites the verbatim CPO approval for exactly the step being deleted — the same scope round 1 already judged authorized. No new mechanism smuggled in this round.
- Swept the full diff for credential-shaped strings: only env var NAMES appear, no values; no widened permissions.
- `decisions_reserved` contains nothing that is actually implemented in this diff.

## cto-reviewer
VERDICT: PASS
risks_checked:
- Verified part 2 fully reverted: `grep -rn "prod_state" .gitlab-ci.yml` returns zero hits; the diff touches exactly 4 files and no path under `dbt_project/`.
- Read `.gitlab-ci.yml` directly rather than trusting the contract: `data:build:mr` now contains no ingest call; `data:build:main` still runs `get_new_league_codes.py` then `python -m ingestion.api_football.main` unchanged. The redundancy claim holds.
- `protected_override` covers exactly what remains; `impact_map` is non-placeholder and its line references check out.
- Guard invariant: no dbt test, macro or selector is touched. The four `*_covers_active_competition_var` tests stay unconditional and fail-closed on an onboarding MR. The consequence is stated three times independently and is not minimised. No guard is loosened.
- New mechanism / recurring cost: none introduced; recurring cost is strictly negative (drops one billed `SELECT DISTINCT` per MR).
- Pinning test scoping: uses `_script_lines_by_job` (parsed YAML, per job), asserts only against `data:build:mr`, so it cannot false-positive on `data:build:main`/`data:nightly` which legitimately contain both tokens. The explanatory YAML comment naming those tokens is stripped by `yaml.safe_load` before the assertion sees it.

## platform-reviewer
VERDICT: PASS
risks_checked:
- Round-1 finding addressed: `test_mr_data_build_never_ingests` reads the parsed job body, checks only `data:build:mr`, and asserts `"data:build:mr" in jobs` first so a rename fails loudly rather than passing vacuously.
- RED-then-green demonstrated: the test was run against a re-injected `- python -m ingestion.api_football.main` line, failed with the intended message, then reverted to green. Satisfies the "verify the test fails" rule.
- Both `dbt` invocations in `data:build:mr` are back to their original `--exclude tag:freshness_check` form; `prod_state` has zero hits across `.gitlab-ci.yml` and `dbt_project/`, so the revert is total.
- No dead `$NEW_CODES` reference remains in `data:build:mr`; all three occurrences belong to `data:build:main`. `scripts/get_new_league_codes.py` is not orphaned.
- Re-run safety: the deleted step was the only prod-writing action in the job; nothing after it depends on an ingest having run, since both dbt steps read prod via `--defer --favor-state`.
- The new test runs in `test:python`, which executes unconditionally on every pipeline, so the invariant fails closed.
- No credentials or permission widening in the diff.

## escalations
(none new this round. The #73 ruling and the CPO's rejection of the guard-narrowing are recorded in `.claude/task/escalations.log`, 2026-08-16 entry.)
