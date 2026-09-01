# Acceptance evidence — record where the nightly actually runs

Branch `docs/nightly-lives-in-cloud-scheduler`, from main `1e76078`. **Documentation only.**

`CLAUDE.md` told every session that nothing refreshes the data on a timer. A Cloud Scheduler job has
been doing exactly that every morning, on the CPO's own decision. This MR writes down the world as it
is; it changes nothing about the world.

criteria_demonstrated:

  - **`CLAUDE.md` no longer asserts the false thing.** The bullet now names the owner —
    **`fdp-nightly` (`0 4 * * *`) and `fdp-freshness` (`7 * * * *`), both ENABLED in
    europe-west1** — states that the data IS refreshed on a timer, and marks `data:nightly` and the
    disabled GitLab schedule `4379625` as NOT the owner, with the warning that enabling the latter
    without disabling the former runs the build twice.
  - **`.claude/active_work.md` no longer presents this as an open CPO cost item.** It records the
    answer and the CPO's verbatim sentence.
  - **`escalations.log` is APPENDED, never rewritten.** Asserted mechanically: **0 removed lines,
    31 added**, and no hunk touches the `!136` entry that framed this as unexplained. That entry is
    a dated record of what I believed at the time and stays verbatim — *living document → replace;
    dated log → append.*
  - **No executable file in the diff.** `git diff --name-only` is four files: `CLAUDE.md`,
    `.claude/active_work.md`, `.claude/task/contract.md`, `.claude/task/escalations.log`. No
    workflow, no `.gitlab-ci.yml`, no scheduler job, no IAM binding.
  - **The legacy-name trap is written into both documents**, because it is the reusable part.

## Gates

  - `check_layer_contract.py` — **EXIT=0**. `check_registry_var_sync.py` — **EXIT=0** (48
    competitions). `sync_metric_docs_blocks.py --check` — **EXIT=0**, 163 blocks.
    `check_copy_gate.py` — **EXIT=0**, 435 strings.
  - `pytest` / `npm test` / the site build are **not run and not claimed**: nothing executable
    changed, and asserting a green suite for a prose diff would be noise dressed as rigour.

## ⛔⛔ THIS MR IS A CORRECTION OF MY OWN REPORTING, AND THE MECHANISM IS THE POINT

While attributing `!136`'s BigQuery spend I found a daily 04:02 UTC pipeline, could not reconcile it
with the docs, and reported it to the CPO as **unexplained recurring cost**. His answer:
*"We moved these two jobs to the cloud after your recommendation. We did this after I ran into CI
limitations with Gitlab."* Authorised, on my own earlier recommendation, and recorded nowhere.

**Three distinct errors, and each has a rule attached:**

**(a) I named a culprit from a NAME.** I said GitHub Actions was running it, from two circumstantial
facts: the service account is `github-actions-dbt@…`, and `.github/workflows/dbt-scheduled.yml`
carries a matching `0 4 * * *` cron. I reported that as fact. The CPO refused it in one sentence —
*"How is that possible, the account is suspended"* — and he was right. **The auth path settled it in
two queries**: that SA has **zero user-managed keys** and exactly one `workloadIdentityUser` binding
(the `gitlab-pool`), so GitHub could never have assumed it under any circumstances.
⭐ **Rule: identify a caller by how it AUTHENTICATES, never by what it is NAMED.**

**(b) I called it unexplained when it was merely undocumented.** The job was authorised; the repo was
silent. ⭐ **Rule: before reporting something as unexplained, ask whether it is simply unrecorded.**

**(c) I quoted a rate from one sample.** My first figure was ~$0.23/day ≈ $7/month, taken from a
single day — which happened to be the **smallest of the previous fourteen** (37 GB against a 15–197
GB range) — and before I had found `fdp-freshness` at all. Measured over 14 days the two jobs
together bill **~129 GB/day ≈ 3.8 TiB/month ≈ $17–24**. ⭐ **Rule: pull a RANGE before quoting a
rate.** ⚠ And query `region-eu` — `region-us` returns a confident, false "0 jobs, no cost".

## What was measured, and how

All read-only, all from GCP directly rather than from documents:

    Cloud Scheduler europe-west1   fdp-nightly    0 4 * * *   ENABLED
                                   fdp-freshness  7 * * * *   ENABLED
    Observed effect                ingest + prod dbt build, 04:01–04:03 UTC, 14 days running,
                                   writing dbt_analytics / marts / core / intermediate / staging
    GitLab schedule 4379625        Active=false; last scheduled pipeline 2026-08-10, failed
    SA github-actions-dbt          0 user-managed keys; 3 system-managed
                                   1 workloadIdentityUser binding -> gitlab-pool only
    Project IAM                    no broad serviceAccountTokenCreator; owner is the CPO
    Cloud Workflows API            disabled — ruled out

## Deliberately NOT done

  - **Nothing was switched on, off, or deleted.** The two scheduler jobs, the disabled GitLab
    schedule and `.github/workflows/dbt-scheduled.yml` are all exactly as they were.
  - **Whether `fdp-freshness` should be hourly** (24×/day) is a recurring-cost question and the
    CPO's. Written into the docs as a fact, not as a recommendation.
  - **Whether GitLab schedule `4379625` should be deleted** rather than left disabled — that is
    infrastructure, not documentation. This MR only stops it reading as the intended owner.
