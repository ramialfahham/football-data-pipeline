# Task contract — #898: a run that drops API calls cannot look clean

> Written on a clean tree before any file was touched. Branch `fix/898-surface-dropped-calls` from
> `main` at `0a4f636`. No protected path in scope, so no `protected_override`. No `site_v2/src/`
> path, so no `acceptance_criteria`. `completeness.py` WRITES a raw table, so `impact_map:` below is
> required and is evidenced.

impact_map: >
  Written with the #896 lesson applied: this diff touches functions shared by many callers, so the
  map traces EVERY caller rather than the one the task came for.

  SHARED FUNCTION 1 — `quota.append_api_errors` is NOT changed, and round 1 is why. The first
  version counted dropped calls inside it, keyed off the caller's context string, on the reasoning
  that all 16 call sites pass the endpoint as the first token. `data-engineer-reviewer` FAILED that:
  `loads/fixtures.py` calls it TWICE against overlapping data, per season at :163 and again at :183
  on the accumulated envelope, and `seasons.py::_merge_merged_paged` extends `dst["errors"]` so the
  earlier seasons' rate-limit text is carried forward. The `fixtures` count was inflated up to 2x.
  Verified independently by reading those lines. Counting now happens in `fetch_json`, once per HTTP
  call whose final attempt was still rejected, keyed by API path. That is immune to how many times
  any caller reports the same error, so it fixes the class rather than the `fixtures.py` instance.

  SHARED FUNCTION 1a — `completeness.evaluate_completeness_outcome` gains two optional keyword
  arguments and one new key in its returned dict. Callers: `orchestrator.py` (updated) and
  `tests/test_completeness_outcome_and_summary.py`, which asserts the returned dict by EXACT
  equality. That test is updated to include the new key rather than relaxed to a subset, so a future
  signal still cannot be added unnoticed. Both arguments default to None, so the shape change is
  additive and no other caller behaviour moves.

  SHARED FUNCTION 2 — `http_client.fetch_json`, the single HTTP entry point for every endpoint. The
  change adds ONE retry branch for a body-level per-minute rate limit. It does not alter the
  returned dict's key set. That constraint is load-bearing and is why #896 round 1 failed: four
  loaders persist the raw payload by copying every key except a fixed exclusion list. A test added
  in #896 (`TestReturnedKeySetIsStable`) pins that key set and will catch any regression here.

  WRITER OF THE AFFECTED TABLE — `RAW_APIF_INGEST_COMPLETENESS_SNAPSHOT`, written only by
  `completeness.persist_fixture_statistics_missing` and read only by
  `completeness.load_prior_fixture_statistics_missing`, both in the same module.
  `grep -rn "COMPLETENESS_SNAPSHOT_TABLE"` returns three lines, all in `completeness.py`.

  DOWNSTREAM LINEAGE: NONE, and this was checked rather than assumed.
  `grep -rn "INGEST_COMPLETENESS_SNAPSHOT" dbt_project/ scripts/` returns nothing, and no dbt source
  or model references it. The snapshot is internal run state, not warehouse data, so adding a key to
  its payload has zero downstream blast radius. This is the check whose absence caused #896 round 1.

  CI LAYER RULES. None engaged: no model, schema, seed or SQL file is touched.

  SHARED-WAREHOUSE DEPLOY ORDERING. Not engaged; nothing is built or deployed by this diff.

  BLAST RADIUS ON NUMBERS: none. No mart value can change. No fact is derived, no grain moves, no
  raw entity table gains or loses a row. The diff changes what a run REPORTS and, in one specific
  case, whether it exits nonzero.

  ⚠ THE ONE REAL CONSEQUENCE, stated plainly because it trades a non-negotiable. A hard fail returns
  503, which `main.py` maps to exit code 3. In `dbt-scheduled.yml` every post-ingest step is
  conditioned on `steps.ingest.outputs.new_data == 'true'` with NO `always()`, so a nonzero ingest
  exit SKIPS `dbt deps`, `dbt seed`, the layer-contract check and `dbt build`. On a day the
  stagnation gate fires, the warehouse therefore does NOT ingest that day's marts and the data is a
  day stale. That is the existing behaviour of the `stagnant_statistics` gate too; this diff adds a
  second trigger to the same exit path rather than a new one.

objective: >
  A nightly run that dropped 26 API calls reported `conclusion: success`, and that has happened on
  10 of the last 18 runs since 2026-07-16, every one green. The project's stated non-negotiable is
  that the CPO cannot verify numbers by hand, so a run reporting success is the only signal that the
  data is complete. For three weeks it has meant nothing.

  Four independent causes, all verified in code:
  1. `http_client.py` retries on `status_code == 429`, but the per-minute limit arrives as HTTP 200
     with the error in the body, so the retry never fires and the call is dropped with ZERO retries.
  2. `quota.py::_payload_shows_daily_limit_exceeded` matches only the DAILY text ("request limit"
     and "day"), so the per-minute class sets no flag and is invisible to every consumer of it.
  3. `completeness.py`'s `FANOUT_ENTITIES` covers only LINEUPS / FIXTURE_EVENTS /
     FIXTURE_STATISTICS / FIXTURE_PLAYERS — zero overlap with coaches, players, player_squads,
     transfers, which are the endpoints that actually dropped.
  4. `orchestrator.py` builds the job summary from `tables_loaded`, `soft_partial`,
     `stagnant_statistics` and `hard_gated_failures`. `ctx.errors` is NEVER appended. The only
     channel is a stdout line deduped and truncated at 40 entries; the 07-16 run ended "+1480".

  #897 (merged) reduced the failure RATE. #896 (merged) stopped a dropped call DESTROYING data.
  Neither makes a dropped call visible. This does.

