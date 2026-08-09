# Task contract — #33 item 8a: an incomplete fetch must not supersede a good snapshot

> Branch `fix/896-guard-partial-writes` from `main` (`7b464bd`), worktree `D:\Projects\fdp-pipeline`.
> No PROTECTED path, so no `protected_override`. `ingestion/**` IS the structural surface, so an
> `impact_map` is REQUIRED and is below. No `site_v2/src/`, so no `acceptance_criteria`.

objective: >
  Port the #896 guard — "an incomplete fetch must never supersede stored data" — to the four
  per-league snapshot loaders that lack it: TRANSFERS, COACHES, STANDINGS, TEAMS.

  WHY THIS EXISTS, AND WHY IT IS ITS OWN MR. #33 item 8 converts the append-only raw tables to
  merge-on-write keyed on `league_code`. Applying that today would DESTROY PRODUCTION DATA: each
  of these four loaders abandons its fetch loop when the daily quota latches and then writes the
  partial payload unconditionally. Under append-only that is recoverable — the partial wins the
  latest-snapshot `qualify` in staging, but the complete prior row still exists in `raw`. Under
  merge-on-write the partial write DELETES the complete prior row. The CPO split item 8 on
  2026-08-08 after this was found; 8a is the precondition that makes 8b non-destructive.

  THE DEFECT, one shape in four files:
      transfers.py:31-33   coaches.py:44-45   standings.py:31-32   teams.py:29-30
      for x in ...:
          if errors_quota._http_quota_exhausted:
              break                      # loop abandoned, nothing recorded
          ...
      load_json_to_bq(..., append=True)  # partial written as if complete

  THE FIX ALREADY EXISTS IN THIS REPO and is not being invented here. `result_is_complete()`
  (`http_client.py:83`) is the #896 primitive: True only when the provider reported no body-level
  error AND the run's daily-quota flag is unset, because the two failure shapes differ — a
  per-minute rate limit arrives as HTTP 200 with the error in the body, while an exhausted daily
  quota short-circuits to an empty body with no error at all. Either signal alone misses one.
  `players_response_for_team` (`fixture_scheduling.py:480`) already uses it.

  ⚠ A SWEEP CHANGED WHAT I THOUGHT THE SCOPE WAS. `result_is_complete` is called in exactly ONE
  place in the whole codebase. Eleven loaders fetch-and-write; nine have no completeness check.
  Only RAW_APIF_PLAYERS is genuinely protected (per key, `squads.py:188-196`); RAW_APIF_SQUADS is
  partially protected (`player_squads.py` guards the catch-up path on `quota_cut` only, not on
  body errors). This MR fixes the four the CPO named and scoped. The remaining holes are listed
  under decisions_reserved rather than silently widened into or silently dropped.

  CONSULTED BEFORE BUILDING (§2 norm): read `result_is_complete`'s docstring for why both signals
  are needed; read `squads.py`'s per-key guard and `player_squads.py`'s discard-the-partial guard
  as the two existing precedents, and followed the second, because these four tables are ONE row
  per league and cannot withhold per team.

refs: >
  GitLab #33 item 8, split into 8a/8b by the CPO on 2026-08-08 after this defect was found.
  Implements the #896 ruling for four more tables. Follows !23, !24, !25 (Wave 1, all merged).

scope_paths:
  - ingestion/api_football/loads/transfers.py
  - ingestion/api_football/loads/coaches.py
  - ingestion/api_football/loads/standings.py
  - ingestion/api_football/loads/teams.py
  - ingestion/api_football/fixture_scheduling.py
  - tests/test_incomplete_snapshot_not_written.py

