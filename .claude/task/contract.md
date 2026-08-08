# Task contract — Wave 1 item 1 (#33): hoist the per-run ingestion reads

> Branch `perf/ingestion-hoist-per-run-reads` from `main` (`72a6a69`), in the worktree
> `D:\Projects\fdp-pipeline`. No PROTECTED path, so no `protected_override`. `ingestion/**` IS the
> structural surface, so an `impact_map` is REQUIRED and is below. No `site_v2/src/`, so no
> `acceptance_criteria`.

objective: >
  Wave 1 item 1 of GitLab #33 — the only change in the plan that alters an exponent. Ingestion
  reads are O(competitions^2): two full-table scans are issued once per competition inside the
  per-competition loop, so adding a league makes every league more expensive.

  WHAT IS ACTUALLY QUADRATIC, traced rather than taken from #33:
  - `coverage.read_coverage()` scans ALL of `RAW_APIF_FIXTURE_DETAILS` with no `league_code` and no
    `ingested_at` filter, reading the `payload` JSON column twice. Reached from `ingest_plan.py:84`
    (`_fanout_covered_from_bq`) <- `_finished_fanout_has_gaps` <- `resolve_ingest_mode` <-
    `orchestrator.py:140`, which is inside the loop over all selected competitions. 45 active
    competitions today, so 45 scans, plus 1 more in `completeness.py:135`.
  - `squads.captured_player_team_seasons()` UNNESTs ALL of `RAW_APIF_PLAYERS` and is called from
    `load_squad_players_batch` (`squads.py:146`) once per full-mode competition in Phase 3.

  Two cheaper duplicates ride along, both provably safe to collapse (see the impact_map):
  - `player_universe._query_universe()` — the same full `RAW_APIF_PLAYERS` UNNEST runs twice per
    run, once for `PLAYER_PROFILES` and once for `PLAYER_TEAMS`.
  - The completeness snapshot is read three times back to back (`completeness.py:433/455/471` from
    `orchestrator.py:214-217`) to extract three different keys from one payload.

  CONSULTED BEFORE BUILDING (§2 norm): traced every call site with grep rather than assuming, and —
  the part that changed the design — established the WRITE ordering between each pair of duplicate
  reads before deciding what may be cached.

refs: >
  GitLab issue #33, Wave 1 item 1. Follows !23 (merged, `72a6a69`) and !24 (open). Related: #892.

scope_paths:
  - ingestion/api_football/orchestrator.py
  - ingestion/api_football/ingest_plan.py
  - ingestion/api_football/completeness.py
  - ingestion/api_football/loads/squads.py
  - ingestion/api_football/loads/competition_runner.py
  - ingestion/api_football/loads/player_universe.py
  - ingestion/api_football/loads/player_profiles.py
  - ingestion/api_football/loads/player_teams.py
  - tests/test_ingestion_read_hoisting.py

