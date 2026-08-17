# Task contract — raw appends and never deletes (#75, reverses #33 item 8b)

objective: >
  Remove every DELETE from the ingestion layer so the raw landing zone is append-only for all
  entity tables. The retention decision moves out of Python and into base, which already has the
  correct rule and is currently starved of the rows it needs to apply it. This closes three
  separate paths by which data we once held is destroyed permanently, and replaces five per-table
  write strategies with one rule.
refs: GitLab #75; reverses the delete half of #539 and of #33 item 8b; supersedes the narrower
  "#75 part A" scope recorded in `escalations.log` 2026-08-17.

scope_paths:
  - ingestion/api_football/bigquery.py
  - ingestion/api_football/completeness.py
  - ingestion/api_football/coverage.py
  - ingestion/api_football/refetch.py
  - ingestion/api_football/loads/competition_runner.py
  - scripts/diagnostics/reshape_players_to_team_season.py
  - tests/test_refetch_cadence.py
  - tests/test_incomplete_snapshot_not_written.py
  - ingestion/api_football/loads/batch_fixtures.py
  - ingestion/api_football/loads/squads.py
  - ingestion/api_football/loads/standings.py
  - ingestion/api_football/loads/teams.py
  - ingestion/api_football/loads/transfers.py
  - tests/test_raw_merge_on_write.py
  - tests/test_incomplete_fetch_no_supersede.py
  - tests/test_squad_players_rows.py
  - docs/data_contract.md
  - docs/roles/data_engineer.md
  - dbt_project/docs/layering.md
  - dbt_project/models/1_staging/api_football/stg_apif__fixture_events.sql
  - dbt_project/models/1_staging/api_football/stg_apif__fixture_players.sql
  - dbt_project/models/1_staging/api_football/stg_apif__fixture_statistics.sql
  - dbt_project/models/1_staging/api_football/stg_apif__lineups.sql
  - dbt_project/models/1_staging/api_football/stg_apif__generic.yml
  - .claude/active_work.md

impact_map: >
  WRITERS of the five affected raw tables, enumerated by grep, not memory
  (`grep -rn 'raw_table("TRANSFERS")\|..."STANDINGS"\|..."TEAMS"\|..."PLAYERS"\|..."FIXTURE_DETAILS"' ingestion/`):
    RAW_APIF_FIXTURE_DETAILS — `loads/batch_fixtures.py:266` (sole writer)
    RAW_APIF_PLAYERS         — `loads/squads.py:221` write, `:228` delete
    RAW_APIF_STANDINGS       — `loads/standings.py:72` write, `:82` delete
    RAW_APIF_TEAMS           — `loads/teams.py:78` write, `:96` delete
    RAW_APIF_TRANSFERS       — `loads/transfers.py:77` write, `:89` delete
  No other module writes any of them. `orchestrator.py:164` reads TRANSFERS only.
  Every call site of the three delete paths, complete:
    `bigquery.py:262` def; called at `standings.py:81`, `teams.py:95`, `transfers.py:88`
    `squads.py:43` def; called at `squads.py:227`
    `batch_fixtures.py:155` def; called at `batch_fixtures.py:293`
  Test references that must move with them: `test_raw_merge_on_write.py` (whole file premise),
  `test_incomplete_fetch_no_supersede.py:49,276`, `test_squad_players_rows.py:60,118`.

  DOWNSTREAM lineage, pasted from `dbt ls` (dbt 1.7.19, `--resource-type model --output name`),
  not asserted:
    `--select stg_apif__fixture_events+ stg_apif__fixture_players+ stg_apif__fixture_statistics+
      stg_apif__lineups+` -> 61 models, ending at mart_leaderboards, mart_matchday_insights,
      mart_player_career, mart_player_profile, mart_roster, mart_team_momentum_window,
      mart_team_profile, mart_team_season and 14 more.
    `--select stg_apif__transfers+ stg_apif__standings+ stg_apif__teams+ stg_apif__players+`
      -> 40 models, marts: mart_fixture_standing_context, mart_leaderboards,
      mart_matchday_insights, mart_player_career, mart_player_competition_benchmarks,
      mart_player_fixture_stats, mart_player_match_log, mart_player_profile, mart_roster,
      mart_standings, mart_team_competition_benchmarks, mart_team_fixture_stats,
      mart_team_fixtures, mart_team_market_value, mart_team_momentum_window, mart_team_profile,
      mart_team_season, mart_team_season_insights.
    `--select stg_apif__lineups+` -> returns only itself; that model has no consumer.

  LAYER RULES that apply: `layering.md` §1_staging says entity dedup belongs in base, never
  staging. That rule is unchanged by this task and is the reason no staging model needs an edit
  beyond its header comment: all four fixture-details staging models and `stg_apif__players`
  already read ALL rows with no latest-snapshot qualify, and carry `raw_ingested_at` in the grain.
  The three whole-league staging models (`stg_apif__standings`, `_teams`, `_transfers`) already
  apply `qualify row_number() over (partition by league_code order by ingested_at desc) = 1`, so
  they select the newest row and ignore the older ones that now survive. No SQL changes.

  DEPLOY ORDER: none required. This is an ingestion-side change; nothing in dbt is repointed and no
  model contract moves. The four dbt model edits are comment-only and change no compiled SQL.
  Sequencing against the 04:00 nightly is irrelevant because the change is subtractive at the
  storage layer: after merge the loaders simply stop issuing DML, and any row already deleted stays
  deleted.

  BLAST RADIUS on numbers: no mart column changes definition. Values can change in exactly one
  direction, and that is the intent of the ruling: where a provider answer had shrunk, base's
  existing newest-per-entity-key dedup now has the older rows to fall back on, so entities that
  would have been lost survive. Measured precedent, `escalations.log` 2026-08-17: fixture 1564795
  would yield 27 events instead of 17. The three whole-league staging models take the newest row
  only, so standings/teams/transfers numbers are unchanged on any run where the provider answered
  normally.
  NOT repaired by this change: the existing 5-fixture / 29-event backlog. Those events are gone at
  source. This stops future loss; it does not heal past loss.
  Storage: RAW_APIF_FIXTURE_DETAILS is 0.62 GiB and only retried fixtures gain a row.
  RAW_APIF_TRANSFERS is 0.178 GiB post-8b and gains one row per league per ingest (7-day cadence).

