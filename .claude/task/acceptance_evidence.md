# Evidence — #92: the MR singular-test gate now reads the branch, not production

Branch `fix/92-singular-tests-read-the-branch`, from main `1804a64`.
No `site_v2/src/` path is in scope, so the acceptance gate does not fire and there are no
`acceptance_criteria` to demonstrate. This file carries the verification instead.

## The change, in full

```
- dbt test --select test_type:singular --exclude tag:freshness_check --defer --favor-state --state /tmp/main-state --target ci
+ dbt test --select test_type:singular --exclude tag:freshness_check --defer --state /tmp/main-state --target ci
```

One flag, on one invocation. Everything else in the diff is the comment above it.

| check | result |
|---|---|
| flag diff, from `git diff -U0` | exactly one `-`/`+` pair; `--defer` retained, `--favor-state` removed |
| `dbt build` invocation | **byte-identical** — still `--defer --favor-state`, deliberately |
| `.gitlab-ci.yml` parses as YAML | yes; `data:build:mr` still has **13** script steps, same as main |
| selection string | unchanged — `--select test_type:singular --exclude tag:freshness_check`, so the suite size cannot drop |
| `allow_failure` / `|| true` / new tag / new exclusion | none introduced; the job still fails closed |
| `python -m pytest -q tests/test_ci_data_job_invariants.py` | 4 passed |
| `python -m pytest -q` (full) | see below |

## What the flag actually does, verified against the failing job rather than from memory

`--favor-state` makes dbt resolve a `ref()` to the deferred (prod) relation **even when the current
run has just built that model**. The proof is in one job, ninety seconds apart —
pipeline `2796272877`, job `16145201830`, on `!114`:

| line | event |
|---|---|
| 836 | `OK created sql table model ci_marts.mart_team_season_insights` — with the renamed column |
| 854 | `PASS assert_mart_team_season_insights_metric_consistency [PASS in 0.75s]` — inside `dbt build`, against that freshly built table |
| 1021 | the SAME test, in the second invocation: `Database Error ... Unrecognized name: points_capture_pct; Did you mean points_capture?` |

Same assertion, same branch, same job, opposite result. `points_capture_pct` exists only in the
`ci_*` copy this job built; `points_capture` exists only in prod. The second run was reading prod.

## The asymmetry is deliberate, and is the thing to review

The two invocations now differ, and that is the change. On the **build** line `--favor-state` is
correct and load-bearing: a model being BUILT must take its upstreams from prod, never from a stale
`ci_` table an earlier MR left, and a node dbt is building in the current run is not deferred at
all — so the flag costs that line nothing and buys isolation. On the **test** line nothing is being
built, so the identical flag has the opposite effect. Both the file comment and `escalations.log`
say this at the point of difference, including a `⛔ Do NOT re-add --favor-state here to "match the
build line"`.

## What this does NOT do

- No test is removed, excluded, tagged out or skipped. The suite is the same 30.
- No assertion is weakened. Every singular test's SQL is untouched.
- `data:build:main` (line 714) is untouched: it runs the same suite `--target prod` with no
  `--defer` and no `--favor-state`, and remains the full-strength production gate.
- `data:nightly` and the ingest-lock invariant are untouched.

## The remaining hole, stated rather than left implicit

`--defer` alone still prefers a `ci_` relation **when one exists**, so a singular test can read an
UNMODIFIED upstream from a table another merge request left in the shared `ci_*` datasets. That is
narrower than aiming the whole suite at the wrong database, and it fails loudly rather than passing
quietly. It stays open on #92; closing it means per-MR ephemeral datasets, which is a recurring-cost
decision and therefore the CPO's. Not taken here.

## ROUND 2 — two FAILs, both correct, both the same class this task exists to fix

`cto-reviewer` and `platform-reviewer` FAILed round 1 independently. Neither finding was in the CI
change itself; both were the change's own blast radius, undisclosed.

**Finding 1 (both reviewers) — the change made two dbt guards' CI notes false and overrode a
standing instruction, and round 1 left them standing.** `assert_metric_meaning_complete.sql` and
`assert_metric_direction_lower_is_better_agree.sql` each documented that on a PR
`ref('metric_catalogue')` resolves to MAIN's seed "because `--favor-state` swaps it for the state
relation", derived a workflow rule from it (catalogue VALUES and a guard depending on them cannot
land in the same PR), and closed with **"Do not try to solve this with a CI workflow change."**
`dbt seed --target ci` runs at `.gitlab-ci.yml:589` before both invocations, so the BRANCH's seed
relation always exists in the ci target; with `--favor-state` gone, plain `--defer` prefers it.
Both guards now read the branch's seed and the split-the-PR rule is obsolete.
⛔ Correcting `.gitlab-ci.yml` while leaving two dbt guards asserting the old behaviour is exactly
the failure this task is about — "the file asserted the behaviour the flag prevented" — and exactly
the "corrections replace, never accumulate" rule. Both notes rewritten, the old text preserved in
git rather than paraphrased away, and the obsolete instruction re-aimed rather than deleted quietly.

**Finding 2 (platform-reviewer) — the change was pinned by nothing but a comment.** Re-adding
`--favor-state` restored the entire defect with pytest, sqlfluff, every offline gate and the
pipeline all still green. A comment is precisely what failed here the first time.
`tests/test_ci_data_job_invariants.py` — the module whose docstring opens *"Pin three CI data-job
invariants that can be broken while every pipeline stays GREEN"* — gains
`test_the_mr_singular_test_gate_reads_the_branch_not_prod`, asserting **both halves** of the
asymmetry. One-sided pinning would let someone "restore symmetry" by stripping the flag from the
build line instead, which is a different bug that would pass.

### The new pin, watched failing BOTH ways before being trusted

| mutation | result |
|---|---|
| `--favor-state` re-added to the `dbt test` line | ✅ RED — *"data:build:mr's `dbt test` line carries --favor-state again … the 30 singular tests stop testing the branch and re-report on prod"* |
| `--favor-state` removed from the `dbt build` line | ✅ RED — *"data:build:mr's `dbt build` line lost --favor-state … Do not make the two lines match."* |
| both restored | 5 passed |

`scope_paths` was extended by three files to carry these fixes, on a clean tree, recorded under
`amendments:` in the contract. The authority is the standing rules the FAILs invoked, not a new CPO
decision — neither extension widens what this task decides.

## One thing checked and deliberately NOT changed

`tests/test_ci_data_job_invariants.py:17` reads "every MR build defers to prod with
`--defer --favor-state`". That sentence is about the **build** line, which still carries both flags,
so it remains true and was left alone rather than edited — the file is not in `scope_paths` and
touching it would be scope drift. Flagged here so a reviewer grepping for `--favor-state` finds the
hit already accounted for.

## The claim is proved by RUNNING it, not by reading it

The done_when that matters cannot be satisfied on this branch: after this merges, `!114` is rebased
onto it and its pipeline must be watched going green **on the exact test that failed at job
`16145201830` line 1021**. Until that is observed, this change is argued, not demonstrated.