impact_map: >
  WRITERS. This task changes no writer. Every raw table is written by exactly the loaders that
  write it today, with the same payloads, the same merge keys and the same ordering. What changes
  is how many times the pipeline READS three tables inside one run.

  DOWNSTREAM. Nothing in dbt is touched, so there is no model lineage to trace and no mart or
  number can move. Evidence that the boundary is real: `git diff --stat main...HEAD` touches only
  `ingestion/**` and `tests/**`; `RAW_APIF_*` schemas, the `payload` column and the merge keys are
  untouched, so every `stg_apif__*` model reads exactly what it reads today.

  ⚠ THE CONSTRAINT THAT SHAPES THE WHOLE DESIGN — WRITE ORDERING. A run-wide read cache would be
  WRONG here, and wrong silently. `orchestrator.py` interleaves the duplicate reads with writes to
  the very tables being read:
      line 140  resolve_ingest_mode      -> reads FIXTURE_DETAILS coverage, per competition
      line 176  run_batch_fixture_fanout -> WRITES FIXTURE_DETAILS
      line 231  run_ingest_completeness  -> reads FIXTURE_DETAILS coverage again
  The completeness check MUST see post-fanout rows; that is what it is for. Cache coverage across
  those two points and every run reports fanout gaps that were filled minutes earlier. So the fix
  is a PHASE-SCOPED hoist — one read shared by the Phase-1 loop, and the completeness check keeps
  its own, separate read — not a memo on `PipelineContext` and not a module-level cache.
  The same reasoning rules each of the other three individually; each is justified below by naming
  what writes between the reads, or that nothing does.

  PER-READ SAFETY, one argument each:
  1. `read_coverage` in Phase 1. All 45 calls happen inside one loop with NO write to
     FIXTURE_DETAILS between them — the fanout is Phase 2. One read before the loop is therefore
     observationally identical for every competition. 45 -> 1.
  2. `captured_player_team_seasons` in Phase 3. Here a write DOES land between calls:
     `load_squad_players_batch` writes RAW_APIF_PLAYERS for each competition. A naive hoist would
     let competition 2 re-fetch a (team, season) competition 1 just captured — wasteful, not
     incorrect (the function's own docstring: "a duplicate download, never a silent miss"), but
     national teams genuinely appear in more than one competition, so it would fire. The hoisted
     set is therefore UPDATED IN PLACE with the keys each competition fetches, which keeps it
     exactly as accurate as re-reading. N -> 1.
  3. `_query_universe` (Phase 5). Between the `PLAYER_PROFILES` and `PLAYER_TEAMS` calls, the only
     write is to RAW_APIF_PLAYER_PROFILES. The universe query reads RAW_APIF_PLAYERS, which nothing
     writes in Phase 5. Safe. 2 -> 1. `_existing_player_ids` is NOT cached — it reads the target
     table, which differs per call and is written between them.
  4. The completeness snapshot triple. Three reads of one table, back to back, extracting three
     different keys; the snapshot is not written until `persist_fixture_statistics_missing`
     afterwards. Safe. 3 -> 1.

  A CORRECTION TO #33, on evidence. #33 claims this takes "46 full scans of a ~4 GiB table per run
  to 1". It cannot go to 1, and should not: the 46th scan is the completeness check's, and it must
  stay because it has to observe the fanout's writes. The achievable figure is **2** — one for the
  Phase-1 loop, one for completeness. The quadratic TERM is still removed, which is the point of
  the item; only the headline number is wrong.

  LAYER RULES. `check_layer_contract.py` governs dbt directories and is unaffected. The ingestion
  rule that applies is the competition-agnostic one (`docs/working_agreement.md` §8): nothing here
  introduces a league identifier, and the hoist makes the code MORE competition-agnostic by
  removing per-competition work that did not depend on the competition.

  DEPLOY ORDER. No warehouse object changes, no migration, nothing to sequence around the nightly
  (which is unreachable anyway — no schedule exists; that is item 7). The ingest is not run by this
  MR's CI: `data:build:mr` reaches the ingest branch only when `get_new_league_codes.py` returns a
  non-empty list, and on !23's pipeline it printed "All leagues already have raw tables — skipping
  bootstrap ingest."

  BLAST RADIUS: no mart, no number, no displayed value. The observable change is the count of
  BigQuery jobs a run issues, and the risk being managed is a stale read inside a run, which is
  what the per-read safety arguments above address one by one.

decisions_taken: >
  AUTHORITY: the CPO's standing approval of 2026-08-08, durably recorded in
  `.claude/task/escalations.log` ("2026-08-08 — GitLab #33: the CPO approves the whole pipeline
  cost/scalability plan, in advance"), which is on `main` at `72a6a69` and independently checkable.
  #33 lists item 1 under "Wave 1 — mechanical, no CPO decision".

  THRESHOLD DECLARATIONS (no gate parses this field; an omission is a defect, not an oversight).
  - RECURRING COST: reduced, and this is the item's whole purpose. No new job, schedule, cadence,
    API call, endpoint or history depth. The API-call count per run is UNCHANGED — this touches
    BigQuery reads only, never the fetch plan. That distinction matters: `captured_player_team_
    seasons` feeds a fetch-side skip, so getting it wrong WOULD change API spend. It is kept exact
    by updating the hoisted set in place rather than by accepting a stale one.
  - NEW MECHANISM: none. No cache class, no memo decorator, no module-level state, no new
    dependency. The hoists pass an already-computed value down as an ordinary parameter — the
    plainest thing that works, and deliberately not a `PipelineContext` cache, which would have
    been the tempting general mechanism and would have made the write-ordering hazard invisible.
    One private module constant was added: `completeness._UNREAD`, a sentinel — see round 1.

  WHAT REVIEW ROUND 1 FOUND, both accepted, both verified against the code before acting:
  - `data-engineer-reviewer`: the completeness-snapshot hoist made a FIRST RUN WORSE, not better.
    `read_prior_snapshot()` returns None when there is no prior record — a first run, or one whose
    predecessor had `API_FOOTBALL_SKIP_COMPLETENESS_CHECK` set. None was also the "caller supplied
    nothing" sentinel, so passing it through made all three readers fetch for themselves: 1 hoisted
    read + 3 re-reads = 4, against a baseline of 3, in exactly the case each reader's docstring
    says it exists to handle. Fixed with a private `_UNREAD` sentinel so "no prior record" and
    "unsupplied" stop being the same value. This is the finding that mattered most in the round.
  - `platform-reviewer`: the other three hoists were revertible in silence. `already_captured` and
    `universe` had defaults, and the orchestrator is their ONLY caller, so deleting one keyword
    argument at one call site restored a full-table scan with the entire suite green — the tests
    exercised the functions in isolation, never the wiring. Fixed STRUCTURALLY rather than with a
    wiring test: those arguments are now REQUIRED, so omitting one is a TypeError, which is the
    same protection `resolve_ingest_mode` already had and which that reviewer had singled out as
    the reason it alone was safe. It also showed the correctness pin could be defeated by ADDING
    an `all_covered=None` parameter to `run_ingest_completeness_checks` and wiring Phase 1's result
    in — a behavioural test cannot see that, so the signature is now pinned too.

  WHAT REVIEW ROUND 2 FOUND. `data-engineer-reviewer` PASSED. `platform-reviewer` FAILED again, on
  a DIFFERENT path to the same failure class, and was right twice: requiring the argument closes
  only the narrowest revert — deleting the keyword. Moving the computation back INSIDE the
  per-competition loop, while still passing it, restores the whole O(competitions^2) scan with all
  14 assertions green, because every callee-level test sees a value arrive exactly as before. It
  also caught `done_when` claiming a multi-competition orchestrator count test that does not exist.
  Fixed by pinning the CALLER: an AST check that the three readers are not called from inside any
  loop in `_load_api_football`, proven by moving `read_coverage` back into the loop and watching it
  fail. Its limit (name-based, so an alias evades it) is stated in the test. The overclaimed
  `done_when` line is rewritten to say what the tests actually assert.
  - GUARD WEAKENED: no. No test is removed or narrowed, no assertion relaxed. The completeness gate
    keeps its own independent read precisely so it cannot be weakened by this change.

  SCOPE JUDGEMENT — TWO OF #33's SIX SUB-ITEMS ARE DEFERRED, stated rather than silently dropped:
  - "Make `_finished_fanout_has_gaps` lazy." Once the coverage read is hoisted out of
    `resolve_ingest_mode`, that function no longer issues a query at all — the remaining work is an
    in-memory set walk. Laziness would save microseconds and add a branch. Deferred as not worth
    the diff; the saving #33 attributes to it is entirely delivered by the hoist.
  - "Cache the FIXTURES_NEXT payload." The duplicate is `ingest_plan.py:113` and
    `loads/fixtures.py:117`, both per competition. Unlike the two scans above this is a PRUNED
    equality read on one league's latest snapshot, not a full-table scan, and collapsing it means
    threading a payload through `run_cheap_phases` into the fixtures loader — invasive for a small
    constant. Deferred as its own follow-up rather than bundled into a refactor whose value is the
    exponent change.
  Both are recorded on #33 so they are visible as remaining work, not lost.

decisions_reserved:
  - Whether the completeness check's independent `read_coverage` should ALSO be avoided, by having
    the fanout return what it wrote instead of re-reading. That would take the count from 2 to 1
    and is what #33 assumed was free. It changes what the completeness gate observes — from
    "what BigQuery says is there" to "what this process believes it wrote" — which is a
    weaker check, and weakening a DQ gate is §10. NOT decided here; flagged on #33.
  - #33 items 13, 14, 15 (fetch-side skips, dropping `/injuries`) all change API spend and are
    CPO-class. Nothing here touches the fetch plan.

done_when:
  - `python -m pytest tests/ -q` exit code read DIRECTLY; green, and no lower than main's count
    plus the new tests.
  - `tests/test_ingestion_read_hoisting.py` pins the property at BOTH ends, because neither end
    alone is enough — `platform-reviewer` demonstrated that at round 2:
      · CALLEE side, with a mock client that records every query issued: `resolve_ingest_mode`
        issues no FIXTURE_DETAILS scan; `load_squad_players_batch` issues no RAW_APIF_PLAYERS
        UNNEST when handed the set; `players_needing` does not recompute the universe when handed
        one; the three `load_prior_*` readers issue nothing when handed the payload (including an
        explicit None).
      · CALLER side, by AST: `read_coverage`, `captured_player_team_seasons` and
        `query_player_universe` must not be CALLED FROM INSIDE A LOOP in `_load_api_football`.
      An earlier version of this line claimed the tests assert an end-to-end
      "one query for a multi-competition run". They do not, and did not — no test drives the
      orchestrator across several competitions. That overclaim was itself a round-2 finding.
      The reason for the split is concrete: with only the callee assertions, moving the read back
      inside the loop while still passing the result restores the full quadratic scan and every
      callee test stays green, because the callee still receives a value on every call.
  - EVERY assertion proven load-bearing by reverting the hoist it guards and watching the test go
    red, then restoring. DONE for all of them, and the step paid for itself THREE times — three
    assertions passed while their subject was broken, i.e. were decoration, and were rewritten:
      · `test_resolve_ingest_mode_issues_no_coverage_query` — the first probe only added a default
        argument, which does not restore the read. Re-probed by reintroducing the scan at the call
        site; it then failed, quoting the RAW_APIF_FIXTURE_DETAILS SQL.
      · `test_completeness_keeps_its_own_coverage_read` — grepped `inspect.getsource` for
        "read_coverage(" and passed with the call deleted, because that string ALSO appears in a
        comment inside the same function. A guard that matches prose is defeated by a reword, and
        this one was defeated by a reword that had already happened. Rewritten to monkeypatch and
        assert the call, and given a signature companion after `platform-reviewer` showed the
        behavioural form still misses the realistic regression.
      · `test_a_first_run_still_costs_one_snapshot_read_not_four` — counted `client.query` calls,
        but that reader reaches BigQuery through the Storage Read API and never touches
        `client.query`, so it read green against the very defect it was written for. Rewritten to
        count `read_latest_payload_json` calls.
  - The safety property is tested TWICE, behaviourally and structurally: the completeness check
    must still call `read_coverage` itself, AND `run_ingest_completeness_checks` must accept no
    parameter but `client`, so coverage cannot be injected into it at all.
  - The three orchestrator-facing hoisted arguments have NO defaults, and a test asserts that, so
    reverting a hoist is a TypeError rather than a silent cost regression.
  - `python -m pytest tests/ -q -k "coverage or squad or player or completeness or ingest"` green —
    the existing suites over the changed modules, unchanged and unweakened.
  - No `dbt build`, `dbt run` or ingest is executed locally at any point.

amendments: (none)