impact_map: >
  WRITERS. Exactly the four loaders named, each the sole writer of its raw table — verified with
  `grep -rn "load_json_to_bq" ingestion/`:
      loads/transfers.py  -> RAW_APIF_TRANSFERS   (6.99 GiB, 59% of raw)
      loads/coaches.py    -> RAW_APIF_COACHES     (0.21 GiB)
      loads/standings.py  -> RAW_APIF_STANDINGS   (0.09 GiB)
      loads/teams.py      -> RAW_APIF_TEAMS       (0.08 GiB)
  `fixture_scheduling.py` is touched only to give `transfers_response_for_team` the same
  `(rows, complete)` return shape `players_response_for_team` already has. No other caller of that
  function exists — verified.

  WHAT CHANGES BEHAVIOURALLY, stated precisely because it is a behaviour change and not a refactor.
  When a fetch loop is cut short by the daily quota, or any per-team/per-season response carries a
  body-level error, the league's snapshot is now DISCARDED instead of written. Consequences:
  - Normal runs: nothing changes. A complete run writes exactly what it writes today.
  - A degraded run: staging keeps the PREVIOUS complete snapshot instead of being superseded by a
    partial. That is the #896 ruling and it is strictly better for data quality.
  - A degraded FIRST-EVER ingest of a league: nothing is written at all, where today a partial
    would land. Accepted, and it is the same trade `player_squads.py` already makes on its
    catch-up path. It self-heals on the next run, and the discarded snapshot is reported through
    `ctx.errors`, which reaches the completeness summary rather than being silent.

  DOWNSTREAM. No dbt model, seed, macro or test is touched, so there is no lineage to trace and no
  mart or number can move. The raw SCHEMA is unchanged — same table, same columns, same payload
  shape, same append semantics. What changes is only WHETHER a given degraded run writes a row.
  Staging is unaffected by construction: `stg_apif__transfers`, `_standings` and `_teams` already
  select the latest snapshot per `league_code`, so they read one row per league either way.

  DELIBERATELY NOT IN THIS MR: no merge-on-write, no delete of any kind, no `league_code`-keyed
  DELETE. This MR only ever writes FEWER rows than today. That is what makes it safe to land
  before 8b, and safe to land the same day the nightly resumes.

  DEPLOY ORDER. No warehouse object changes. The nightly (schedule 4379625) fires 04:00 UTC daily
  and will be the first consumer. Landing this BEFORE 8b is the point of the split; landing it
  before tonight's run is desirable but not required, because append-only remains safe either way.

  BLAST RADIUS on data: no mart, no number, no displayed value. The risk being managed is the
  reverse of the usual one — this makes the pipeline write less, never more.

decisions_taken: >
  AUTHORITY. The durable record is `.claude/task/escalations.log`, entry
  "2026-08-08 — #33 item 8 SPLIT into 8a/8b: item 8 as approved would have destroyed prod data",
  appended in this branch. It records the split itself, the evidence that forced it, the CPO's
  "go ahead with 8a", and — explicitly, because it was the thing most likely to be inferred later
  — that 8a is scoped to FOUR loaders and which five gaps are deliberately left out.
  That entry exists BECAUSE `scope-auditor` FAILed round 1 for its absence, and it was right:
  the 2026-08-08 blanket #33 approval covers item 8 as ONE thing ("raw merge-on-write with the
  raw_archive backup first"), and a split that changes what item 8 IS is a new decision. Fourth
  time this repo has ruled that a decision living only in `contract.md` is not recorded
  (2026-07-31, 2026-08-01, and the standing-rule entry of 2026-08-08).
  The underlying rule is NOT new: #896 is already this repo's ruling, recorded 2026-08-03, and
  already implemented for RAW_APIF_PLAYERS. This MR applies an existing ruling to four more
  tables; it does not create one.

  THRESHOLD DECLARATIONS (no gate parses this field; an omission is a defect, not an oversight).
  - NEW MECHANISM: none. `result_is_complete()` already exists and is already used. No new
    dependency, no new config, no new env var, no new table.
  - RECURRING COST: unchanged, or very slightly reduced. No new API call — `result_is_complete`
    inspects the response already in hand. No extra BigQuery read. On a degraded run one LOAD job
    is skipped, so a bad night gets marginally cheaper.
  - GUARD STRENGTHENED, not weakened. Four tables gain a protection only one table had.
  - BEHAVIOUR CHANGE, declared: a degraded first-ever ingest now writes nothing. See impact_map.

  WHY DISCARD RATHER THAN WRITE-AND-MARK. Two precedents exist. `squads.py` withholds incomplete
  KEYS, which works because RAW_APIF_PLAYERS is one row per (team, season). These four tables are
  ONE ROW PER LEAGUE, so there is no key to withhold — the snapshot is complete or it is not.
  `player_squads.py` faces the same one-row-per-league shape and DISCARDS. Followed the second.

