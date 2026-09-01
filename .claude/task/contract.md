# Task contract — record where the nightly actually runs

objective: >
  **Correct two documents that state, as fact, that nothing refreshes the data on a timer — when a
  Cloud Scheduler job has been doing exactly that every morning.** Documentation only: no code, no
  config, no infrastructure change.

  `CLAUDE.md:209-211` says *"⚠ No nightly SCHEDULE exists on GitLab yet … so nothing refreshes the
  data on a timer right now."* That file is loaded at the start of every session. It is now false,
  and being false there is expensive: a fresh chat reads it, observes fresh data, and has to
  reconstruct why.

  ⛔ **THIS MR EXISTS BECAUSE I DID EXACTLY THAT, AT LENGTH.** While attributing `!136`'s BigQuery
  spend I found a daily 04:02 UTC pipeline, could not reconcile it with the docs, and reported it to
  the CPO as an unexplained recurring cost. His answer: **"We moved these two jobs to the cloud after
  your recommendation. We did this after I ran into CI limitations with Gitlab."** It was a
  deliberate, authorised decision that no document records. The investigation was avoidable; the
  documentation gap is the actual defect.

refs: >
  **CPO, verbatim, this session:** *"We moved these two jobs to the cloud after your recommendation.
  We did this after I ran into CI limitations with Gitlab."* That is the authority for what this MR
  writes down. It is a statement of fact about a past decision, not a new ruling.

  **Measured directly from GCP, read-only** — this is what the docs will now say:
    · Cloud Scheduler, **europe-west1**: `fdp-nightly` `0 4 * * *` ENABLED; `fdp-freshness`
      `7 * * * *` ENABLED.
    · Observed effect: a full ingest + prod dbt build starting 04:01–04:03 UTC **every day for the
      last 14**, writing to `dbt_analytics`, `marts`, `core`, `intermediate`, `staging`.
    · GitLab schedule `4379625` exists but is **Active=false**; its last scheduled pipeline ran
      **2026-08-10** and failed.

scope_paths:
  - .claude/active_work.md
  - .claude/task/contract.md
  - .claude/task/acceptance_evidence.md
  - .claude/task/escalations.log
  - .claude/task/review.md
  - CLAUDE.md

protected_override: >
  ⛔ **DOCUMENTATION ONLY. NOTHING EXECUTABLE CHANGES.** No workflow, no `.gitlab-ci.yml`, no
  scheduler job, no IAM binding, no `.github/workflows/**` file. The two Cloud Scheduler jobs and the
  disabled GitLab schedule are left exactly as they are — this MR describes the world, it does not
  alter it.

  ⛔ **`escalations.log` IS APPENDED TO, NEVER REWRITTEN.** The `!136` entry that framed this as an
  unexplained finding is a DATED record of what I believed then. It stays verbatim; the correction is
  a new dated entry. *Living document → replace; dated log → append.*

impact_map: >
  `CLAUDE.md` is loaded into every session by the harness, and `.claude/active_work.md` by the
  SessionStart hook — so both reach every future chat directly. That is the entire blast radius:
  nothing reads them at build or run time.

acceptance_criteria:
  - `CLAUDE.md` no longer asserts that nothing refreshes the data on a timer, and names Cloud
    Scheduler as the owner of the nightly, with the job names, crons and region.
  - `.claude/active_work.md` no longer presents this as an open cost finding for the CPO; it records
    the answer.
  - `escalations.log` carries a NEW dated entry correcting the `!136` framing, with the earlier
    entry untouched.
  - **The legacy-name trap is written down**, because it is the reusable part: the service account
    is called `github-actions-dbt` and that name says nothing about the caller.
  - No executable file appears in the diff.

decisions_taken: >
  ⭐ **§1. WHAT THE DOCS WILL SAY, AND WHY IT IS PHRASED AS OWNERSHIP.** Not "a schedule exists" but
  "the nightly lives in Cloud Scheduler" — because the failure mode this fixes is a reader asking
  *what refreshes the data* and finding an answer that points nowhere. The GitLab schedule is named
  as deliberately disabled so it does not read as the intended owner, and `data:nightly` is named as
  reachable-but-unused rather than deleted.

  ⭐ **§2. THE LEGACY SERVICE-ACCOUNT NAME IS THE PART WORTH KEEPING.** The jobs authenticate as
  `github-actions-dbt@…`, which sent me to GitHub on nothing but the name plus a workflow file with a
  matching cron. Both circumstantial; I reported them as fact and was wrong. What actually settles
  the caller is the auth path — that SA has **zero user-managed keys** and exactly one
  `workloadIdentityUser` binding (the `gitlab-pool`), so GitHub could never have been it. **Check how
  a principal authenticates before naming it from its name.**

  ⭐ **§3. THE COST FIGURES GO IN, BECAUSE THEY WERE MEASURED AND ARE OTHERWISE UNRECORDED.**
  ~129 GB/day over 14 days ≈ 3.8 TiB/month ≈ $17–24. Recorded as the observed cost of an authorised
  decision, NOT as a concern. ⚠ And with the correction attached: my first figure was ~$7/month, from
  a single day that happened to be the smallest of the fourteen, and before I knew `fdp-freshness`
  existed at all.

decisions_reserved:
  - ⛔ **Whether `fdp-freshness` should run hourly** (24×/day) is a recurring-cost question and
    therefore the CPO's. Noted in the docs as a fact, not as a recommendation, and not acted on.
  - ⛔ **Whether the disabled GitLab schedule `4379625` should be deleted** — it is infrastructure,
    not documentation. This MR only stops it reading as the intended owner.
  - ⚠ CARRIED: step 5's two follow-ups; the `__team`/`__player` split with no live instance; the
    resolver as a CI gate; **#99**, **#96**, **#87**, **#98**; `stash@{0}`'s parked test.

done_when: >
  - `CLAUDE.md` and `.claude/active_work.md` describe the real arrangement, including the legacy
    service-account name.
  - `escalations.log` has a new dated correction; the `!136` entry is byte-identical.
  - `git diff --stat` shows documentation files only.
  - Offline gates green; blinded review; `review.md` bound with `--staged-hash`. **Round cap 3.**
