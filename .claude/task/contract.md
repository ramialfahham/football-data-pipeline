# Task contract — #897: production pauses between API calls

> Written on a clean tree before any file was touched. Branch `fix/897-pace-production-ingest` from
> `main` at `36b5f98`. No protected path in scope, so no `protected_override`. No `site_v2/src/`
> path, so no `acceptance_criteria`. `ingestion/api_football/settings.py` IS on the structural
> surface, so `impact_map:` below is required and is evidenced, not asserted.

impact_map: >
  SHORT FORM, and the evidence is a complete call trace rather than a claim of triviality.

  WRITERS. `settings.py` writes no table: `grep -n "load_json|bigquery|insert|query(" ` over it
  returns zero hits. It sets process env defaults and nothing else.

  FULL CONSUMER TRACE of the value being changed. `API_FOOTBALL_REQUEST_PAUSE_MS` is read at exactly
  ONE site, `quota.py:99` inside `_request_pause_seconds`. That function has exactly ONE caller,
  `_throttle` at `quota.py:109`. `_throttle` has exactly ONE call site, `http_client.py:51`, reached
  after a successful HTTP response. Verified by
  `grep -rn "_request_pause_seconds|_throttle" --include=*.py .` which returns those five lines and
  no others. So the entire reachable effect of this change is the duration of one `time.sleep()`
  between API calls.

  DOWNSTREAM LINEAGE. None to trace. No dbt model, no SQL, no seed and no schema is touched, so
  there is no `ref()` edge to follow and no CI layer rule (staging/base/core/marts) is engaged.
  `dbt ls` is not applicable to a change that adds no node and alters no node.

  SHARED-WAREHOUSE DEPLOY ORDERING. Not engaged. Nothing is built or deployed by this diff, so there
  is no ordering constraint against the shared CI/prod datasets.

  BLAST RADIUS ON NUMBERS: none, in the strict sense that no mart value can change as a
  CONSEQUENCE of the diff. Same endpoints, same call count, same payloads, same raw tables, same
  columns, same row grain. The two observable changes are both non-data: run duration rises by a
  measured factor of 1.55, and provider rejections fall. Where a number does move, it moves only
  toward completeness: a call that is no longer rejected returns rows it previously did not. This
  change cannot remove data.

  RAW COUNT EVIDENCE. `RAW_APIF_TRANSFERS` is the table the sibling issues touch and is untouched
  here: 1,117 rows / 6.82 GiB, partitioned on `ingested_at` (DAY), clustered on `league_code`. This
  diff writes to it neither before nor after.

objective: >
  Production ingest runs with NO pacing between API calls, against a requirement this repo wrote
  down. `settings.py:146` sets `API_FOOTBALL_REQUEST_PAUSE_MS=0` under the `full` profile, and
  `dbt-scheduled.yml` sets no profile, so production inherits zero.
  `docs/api_football_ingestion_blueprint.md` §4 mandates a 0.25s pause and names the per-minute
  burst as the binding constraint.

  Consequence, measured on the 2026-08-02 nightly: 26 calls rejected by the provider's per-minute
  limit (7 coaches, 11 players, 7 player_squads, 1 transfers). It has hit 10 of the last 18 runs
  since 2026-07-16, and every one reported `success`. The trigger is volume growth, not a code
  change: per-team calls are now 2,058 per entity across 26 leagues.

  This is the cheapest of the three sibling fixes and reduces the failure RATE. It does NOT make a
  failure visible (#898) and does NOT stop an empty response destroying good rows (#896). Those are
  separate PRs, in that order, by CPO decision.

refs: >
  #897 (this). Siblings #896 (an incomplete fetch must not supersede) and #898 (dropped calls are
  invisible in four places) follow as PR 2 and PR 3. #892 is the precedent for the pinning test: a
  silently reverted default regressed for two months because nothing asserted it.

scope_paths:
  - ingestion/api_football/settings.py
  - docs/operations_guide.md
  - docs/api_football_ingestion_blueprint.md
  - tests/test_ingest_profile_pacing.py
  - .claude/task/contract.md
  - .claude/task/review.md
  - .claude/task/review_input.patch
  - .claude/task/escalations.log

decisions_taken: >
  CPO, this session, asked as one batch before any file was touched:

  1. Fix via the `settings.py` profile default, NOT via `dbt-scheduled.yml`. The workflow route
     touches a protected path and would need `protected_override` + `impact_map`; the settings route
     also prevents recurrence, because nothing can inherit zero pacing by omission afterwards.
  2. The value is 250ms, the figure the blueprint already mandates.

  THRESHOLD DECLARATIONS.

  NEW MECHANISM: none. This changes the value of an existing setting and adds a test.

  RECURRING COST: a real one, measured, and approved with the numbers in hand.
    - API calls per run: UNCHANGED. Same endpoints, same count. Measured usage today is 7,437 of a
      75,000 daily quota (~10%), so the daily budget is not affected and is not the constraint.
    - BigQuery: unchanged. No model, no query, no storage touched.
    - Wall-clock: ingest averages 0.455 s/call today; a 250ms pause makes it 0.705 s/call, a factor
      of 1.55. Ingest 63 min -> ~98 min; whole run 1h11m -> ~1h46m. The job has no
      `timeout-minutes`, so GitHub's 6h default applies: ~3.4x headroom. Daily freshness is
      preserved, which is the non-negotiable this trade was checked against.
    - GitHub Actions minutes: free. The repository is public.
    - Provider limits are MEASURED, not assumed: `x-ratelimit-limit: 450` per minute and
      `x-ratelimit-requests-limit: 75000` per day. Our plan is Ultra. 250ms caps the request rate at
      240/min, i.e. 53% of the real per-minute limit.

decisions_reserved:
  - The blueprint's §4 plan table has no row for the plan we are actually on, and its "approximately
    20-50 API calls total" estimate for a full daily run is stale by roughly 200x against a measured
    ~8,300. This contract corrects the table and the pacing rule ONLY. Rewriting the blueprint's cost
    model is not attempted here.
  - #898's threshold policy (how many dropped calls a run may tolerate) is decided but belongs to
    PR 3, not here.
  - `standings.py:30` and `teams.py:28` loop every configured season daily with no skip. Real, and a
    #547 cost item. Out of scope.

done_when:
  - `API_FOOTBALL_REQUEST_PAUSE_MS` defaults to 250 under the `full` profile, and an explicitly set
    env var still wins (`setdefault` semantics unchanged).
  - The `economy` profile is untouched: unset still yields `quota.py`'s 6600ms free-tier pacing.
  - A test pins the `full` default and asserts the explicit-override path. It must FAIL against the
    pre-fix value, otherwise it does not pin anything.
  - Every user-facing statement of the old value is corrected in the same commit: the profile
    docstring, the profile log line, and `docs/operations_guide.md`.
  - `docs/api_football_ingestion_blueprint.md` §4 states the plan tier we are on with its measured
    per-minute limit, so the next reader does not re-derive it.
  - `python -m pytest tests/ -q` passes.

amendments: (none)