decisions_reserved:
  - THE REMAINING #896 HOLES, found by the sweep and deliberately not fixed here: `catalog.py`
    (LEAGUES), `injuries.py` (INJURIES), `fixtures.py` (FIXTURES_NEXT), `player_profiles.py`,
    `player_teams.py`, and the body-error half of `player_squads.py`. The CPO scoped 8a to four
    loaders; widening to nine inside the same MR would be exactly the drift `scope_paths` exists
    to stop. They matter for 8b, and are reported on #33 so 8b's scope is decided with them in
    view — not left to be rediscovered.
  - Which tables 8b may convert at all. `PLAYER_PROFILES` and `PLAYER_TEAMS` accumulate per player
    (`players_needing()` writes only newly-seen players), so a `league_code`-keyed DELETE would
    erase every player ingested on an earlier run. They must never be converted. Not decided here.
  - #33 item 15 (drop `/injuries`). RAW_APIF_INJURIES is 1.78 GiB, the second-largest raw table,
    with no source declaration and no model. Whether to guard it or delete the endpoint is one
    decision, and it is the CPO's.

done_when:
  - `python -m pytest tests/ -q` exit code read DIRECTLY; green, and no lower than main's 683.
  - New tests in `tests/test_incomplete_snapshot_not_written.py` assert, for EACH of the four
    loaders: (a) a complete fetch still writes exactly one payload; (b) a body-level error on any
    one team/season writes NOTHING and reports through `ctx.errors`; (c) a mid-loop daily-quota
    cut writes NOTHING. Assertions are on whether the loader called its BigQuery write, using a
    recording double — not on log text.
  - EVERY new assertion proven load-bearing by reverting the guard it covers and watching that
    test go red, then restoring. DONE, and it caught TWO decoration bugs in this MR alone:
      · round 0: the quota-cut cases for `standings` and `teams` PASSED with the guard disabled.
        Their helper re-patched `fetch_merged_paged` with an empty response list, so they were
        exercising an IndexError path, not a quota cut. Harness restructured (patch and invoke
        split apart); all 8 discard cases then failed as required.
      · round 1, found by BOTH specialists independently: `_patch_transfers` monkeypatched
        `transfers_response_for_team` out entirely and substituted a hand-rolled stand-in, so the
        REAL guard at `fixture_scheduling.py:513` — the one protecting RAW_APIF_TRANSFERS, 6.99
        GiB and 59% of raw — was never executed by any test. Reverting it to `complete = True`
        left the whole suite green. Fixed by patching the HTTP layer UNDER the helper instead,
        plus a direct unit test of the helper's own return value; re-verified against that exact
        revert, which now fails two cases.
      · round 2, `platform-reviewer` again, and the sharpest of the three: the mid-loop
        quota-cut cases were masked for ALL FOUR loaders. The fake sets the latched quota flag on
        iteration 1, and every one of these loaders has a PRE-EXISTING top-of-loop
        `if _http_quota_exhausted: break` that catches it on iteration 2 — so the new check could
        be regressed to body-errors-only (`if data.get("errors")`, blind to the quota flag, which
        is half of what #896 is about) and all four cases would still pass on the OLD code.
        Fixed by adding `test_a_quota_cut_on_a_single_iteration_is_caught`, which invokes each
        loader with exactly ONE team/season so there is no second iteration for the old guard to
        fire on. Verified against exactly that regression in all four loaders: the four new cases
        fail, and — confirming the reviewer's analysis precisely — the four mid-loop cases stay
        green throughout.
    TEN decoration tests have now been caught this way across four MRs. None was caught by
    reading the test; every one needed the subject broken.
  - `grep -rn "result_is_complete" ingestion/` shows the four new call sites plus the pre-existing
    one — i.e. the fix uses the existing primitive rather than a private reimplementation.
  - `ruff check --config .ruff-ci.toml ingestion/ tests/` exits 0.
  - No `dbt build`, `dbt run` or ingest is executed at any point.

amendments: (none)
