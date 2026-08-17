# Task contract — never record a gap as captured (#75 MR2)

objective: >
  Four fixes of ONE class: a fetch that failed is written as fact, and the key it names is then
  treated as done forever. Unlike #75 nothing here DELETES — the damage is a permanent hole that
  no later run re-fetches, which is why no existing test or DQ check can see it. Append-only
  (`!59`) made bad writes recoverable; it did not stop us recording them.
refs: GitLab #75 (MR2 of the plan recorded in `escalations.log` 2026-08-17); the four sites were
  found by the two blind lead-DE assessments the CPO ordered.

scope_paths:
  - ingestion/api_football/bigquery.py
  - ingestion/api_football/completeness.py
  - ingestion/api_football/fixture_scheduling.py
  - ingestion/api_football/loads/player_profiles.py
  - ingestion/api_football/loads/player_squads.py
  - ingestion/api_football/loads/player_teams.py
  - ingestion/api_football/loads/transfers.py
  - tests/test_never_record_a_gap.py
  - tests/test_incomplete_fetch_no_supersede.py
  - tests/test_player_squads_catchup.py
  - .claude/active_work.md

impact_map: >
  WRITERS TOUCHED, and what each currently records as fact:
    `loads/player_squads.py:75`   -> RAW_APIF_SQUADS. Marks `(team, season)` captured via
      `captured_team_seasons`, which reads `$.team_id` PRESENCE over ALL rows (no latest filter).
    `loads/player_profiles.py:68` -> RAW_APIF_PLAYER_PROFILES. Marks the player ingested via
      `player_universe._existing_player_ids`, which reads `$.player_id` presence.
    `loads/player_teams.py:68`    -> RAW_APIF_PLAYER_TEAMS. Same reader, same effect.
    `loads/transfers.py:86`       -> RAW_APIF_TRANSFERS, one row for the WHOLE league.
  Because all three "captured" readers key on PRESENCE of the id and not on the payload being
  non-empty, a rate-limited empty answer is indistinguishable from a real one and the key is
  never re-fetched. That is the permanent hole.

  THE FETCH HELPERS, verified by reading them, not assumed:
    guarded, return `tuple[list, bool]`: `players_response_for_team` (:457),
      `transfers_response_for_team` (:487)
    UNGUARDED, return a bare `list`: `squads_response_for_team` (:520),
      `profiles_response_for_player` (:545), `player_teams_response_for_player` (:569)
  So the completeness signal exists and three siblings simply never got it.

  `load_json_to_bq` DEFAULT, enumerated across every call site
  (`grep -rn "load_json_to_bq(" ingestion/ scripts/` -> 11 callers):
    9 pass `append=True` explicitly. TWO omit it and rely on the `False` default, i.e.
    WRITE_TRUNCATE, and both do so DELIBERATELY because their tables hold a single current-state
    row: `completeness.py:602` (RAW_APIF_INGEST_COMPLETENESS_SNAPSHOT) and
    `fixture_scheduling.py:345` (RAW_APIF_{lc}_INGEST_CURSOR).
    Making the parameter REQUIRED therefore changes no behaviour anywhere; it forces the
    destructive choice to be written down at the two places that make it. `fixture_scheduling.py`
    is in scope for that one-word edit.

  DOWNSTREAM: none of this changes a model, a grain or a number. It changes WHICH KEYS GET
  RE-FETCHED, so the observable effect is more API calls on runs following a rate limit, and
  players/squads that previously stayed permanently blank getting filled on a later run. No dbt
  file is touched, so `dbt ls` lineage is not the relevant evidence here and is deliberately not
  pasted — the blast radius is the ingest planner, not the warehouse graph.
  DEPLOY ORDER: ⚠ `.data_paths_prod` EXCLUDES `ingestion/**`, so merging does NOT rebuild prod.
  ⚠ #74: nothing redeploys the Cloud Run image on merge, so this is INERT in production until the
  nightly image is rebuilt from main by hand — the same gap that left `!59` inert for six hours.

decisions_taken: >
  CPO instruction, 2026-08-17, in this conversation: "go ahead as recommended", against a
  recommendation that named these four fixes explicitly. MR2 of the plan the CPO approved earlier
  the same day when he chose "Everywhere" for the append-only rule.

  NOT LOOSENED, and this is the trap to avoid: the fix is to WITHHOLD THE WRITE, never to widen
  what counts as complete. `result_is_complete` keeps its exact meaning, including the CPO ruling
  of 2026-08-03 that an empty error-free response IS complete. An empty answer from a healthy
  provider still gets written and still marks the key captured — that is correct and it is what
  keeps 3,539 historical team-seasons out of a nightly re-fetch.

  NEW MECHANISM: none. Three helpers gain the return shape two siblings already have.
  RECURRING COST: a small INCREASE in API calls is the intended effect — keys that were wrongly
  marked captured will now be re-fetched once. Bounded by the existing skip logic and the daily
  quota guard; no change to cadence, fanout caps or history depth.

decisions_reserved:
  - The volume-delta threshold stays MR3 and stays the CPO's. This task only stops us recording a
    FAILED fetch as fact; it does not judge a SUCCESSFUL fetch that came back smaller.
  - Whether `event_loss_detector_from` should be lowered now that the backlog is triaged. It is
    2026-08-19 and therefore inert. Deliberately NOT bundled here: it is a dbt change with its own
    blast radius and it needs its own measurement (zero rows at the new cutoff) before it moves.

done_when:
  - `grep -rn "-> list:" ingestion/api_football/fixture_scheduling.py` shows no per-entity fetch
    helper returning a bare list.
  - `load_json_to_bq` cannot be called without stating `append`; the two deliberate WRITE_TRUNCATE
    callers say so explicitly.
  - A test proves each of the four holes RED against the current code before the fix, pasted into
    `.claude/task/acceptance_evidence.md`.
  - `python -m pytest tests/ -q` passes in full; `ruff --config .ruff-ci.toml` clean.
  - No change to `result_is_complete` or to what counts as complete.

amendments:
  - 2026-08-17: + `tests/test_player_squads_catchup.py` — authority: the same CPO go for MR2; no new
    decision. `squads_response_for_team` gains a second return value, and that file holds the one
    test double for it in the repo (`grep -rn "squads_response_for_team" tests/` → exactly one hit,
    line 176), still returning a bare list. Left alone it raises "not enough values to unpack",
    which the loader's own `except` swallows into an error string — so the suite would go red for a
    reason unrelated to the defect. Harness-only change: the fake returns `(rows, True)`; no
    assertion moves.
    ⚠ FOUND BY RUNNING THE SUITE, not by reading the diff. The signature change is invisible to a
    grep of the changed files, because the breakage lives in a file this task never intended to
    touch.
