# Task contract — #896: an incomplete fetch must never supersede good data

> Written on a clean tree before any file was touched. Branch
> `fix/896-incomplete-fetch-must-not-supersede` from `main` at `d2b5789`. No protected path in
> scope, so no `protected_override`. No `site_v2/src/` path, so no `acceptance_criteria`.
> `loads/squads.py` WRITES a raw table, so `impact_map:` below is required and is evidenced.

impact_map: >
  WRITERS OF THE AFFECTED TABLE. `RAW_APIF_PLAYERS` has exactly one writer:
  `loads/squads.py::load_squad_players_batch`, via `load_json_payload_rows_to_bq` (append) followed
  by `_delete_superseded_player_rows`. Verified by `grep -rn "delete from|_delete_superseded"` over
  `ingestion/`, which returns THREE lines, all inside `loads/squads.py`. The merge-on-write pattern
  this task fixes exists in exactly one place, so there is no second site to fix.

  DOWNSTREAM LINEAGE, taken from dbt rather than asserted.
  `dbt ls --select stg_apif__players+ --resource-type model` returns 13 models:
  1_staging: stg_apif__players
  2_base: base_apif__players, base_apif__player_team_season
  3_core: dim_player, dim_player_team_season_mapping
  5_marts: mart_roster, mart_leaderboards, mart_player_career, mart_player_profile,
  mart_player_match_log, mart_player_fixture_stats, mart_player_competition_benchmarks,
  mart_team_momentum_window

  THE SHARED HELPER'S OTHER CALLERS. `http_client.fetch_merged_paged` is shared by seven call
  sites, so editing it has a blast radius wider than `RAW_APIF_PLAYERS`. Review round 1 FAILED the
  first version of this diff for exactly that omission: it added a `complete` key to the returned
  dict, and four loaders build the raw payload they persist by copying every key except a fixed
  exclusion list. The key would have been written into `RAW_APIF_STANDINGS` (via
  `seasons.py::_merge_merged_paged`, `loads/standings.py:47-55`), `RAW_APIF_TEAMS`
  (`loads/teams.py:41-43`), `RAW_APIF_INJURIES` (`loads/injuries.py:52-58`) and
  `RAW_APIF_FIXTURES_NEXT` (`loads/fixtures.py:242-249`). `load_json_to_bq` stores `payload` as a
  schemaless JSON column with no key filtering, so it would have been physically written. The value
  would also have been WRONG: `_merge_merged_paged` copies from the FIRST source only, so it would
  freeze at the first season of a multi-season loop and a run whose fourth season was rate-limited
  would still record the snapshot as complete.

  THE RESOLUTION: completeness is now a FUNCTION (`http_client.result_is_complete`) and no returned
  dict gains a key, so the leak is impossible by construction rather than by remembering to exclude
  a name in four separate places. `coaches.py` and `transfers_response_for_team` were verified to
  read only `.response` and were unaffected either way. A regression test pins the returned key set
  so the next person to reach for a key hits a failing test instead of four raw tables.

  CI LAYER RULES. None are engaged: no model, schema, seed or SQL file is touched, so no
  staging/base/core/marts boundary moves and `check_layer_contract.py` has nothing to judge. No
  per-competition file is added, so the zero-file rule is not implicated.

  SHARED-WAREHOUSE DEPLOY ORDERING. Not engaged. This diff builds nothing and deploys nothing; it
  changes only which raw rows survive a run. No `dbt build` is run from this branch.

  BLAST RADIUS ON NUMBERS: mart values CAN change, and this is stated plainly rather than claimed to
  be nil. The change alters which raw rows survive, so every model in the list above can see rows it
  would otherwise have lost. The direction is one-way: the fix only PREVENTS deletion of rows already
  held. It derives nothing, adds no column, and changes no grain or formula. Concretely, on a run
  like 2026-08-02 the fix retains the squads for UCL 340 (25 players), UEL 573 (24) and UECL 20034
  (23) that were reduced to zero, and the 6 of 46 lost for APD 463.

  RAW COUNT EVIDENCE. `RAW_APIF_PLAYERS`: 22,589 rows / 0.55 GiB, partitioned on `ingested_at` (DAY),
  clustered on `league_code`. Of 22,589 team-season blocks, 4,973 currently hold an EMPTY payload and
  3,539 of those are historical (season < 2026). That measurement is what settled the design; see
  decisions_taken.

