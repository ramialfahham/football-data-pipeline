# Task contract — #39 Stage 2: make the nightly observable

objective: >
  Stage 1 gave the nightly a safe home. It still has the blind spot that turned a silently
  dropped cron into SIX DAYS of stale data (2026-08-03 → 08-09), found by a human by accident
  rather than by a system. Stage 2 closes it.

  THE LOAD-BEARING INSIGHT, and the reason this is not just "wire up dbt source freshness":
  every check that lives inside the nightly only runs when the nightly runs. The failure that
  cost six days was the nightly NOT RUNNING AT ALL. No in-pipeline test can ever see that.

  WHAT SHIPPED, after the CPO redirected the design mid-task: the monitor is ENTIRELY
  out-of-band. `scripts/check_raw_freshness.py` runs hourly as its own Cloud Run Job, reads each
  raw table's last-modified time from BigQuery METADATA, and exits non-zero when it is past the
  `error_after` already declared in `sources.yml`. THE NIGHTLY IS NOT TOUCHED AT ALL —
  `deploy/nightly/entrypoint.sh` has zero net diff on this branch. An earlier attempt added
  `dbt source freshness` inside it and hoisted `dbt deps` above the `new_data` gate; that was
  REVERTED when the sentinel made it redundant. There is no in-pipeline half.
refs: GitLab #39 (Stage 2 of 3); #33 item 16

scope_paths:
  - deploy/nightly/entrypoint.sh
  - deploy/nightly/alert-policy.json
  - deploy/nightly/README.md
  - scripts/check_raw_freshness.py
  - tests/test_nightly_entrypoint_parity.py
  - tests/test_raw_freshness_sentinel.py
  - .claude/task/contract.md
  - .claude/task/escalations.log
  - .claude/task/review.md
  - .claude/task/review_input.patch

# Not gate-required — no path here is on the structural surface. Included because this
# changes the nightly's execution path and its cost profile, and a reviewer should not
# have to take either on trust.
impact_map: >
  what changes in the pipeline: NOTHING. `deploy/nightly/entrypoint.sh` carries zero net diff on
    this branch — verify with `git diff main -- deploy/nightly/entrypoint.sh`, which is empty. A
    quiet night still exits 0 before `dbt deps`, the contract checks, seed and build, and is
    still literally $0, exactly as after Stage 1. No dbt model, seed or macro is touched either.
    The monitoring is entirely beside the pipeline, not inside it.
    (An earlier revision of this contract described adding `dbt source freshness` to the
    entrypoint. That change was reverted when the CPO chose the sentinel; three reviewers caught
    the contract still describing it. Corrected here rather than left as a footnote, because a
    contract that mis-states its own shipped mechanism is worse than no contract.)

  what changes outside the repo: one Cloud Monitoring notification channel (email) and one
    alert policy, both defined in `deploy/nightly/alert-policy.json` and created by REST calls
    recorded in the runbook — version-controlled rather than clicked once in a console.

  downstream: none. No model, mart or number is affected. `dbt build --target prod` is
    unchanged and still gated on `new_data`.

  cost profile: UNCHANGED for the nightly — a quiet night is still literally $0, because the
    entrypoint is untouched. The only new spend is the sentinel itself, and it is close to
    nothing: `client.get_table()` is a METADATA call, not a query, so no bytes are scanned and
    no query job is billed. What remains is ~24 Cloud Run executions a day of a few seconds
    each at 1 vCPU / 512 MiB. Alert policies, notification channels and Cloud Scheduler are
    free at this volume. Being free per run is precisely what makes hourly affordable, and
    hourly is what allows a 3h absence window instead of the 25h ceiling.

  failure semantics: a source past `error_after` makes the SENTINEL exit 1 → the `fdp-freshness`
    execution is marked failed → the policy fires. A source past `warn_after` only logs and does
    not fail. A sentinel that cannot check exits 2, also non-zero, deliberately — a sentinel
    that cannot check must never look healthy.
    ⚠ THE POLICY CANNOT TELL exit 1 FROM exit 2: Cloud Run's `completed_execution_count` carries
    only succeeded/failed, not the exit code. Both are worth waking up for, so they share a
    policy; the sentinel prints `EXIT 1 — STALE` or `EXIT 2 — CANNOT CHECK` as the first thing
    in its failure output, and the policy's documentation sends the reader there. Caught by a
    reviewer, whose point was that the documentation had asserted "users are affected" for a
    case where that is not established.

  the watcher's watcher: the absence condition depends on Cloud Scheduler and Cloud Monitoring
    themselves working. That regress stops here deliberately — both are managed Google services
    with their own status surface, and adding a second monitor to watch the first is where this
    stops being proportionate.

