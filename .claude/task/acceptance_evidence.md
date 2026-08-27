# Evidence — #92: the MR singular-test gate now reads the branch, not production

Branch `fix/92-singular-tests-read-the-branch`, from main `1804a64`.
No `site_v2/src/` path is in scope, so the acceptance gate does not fire and there are no
`acceptance_criteria` to demonstrate. This file carries the verification instead.

## The change, in two halves

**Half one — one flag.** The trailing singular-test run stops reading production:

```
- dbt test --select test_type:singular ... --defer --favor-state --state /tmp/main-state --target ci
+ dbt test --select test_type:singular ... --defer              --state /tmp/main-state --target "$DBT_CI_TARGET"
```

**Half two — one dataset set per merge request.** Half one alone was not enough, and CI proved it
on the first pipeline (below). The profile anchor now derives the target from the merge-request id:

```
+ export DBT_CI_TARGET="ci_mr${CI_MERGE_REQUEST_IID:-shared}"
    target: ${DBT_CI_TARGET}
    ${DBT_CI_TARGET}:
      dataset: ${DBT_CI_TARGET}
```

and all three dbt invocations use `--target "$DBT_CI_TARGET"`.

⛔ **NOTHING IN THIS DIFF DELETES ANYTHING** — no expiry, no TTL, no drop, no cleanup step, no path
by which a mis-scoped rule could reach production. Swept: `git diff` contains no `expiration`, no
`bq rm`, no `drop dataset`. An expiry would bound the storage and was **deliberately refused** on
the CPO's explicit instruction. The datasets accumulate; measured, a full set is 6.0 GB (~12¢/mo).

### Why half two was necessary — measured, not argued

`!115` changes NO models, so it rebuilt nothing and read whatever the shared datasets held. It went
red on three tests against tables `!114` had built an hour earlier:

| test | result | cause |
|---|---|---|
| `assert_mart_team_season_insights_metric_consistency` | Database Error | `!114`'s renamed column |
| `assert_no_uncatalogued_season_metric` | 2 rows | `!114`'s model columns vs THIS branch's seed |
| `assert_momentum_window_matches_momentum` | 257 rows | tables built by a different branch |

Headline error: `Unrecognized name: points_capture; Did you mean points_capture_pct?` — the exact
mirror of the failure that started #92, and proof half one works: the tests were reading the ci
datasets, just the wrong branch's.

### Both halves of the isolation, and why both are pinned

`generate_schema_name` prefixes a model that HAS a `+schema` with `target.name` — that covers the
four layer datasets. It returns **bare `target.schema`** for a model with none, which is the whole
`2_base` layer and **every seed, `metric_catalogue` included**. Those are isolated by the profile's
`dataset:` line alone. The macro itself is **not in the diff**.

### Pre-flight, before building rather than after

This is the first change requiring dbt to CREATE datasets. Read from the live project IAM policy:
the CI service account `github-actions-dbt@…` holds `roles/bigquery.user`, which grants
`bigquery.datasets.create`. (That name is a leftover from before the GitLab migration, not a
GitHub dependency.)

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

### FIVE mutations, every one watched going RED, then restored

Both halves are silently revertible, so both are pinned, and each pin was broken on purpose before
being trusted. Run against this exact tree, not recalled from an earlier one:

| # | mutation | result |
|---|---|---|
| 1 | `--favor-state` re-added to the `dbt test` line | ✅ RED — *"the 30 singular tests stop testing the branch and re-report on prod"* |
| 2 | `--favor-state` removed from the `dbt build` line | ✅ RED — *"Do not make the two lines match."* |
| 3 | a literal `--target ci` restored on the seed line | ✅ RED — *"targets a literal shared `ci` target"* |
| 4 | `DBT_CI_TARGET` derived without `CI_MERGE_REQUEST_IID` | ✅ RED — *"the same for every merge request — the shared workspace is back"* |
| 5 | profile `dataset:` reverted to `ci_analytics` | ✅ RED — *"the base models and every seed (metric_catalogue included) … this line is the only thing isolating them"* |
| — | all restored | **6 passed** |

Mutation 5 is the one a reviewer had to find: an earlier version of this pin asserted only the
target name, so reverting `dataset:` alone put every base table and the seed back in one shared
dataset with the whole suite still green.

`scope_paths` was extended by three files to carry these fixes, on a clean tree, recorded under
`amendments:` in the contract. The authority is the standing rules the FAILs invoked, not a new CPO
decision — neither extension widens what this task decides.

## FINAL ROUND — the same defect class, five more instances, all mine

`platform-reviewer` and `analytics-engineer-reviewer` both failed the completed change, and both
found the same thing: **half two abolished the shared workspace, and five comments elsewhere still
described it as current.** I swept the places I was thinking about and not the rest — which is
precisely the "corrections replace, never accumulate" failure this whole task exists to remove,
committed inside the fix for it.

| # | place | what it still said |
|---|---|---|
| 1 | `.gitlab-ci.yml`, build-line justification | "never from a stale ci_ copy left by **another MR**" |
| 2 | `.gitlab-ci.yml`, above `dbt build` | "Writes ci_* datasets … never a stale ci_ copy left by **a prior MR**" |
| 3 | `.gitlab-ci.yml`, the docs-generate note | "that job builds state:modified+ into the **shared** ci_* datasets" |
| 4 | `tests/test_ci_data_job_invariants.py`, docstring + assertion message | "a stale `ci_` table **an earlier MR left**" |
| 5 | `contract.md`, objective | "the **shared** `ci_*` datasets carry tables left by earlier merge requests" (present tense) |

⭐ **AND THE FIX IS NOT JUST DELETING THE OLD REASON — platform-reviewer worked out the one that
survives, which I had not.** With per-merge-request datasets, "another branch's leftovers" is
structurally impossible, so `--favor-state` on the BUILD line looked like it guarded nothing, and
the next reader would rightly have deleted it — the exact mutation the new pin exists to stop.
The surviving case is an **earlier pipeline of the SAME merge request**: build a model, then push a
commit reverting it to match main, and it drops out of `state:modified+` so the next pipeline does
not rebuild it — leaving a superseded table that `--defer` alone would prefer. `--favor-state`
forces prod for it. That reason is now stated in all four code locations and in the contract.

Swept afterwards for any surviving instance across the CI file, the pin, both dbt guards and both
docs: **zero**. Pins still 6 passed.

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