objective: >
  When a `/players` fetch fails, the loader treats the failed response as authoritative and DELETES
  the previously good rows for the same (league_code, team_id, season).
  `loads/squads.py::_delete_superseded_player_rows` is keyed on what the NEW row claims, with no
  check that the new row actually contains players or that the fetch even succeeded.

  Measured via BigQuery time travel on the 2026-08-02 nightly: UCL team 340 went 25 players to 0,
  UEL 573 24 to 0, UECL 20034 23 to 0, and APD 463 46 to 40 (a rate limit mid-pagination inside
  `fetch_merged_paged`). All four appear in that run's rate-limit list, so every one carried a
  body-level error.

  No existing test can catch this class, and none could be written against the current signals: the
  TABLE GREW while the data was destroyed (`RAW_APIF_PLAYERS` 721,755 to 721,938 rows), so
  row-count, freshness and not-null tests all pass. The loss is only visible per entity.

  The rate limit is only the TRIGGER. The destructive delete is the DEFECT, and it fires for any
  failed fetch whatever the cause.

  ROOT CAUSE, confirmed by reading the models rather than inferred: `base_apif__player_team_season`
  unnests per player and picks with `qualify row_number() over (...) order by raw_ingested_at desc`.
  An empty payload contributes ZERO rows, so it cannot win that race; it is not in the race at all.
  The downstream loss is therefore caused solely by the raw row being physically deleted.

refs: >
  #896 (this). #897 merged as PR 1 (`d2b5789`) and reduces the failure RATE but not this defect.
  #898 follows as PR 3 and makes the failure VISIBLE. #900 is the stale blueprint cost model, filed
  out of scope during PR 1.

amendment_note: >
  `impact_map` was extended in round 2 after `data-engineer-reviewer` FAILED round 1. The addition
  records blast radius that was always true and that the first version failed to trace; it widens no
  permission and takes no decision. `scope_paths` is unchanged.

scope_paths:
  - ingestion/api_football/http_client.py
  - ingestion/api_football/fixture_scheduling.py
  - ingestion/api_football/loads/squads.py
  - tests/test_squad_players_rows.py
  - tests/test_incomplete_fetch_no_supersede.py
  - .claude/task/contract.md
  - .claude/task/review.md
  - .claude/task/review_input.patch
  - .claude/task/escalations.log

decisions_taken: >
  CPO, this session:

  1. (taken before PR 1) #896 covers the EMPTY and the PARTIAL case in one PR. The CPO classified
     "a fetch result carries whether it is complete, and only a complete result may supersede" as an
     EXTENSION of the `quota_cut` PARTIAL handling that already exists in `squads.py`, NOT a new
     mechanism.

  2. (taken for this PR, with the measurement in hand) THE TRIGGER IS THE ERROR SIGNAL, NOT
     EMPTINESS. A fetch does not supersede when it carried a body-level error or was cut by quota
     mid-pagination. An empty response with NO error is treated as the provider genuinely reporting
     no players, and DOES supersede.

     The alternative, refusing to supersede on any empty payload, is what #896's own text suggests
     ("skips the delete when the new payload has zero entities"). It was put to the CPO with its
     price and REJECTED on cost: 3,539 historical team-seasons currently hold an empty payload, and
     refusing to write them would keep them out of `captured_player_team_seasons` forever, so
     `plan_player_team_season_fetch` would re-fetch all 3,539 EVERY night. At 0.705 s/call that is
     about +42 minutes per run, taking the nightly from ~1h46m to roughly 2h28m, permanently.

     The evidence for the cheaper option being sufficient: all four measured loss cases carried a
     body-level error, so the error signal catches every case actually observed.

     KNOWN GAP, stated rather than hidden: an empty response with no error is indistinguishable from
     a genuinely empty squad, and would still supersede. Accepted deliberately.

  THRESHOLD DECLARATIONS.

  NEW MECHANISM: none, per the CPO classification in (1) above.

  RECURRING COST: none. The chosen design leaves the call count, the daily quota draw and the run
  duration unchanged; it only skips a WRITE and a DELETE on a fetch that already failed. The
  rejected alternative would have carried a real recurring cost and is recorded above with its
  figure so the decision is not re-litigated from scratch.

decisions_reserved:
  - #898's threshold policy is decided (visible always, fail only on stagnation) but belongs to
    PR 3.
  - `fetch_merged_paged` builds `out = dict(meta)` where `meta` stays None if the page loop breaks on
    the first iteration, which would raise TypeError. Pre-existing, not reachable from
    `load_squad_players_batch` because it guards on the quota flag before calling. NOT fixed here.
  - Stopping at the deliberate page cap (`API_FOOTBALL_PLAYERS_MAX_PAGE`) is treated as COMPLETE,
    preserving today's behaviour. Treating a cap stop as incomplete would change behaviour beyond
    this defect and is not attempted.

done_when:
  - A fetch that carried a body-level error, or was cut by the quota flag mid-pagination, does NOT
    write a row and does NOT contribute its key to `written_keys`, so the prior row survives.
  - The partial-pagination case is covered by the same signal, so APD/463-style loss (46 to 40)
    cannot recur silently.
  - A successful fetch still supersedes exactly as before, including a legitimately empty one.
  - Tests assert BOTH that an incomplete fetch leaves prior rows intact and that a complete fetch
    still supersedes. They must fail against the pre-fix code, otherwise they pin nothing.
  - `python -m pytest tests/ -q` passes, including the three existing tests in
    `tests/test_squad_players_rows.py` that monkeypatch `players_response_for_team` and must be
    updated for its new return shape.

amendments: (none)