decisions_taken: >
  CPO ruling 2026-08-17, given in this conversation after two independent lead-data-engineer
  assessments were run blind and both returned the same root cause: raw stops deleting old rows
  EVERYWHERE, not only for fixture details. Asked as a single question with the cost stated on both
  options; the CPO chose "Everywhere". This extends his earlier ruling the same day, verbatim
  "raw keeps both versions", from one table to all of them, and it is the written form of his
  standing model: "raw and staging have whatever crap the provider gives us. in base we decide."

  RECORDED AS A REVERSAL, not a discovery. It reverses the delete half of #539 (2026-06-22) and of
  #33 item 8b (2026-08-09). Nobody may later restore a delete as a regression fix.

  WHAT THE REVERSAL COSTS, stated to the CPO before he ruled: the deletes existed for scan cost, and
  RAW_APIF_TRANSFERS did fall 6.99 GiB to 0.178 GiB under 8b. That justification is now obsolete for
  a different reason: staging became a stored table on 2026-08-13 (#33 items 9/10), so each raw
  table is parsed once a night instead of once per test. Going append-only costs roughly $1-2/month
  in extra scanning plus cents of storage.

  RECURRING COST: yes, and it is the threshold that made this CPO-class. About $1-2/month more
  scanning, cents/month more storage, zero additional API calls, no change to the quota or the run
  cadence. Approved explicitly, with the figure in front of him.
  NEW MECHANISM: none. This DELETES mechanisms; it adds none.

  NOT LOOSENED: every `result_is_complete` guard keeps its exact current behaviour. Refusing to
  write a known-partial payload is still right. What changes is that it stops being the only thing
  standing between a shrunken provider answer and permanent loss.

decisions_reserved:
  - The volume-delta threshold, meaning how much smaller a response may be before it is flagged
    rather than accepted. That is a product call, it is the CPO's, and it is MR3, not this task.
    This MR deliberately ships without it: append-only makes a shrunken answer recoverable, which is
    the precondition for deciding the threshold calmly later.
  - Whether to build the `raw_archive` backup that was the stated condition of approving
    merge-on-write in the first place, or to retire that condition on the record. Verified: zero
    references anywhere in the repo. Not raised as a blocker for this MR, which reduces the need for
    it, but it is unresolved and is the CPO's.
  - `.claude/agents/data-engineer-reviewer.md:36` asks a reviewer to check "merge-on-write
    preserved?", which becomes the wrong question after this MR. That file is a PROTECTED path and
    is deliberately NOT in scope_paths. Correcting it is its own governance task with a
    `protected_override`. Flagged, not touched.

done_when:
  - `grep -rn "delete from\|DELETE FROM" ingestion/` returns no hit that targets an entity raw
    table.
  - `python -m pytest tests/ -q` passes in full.
  - Every rewritten test is seen RED first by restoring the delete it guards against, with the
    failing output pasted into `.claude/task/acceptance_evidence.md`. A green test that was never
    seen red is decoration (#904).
  - `python -m ruff check --config .ruff-ci.toml ingestion tests` clean.
  - `dbt parse` succeeds (comment-only dbt edits must still compile). No `dbt build`, ever.
  - No document, comment or docstring ANYWHERE still describes a delete-on-retry or a
    merge-on-write as current behaviour, checked by
    `grep -rni "merge-on-write\|merge on write\|delete-on-retry" --include=*.py --include=*.md
     --include=*.sql --include=*.yml .` excluding `.git/`, `dbt_project/target/`,
    `escalations.log` and `docs/audits/` (both durable records of what was decided when).
    ⚠ THIS GREP WAS WRONG IN THE FIRST VERSION OF THIS CONTRACT and platform-reviewer caught it:
    it covered `docs/` and `dbt_project/` only, never `ingestion/`, even though the loaders being
    changed are the main place the claim lives. A verification step scoped narrower than its own
    sentence is the #904 failure class — the grep passed while four in-scope files still said the
    opposite of the change. Remaining permitted hits are past-tense, historical, or
    `.claude/agents/data-engineer-reviewer.md` (protected; see decisions_reserved).

amendments:
  - 2026-08-17: + `ingestion/api_football/refetch.py`, `completeness.py`,
    `loads/competition_runner.py` — authority: the SAME CPO ruling this contract already rests on
    (2026-08-17, "raw stops deleting old rows everywhere"). No new decision; these three files
    assert the removed behaviour as current fact and the original `scope_paths` simply missed them.
    Found by sweeping the class after data-engineer-reviewer round 1 FAILed the branch for exactly
    this — three module docstrings still saying "MERGE-ON-WRITE since #33 item 8b" eleven lines
    above code saying the delete was removed.
    Content, comments only, no logic: `refetch.py:20-21` is the load-bearing one — it justifies the
    7-day refetch cadence with "a partial write DELETES the complete row it supersedes.
    Unrecoverable", which is now false and would mislead the next person costing that decision.
    `competition_runner.py:128,201` describe coaches as "deliberately excluded from 8b's
    merge-on-write" and transfers as merge-on-write. `completeness.py:283,331` call
    RAW_APIF_PLAYERS merge-on-write; its conclusion (read in full, no per-run snapshot) stays
    correct, only the premise changes.
    ⚠ This is a correction-sweep amendment, not a scope widening: nothing new is BUILT, and no
    file gains a code change. Recorded because the alternative — leaving three files stating the
    opposite of the ruling — is the failure class the ruling was made about.
  - 2026-08-17 (second, and the last): + `scripts/diagnostics/reshape_players_to_team_season.py`,
    `tests/test_refetch_cadence.py`, `tests/test_incomplete_snapshot_not_written.py` — authority:
    the same ruling again. Comments and docstrings only; no assertion changes.
    ⚠ WHY THERE ARE TWO AMENDMENTS AND NOT ONE. The first was written from the reviewer's three
    named files. That is fixing the INSTANCE. Only then did I run the sweep that should have come
    first — `grep -rni "merge-on-write" --include=*.py --include=*.md --include=*.sql --include=*.yml`
    over the whole repo, excluding `.git`, `dbt_project/target/`, `escalations.log` and
    `docs/audits/` — which found three more. That grep output is the evidence the class is now
    closed; the remaining hits are past-tense ("was removed here", "8b shrank it to"), historical
    audit records, or `.claude/agents/data-engineer-reviewer.md`, which is protected and declared
    under decisions_reserved.
    `test_refetch_cadence.py:43,192` and `test_incomplete_snapshot_not_written.py:16,189` assert in
    prose that a partial write DELETES; that is the premise their cadence and guard reasoning rests
    on, and it is now false. `reshape_players_to_team_season.py:8` describes squads.py as
    merge-on-write.
