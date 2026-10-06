# Task contract — the main prod build waits while the nightly runs

objective: >
  The Cloud Run nightly and data:build:main both write prod and are not serialised; 4 of 98 main
  builds overlapped a nightly in 57 nights, each one a main build that started while the nightly
  ran. A first step of data:build:main waits while an fdp-nightly execution is in progress.

refs: >
  #204.

acceptance_criteria:
  - The nightly and the main-branch prod build never write prod at the same time

scope_paths:
  - .gitlab-ci.yml
  - scripts/wait_for_nightly.py
  - tests/test_wait_for_nightly.py
  - .claude/task/contract.md
  - .claude/task/review.md
  - .claude/task/review_input.patch

protected_override: >
  Approved by the CPO in chat, 2026-10-06: a first step of data:build:main waits while an
  fdp-nightly execution is running, polling the Cloud Run API every minute up to the job's
  timeout, with the CI account's existing run.developer grant on the job. Reading: the comment
  above the job, which says how the prod writers are kept apart, is corrected with it.

impact_map: >
  writers: none; one new step in data:build:main, before any prod write (dbt seed is the first),
  and the comment above the job.
  readers: the step reads the Cloud Run Admin API list of fdp-nightly executions with the CI
  account (github-actions-dbt), which holds roles/run.developer on the job
  (`gcloud run jobs get-iam-policy fdp-nightly`). Executions come back newest first and every
  finished one, failed ones included, carries completionTime (checked on the API); one without it
  is in progress.
  when it runs: wherever data:build:main runs (main pushes and web pipelines, its rules unchanged).
  fails closed: an API error stops the job before it writes prod.
  deploy_order: none; the nightly, its image and the GitLab data:nightly job are unchanged.
  blast_radius: data:build:main starts later by the running nightly's remaining time (nightly runs
  measured 47 to 180 minutes, 77 on average). The wait stops after 90 minutes and fails the job
  before any prod write, so the build keeps 30 minutes of the job's 2-hour timeout (it takes about
  13); a nightly still running then means a retry once it ends. No dataset, model or page changes. The opposite order, a nightly starting while a main build runs,
  did not occur in the 57 nights measured and is not covered.

decisions_taken: >
  Readings, under the delegation of 2026-10-02:
  - The wait is a small script with its own unit tests rather than inline shell, so its rule (an
    execution without completionTime is in progress) is tested offline.
  - The first page of executions (newest first) is enough: a run in progress is the newest.
  - "Up to the job's timeout" is read as a 90-minute deadline inside it, so a timeout can never
    land during the build's prod writes; a CI test pins the step after authentication and before
    the first prod write.

  Threshold declarations. NEW MECHANISM: the wait step, approved in chat, 2026-10-06. RECURRING
  COST: none in BigQuery; CI runner time while waiting.

decisions_reserved:
  - None.

done_when:
  - The script's unit tests pass; the API call it makes is checked once against the live job.
  - pytest (whole suite), the offline gates and the CI lint pass.
  - The review cycle passes, review.md bound to --staged-hash; the MR pipeline is green.