refs: >
  #898 (this). #897 merged as `d2b5789`, #896 as `0a4f636`. #900 is the stale blueprint cost model,
  filed during #897. Cause 3 (the fanout-only completeness gate) is a deliberate,
  registry-configurable mechanism and is NOT changed here; this adds a parallel signal instead.

scope_paths:
  - ingestion/api_football/quota.py
  - ingestion/api_football/http_client.py
  - ingestion/api_football/orchestrator.py
  - ingestion/api_football/completeness.py
  - tests/test_dropped_call_visibility.py
  - tests/test_completeness_outcome_and_summary.py
  - .claude/task/contract.md
  - .claude/task/review.md
  - .claude/task/review_input.patch
  - .claude/task/escalations.log

decisions_taken: >
  CPO, 2026-08-03, asked as one batch before any file was touched and recorded in
  `escalations.log`:

  THE THRESHOLD POLICY IS: VISIBLE ALWAYS, FAIL ONLY ON STAGNATION.
  - Dropped calls are surfaced in the job summary on EVERY run, counted by endpoint, so a green run
    with drops looks visibly different from a clean one.
  - A single bad run NEVER fails. Failing would block the dbt build and cost daily freshness, and
    the CPO ruled explicitly against paying that for a transient limit that self-heals.
  - The run fails only when the SAME endpoint drops on consecutive runs, i.e. when it is
    demonstrably not healing.
  - It reuses the existing `stagnant_statistics` no-progress-since-last-run pattern and its existing
    snapshot table, rather than inventing a mechanism. That was the explicit instruction.

  N = 2 CONSECUTIVE RUNS, and this is a rule-settled choice rather than a fresh decision: the
  existing `detect_stagnant_statistics_backfill` compares exactly prior-versus-current, so a second
  stagnation signal on the same gate uses the same window. Choosing anything else would have made
  two gates on one exit path disagree about what "stagnant" means.

  THRESHOLD DECLARATIONS.

  NEW MECHANISM: none. The gate, its exit code (503 to exit 3), its snapshot table and its
  prior-versus-current comparison all already exist; this adds a second trigger to them. The retry
  is a fourth branch in `fetch_json`'s existing retry loop, treating a per-minute limit as the 429
  the provider chose to deliver as a 200.

  RECURRING COST: small, bounded, and measured against the real baseline.
  - The retry costs at most ONE extra HTTP call per rate-limited call, plus its wait. On the
    2026-08-02 baseline of 26 drops that is at most 26 extra calls against ~8,300 (0.3%) and at most
    ~78s. After #897's pacing the drop count should be near zero, so the expected cost is near zero.
  - No change to the endpoints called, the daily quota draw, or the pacing.
  - One extra key in an existing snapshot payload, which has no dbt consumer.
  - The freshness cost is the stagnation fail described in `impact_map`, and it is the trade the CPO
    approved knowingly.

decisions_reserved:
  - Cause 3 is NOT fixed. Widening `FANOUT_ENTITIES` to cover per-team endpoints would change a
    deliberate, registry-configurable gate and is a separate decision.
  - The retry is BEST EFFORT and this is stated rather than oversold: a per-minute window can take
    up to 60s to clear, and the retry waits `Retry-After` or 3s. It will not rescue every call. The
    real protections are #897 (pacing, so limits are rare) and #896 (so a drop cannot destroy data);
    this adds the alarm. Waiting out a full minute per drop was NOT chosen, because it would trade
    run time for a case pacing should already have removed.
  - `_http_quota_exhausted` is deliberately NOT set by the per-minute detector. That flag aborts all
    remaining HTTP for the run, which is right for a daily cap and catastrophic for a transient one.

done_when:
  - A body-level per-minute rate limit is retried once, and a 429 still behaves exactly as before.
  - The per-minute detector never sets `_http_quota_exhausted`.
  - Dropped calls appear in the `$GITHUB_STEP_SUMMARY` notes counted by endpoint, on every run.
  - The same endpoint dropping on two consecutive runs hard-fails; dropping on one does not.
  - The counter resets per run, so a count cannot leak across runs in the same process.
  - Tests pin each of those, and fail against the pre-fix code.
  - `python -m pytest tests/ -q` passes.

amendments:
  - ROUND 2, after both specialist reviewers FAILED round 1. Authority: the CPO's approval of #898
    itself, which is what makes these edits necessary rather than a widening. Per the standing
    lesson, the first question was whether the EDIT belongs in this branch, not how to widen the
    contract to admit it. It does: the approved change breaks that test, and the branch cannot be
    green without it.
    1. `tests/test_completeness_outcome_and_summary.py` added to `scope_paths`. Its
       `test_skipped_report_returns_no_failures` asserts `evaluate_completeness_outcome`'s returned
       dict by exact equality, and the approved fix adds a key to that dict. The test is EXTENDED
       to include the new key, never relaxed to a subset.
    2. `impact_map` corrected: `append_api_errors` is no longer changed at all, and the reason is
       recorded above so the rejected approach is not retried.
    No decision is taken here and no permission is widened beyond that one test file. The threshold
    policy, N, and the freshness trade are unchanged from `decisions_taken`.