decisions_taken: >
  The CPO approved Stage 2 ("do stage 2") and the written plan. Two choices were put to the CPO
  and answered directly: the alert channel is EMAIL to rami.fahham@gmail.com, and the staleness
  threshold is NO SUCCESSFUL RUN IN 30 HOURS (chosen over 26h and 54h).

  ⚠ THE 30h CHOICE COULD NOT BE HONOURED BY THE FIRST DESIGN — AND THE CPO CHOSE A DIFFERENT
  DESIGN RATHER THAN A DIFFERENT NUMBER.

  SEQUENCE, recorded because the first attempt got this wrong. The builder hit the platform
  cap, substituted 25h, DEPLOYED it, and wrote up the reasoning. `scope-auditor` FAILed that in
  round 1 and was right: §10 makes a threshold a CPO decision "regardless of how obvious the
  answer seems", and documenting an override after shipping is not the same as holding
  authority for it. §11 requires the conflicting paths and a recommendation put to the CPO
  BEFORE implementing. The escalation was then run properly — keep 25h / disable staleness
  until item 14 / build a BigQuery-backed check — and the CPO chose:
  **"Build a BigQuery-backed check instead."**

  WHAT THAT CHANGES. The 25h cap stops applying, because the alert no longer keys on Cloud Run
  job success at all. A sentinel measures the thing the product actually cares about — how old
  the DATA is — and job success becomes irrelevant to it. The CPO's original 30h intent is
  reachable again, and better: thresholds come from `sources.yml`, which already declares
  warn 30h / error 54h per source, so there is no second place for a threshold to drift.

  THE PLATFORM CONSTRAINTS THAT DROVE THIS, kept so they are not rediscovered: `conditionAbsent`
  rejects any duration over 23h30m ("Durations longer than 23h30m are not supported"); MQL
  `absent_for` rejects anything over 1d1h. Both tried against the real API, both HTTP 400. For a
  DAILY job every value at or below 24h false-alarms before each run, which left 25h as the only
  usable number — a ceiling, not a choice. Running the SENTINEL hourly dissolves the problem:
  absence detection on an hourly job needs a 3h window, far inside the cap.
    - `conditionAbsent` rejects any duration over 23h30m: "Durations longer than 23h30m are not
      supported" (HTTP 400, tried against the real API).
    - MQL `absent_for` rejects anything over 1d1h: "the longest time the query results might be
      absent is 1d6h, which is greater than the allowed 1d1h" (HTTP 400).
    - 23h30m is WORSE than useless for a daily job — consecutive successes are ~24h apart, so
      it would fire shortly before every single run. That is why the staleness policy is MQL
      rather than the simpler `conditionAbsent`: 25h is the only value above 24h that either
      mechanism permits.
  25h is therefore the maximum achievable and the closest to the CPO's intent. It detects
  FASTER than 30h; what it gives up is slack. With runs currently taking 1-2h, successes land
  ~05:00-06:00 and 25h absorbs about an hour of drift; a run hitting the full 3h timeout could
  trip it spuriously. That window widens on its own once #33 item 14 cuts the run to ~20 min.
  If the CPO would rather have fewer false alarms than this detection speed, the lever is item
  14, not the threshold — the threshold is already at its ceiling.

  A SECOND API CONSTRAINT, same class: one policy cannot hold both conditions — "Alert policies
  with monitoring_query_language condition type can only have a single condition" (HTTP 400).
  Shipped as TWO policies sharing one notification channel.

  A CORRECTION TO #33 ITEM 16, verified rather than inherited: it states the two
  `freshness_check` tests have never run. They DO run — the nightly's `dbt build` carries no
  selector, which is `fqn:*`, and `.gitlab-ci.yml` says so explicitly ("freshness_check is
  deliberately NOT excluded"). The claim was true before the migration and is stale now. What is
  genuinely un-wired is the `dbt source freshness` COMMAND, whose only repo-wide mention is a
  line of prose in `dbt_project/docs/engineering_standards.md:145`. IT REMAINS UN-WIRED after
  this task, and that is deliberate: the sentinel reads the same `sources.yml` thresholds from
  outside the pipeline, which covers the same ground without making a quiet night cost money or
  coupling staleness detection to the nightly running at all.

  # THRESHOLD DECLARATIONS
  NEW MECHANISM — YES. Cloud Monitoring alert policies and notification channels are new to this
  project (0 of each exist today). Declared rather than smuggled, and `cto-reviewer` is spawned
  for this task even though `.claude/review_routing.json` covers neither `deploy/**` nor a
  monitoring surface — the same reason it was spawned for Stage 1.

  RECURRING COST — effectively ZERO, and ZERO for the nightly specifically. Alert policies,
  notification channels and Cloud Scheduler are free at this volume; the sentinel's BigQuery
  reads are metadata calls and are not billed. The only spend is a few seconds of Cloud Run
  compute, 24 times a day, at 1 vCPU / 512 MiB. The nightly's own cost profile does not change
  at all — an earlier revision claimed a quiet night would cost "a few cents a month" via
  `dbt source freshness`; that mechanism was reverted and the claim with it.

  NO new Python dependency, and `requirements.txt` is unchanged.

decisions_reserved:
  - Deleting `data:nightly` from `.gitlab-ci.yml`. Guarded path, needs its own governance task,
    and it stays a fallback while Cloud Run is still new. Not decided here.
  - Whether the 3 sources deliberately left without freshness thresholds should ever gain them.
    They refresh rarely and thresholds would false-alarm; changing that is a data decision.
  - Stage 3 (CI builds and pushes the image on merge), #33 item 14, and the GitLab self-hosted
    runner decision are all separate.

done_when:
  - `pytest tests/ -q` exits 0 (baseline on main is 725 passed, 1 skipped).
  - `ruff --config .ruff-ci.toml ingestion/ tests/` exits 0.
  - `bash -n deploy/nightly/entrypoint.sh` exits 0.
  - Every new/changed test verified by BREAKING ITS SUBJECT — the production code, never the
    test's own helper — and confirming WHICH cases go red:
      · disable the staleness comparison (`age > limit * 100`) → the stale case, the boundary
        case and the end-to-end exit-code case fail; the fresh/warn cases stay green.
      · make "nothing to check" return 0 instead of 2 → the empty-thresholds case fails.
      · rebind `SOURCES_YML` as an import-time default → the cannot-read-thresholds case fails.
        This one was MASKED at first: in an unauthenticated environment `main()` returned 2 via
        the BigQuery branch regardless, so the test passed either way. A reviewer caught it; the
        fix stubs BigQuery healthy so 2 can only come from the branch under test.
      · add a comment key without a `_` prefix to `alert-policy.json` → the API-field whitelist
        case fails. An earlier version of that assertion was tautological, and the break-it
        check that "proved" it had edited the test's own `strip()` helper rather than the JSON.
        Breaking the harness is not breaking the subject.
  - The notification channel and BOTH alert policies exist and are readable back from the
    Monitoring API, confirmed by a GET rather than by trusting the POST responses.
  - The channel's verification state is reported HONESTLY. The API does not return a
    `verificationStatus` field for this channel at all, so whether email delivery works is
    UNKNOWN from here and must be stated as unknown. An unverified channel is a policy that
    looks armed and is not — claiming Stage 2 is complete before the CPO confirms an email
    arrived would be exactly the false green this stage exists to prevent.
  - No Cloud Run execution is triggered by this task.

amendments:
  - 2026-08-10: + `scripts/check_raw_freshness.py`, + `tests/test_raw_freshness_sentinel.py` —
    authority: **CPO, asked via a §11 escalation with three paths and a recommendation, and
    answered "Build a BigQuery-backed check instead"** (the builder's recommendation was to keep
    25h; the CPO chose otherwise). Recorded in escalations.log, 2026-08-10, not only here —
    scope-auditor FAILed this exact omission twice on the Stage 1 branch.
    Content: a sentinel that reads each raw table's last-modified time via BigQuery METADATA
    calls (free — no query, no scan), compares the age against the `error_after` already
    declared in `sources.yml`, and exits non-zero when stale. Deployed as a second Cloud Run Job
    from the SAME image with an entrypoint override, scheduled hourly, so no second image is
    built and absence detection needs only a 3h window.
