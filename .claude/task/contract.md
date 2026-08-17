# Task contract — a retry must not destroy match events (#75)

objective: >
  Fix the ingestion defect behind #75's red nights. `batch_fixtures.py` re-fetches a fixture when
  its STATISTICS array is empty (within 3 days of kickoff), and on retry it DELETES the stored
  payload and inserts whatever comes back — with no check that the replacement is as complete. The
  retry decision never looks at events, so a retry that successfully fills statistics can silently
  destroy match events.

  Downstream that surfaces as a red prod build: the lost events take their players with them, so
  `dim_player` loses a player the (incremental, accumulating) `fct_fixture_event` still references,
  the `player_sk -> dim_player` relationship test fails, `dbt build` SKIPS 103 nodes, prod is left
  half-built, and every subsequent MR goes red on an unrelated test.
refs: GitLab #75, !53, #72

impact_map: >
  MEASURED 2026-08-16 against prod, all figures from queries run for this task:
    · orphan FKs today: `fct_fixture_event` 1 (`player_sk` 544602), `fct_fixture_player_stats` 0.
    · base-vs-fact divergence: exactly 5 fixtures, 29 surplus event rows in the fact, out of 54,795
      fixtures. `fixtures_only_in_fct = 0`.
        1564793 CIT base 2 / fact 15 · 1564791 CIT 4/8 · 1564795 CIT 17/27 ·
        1490377 MLS 17/18 · 1507028 KL1 15/16 — all kickoffs 2026-08-08 or 2026-08-15.
    · DIRECTION, and it decided the whole design: the FACT is right, base is damaged. For 1564793
      the fact holds the full penalty shootout; base holds two goals. A "make the fact mirror base"
      fix was considered and REJECTED on this evidence — it would delete 13 real events from that
      fixture alone.
    · Live provider check: /fixtures?id= now returns 17 events for 1564795 (fact has 27) and 11 for
      1564793 (base has 2). So the loss is NOT recoverable by re-fetching, and this MR does not
      pretend otherwise.

  writer: `ingestion/api_football/loads/batch_fixtures.py` is the ONLY writer of
    `RAW_APIF_FIXTURE_DETAILS` — `_delete_fixtures()` then `_insert_fixture_rows()`. Retry set is
    built in `_plan()` from `_read_fetched_coverage()` + `_needs_fetch()`, gated on
    `_STATS_RETRY_DAYS = 3`.

  WHY KEEPING TWO ROWS PER FIXTURE IS SAFE — the verification that gated this change. FOUR staging
  models read that raw table and ALL read faithfully with NO dedup (`stg_apif__fixture_events`,
  `stg_apif__fixture_players`, `stg_apif__fixture_statistics`, `stg_apif__lineups`). Dedup lives in
  base, on ENTITY keys, latest-ingest-wins:
    · `base_apif__fixture_events`     partition by (league_code, fixture_id, event_index)
    · `base_apif__fixture_players`    partition by (league_code, fixture_id, team_id, player_id)
    · `base_apif__fixture_statistics` partition by (league_code, fixture_id, team_id)
    · `stg_apif__lineups` has NO consumer at all — `grep -rn "ref('stg_apif__lineups')"
      dbt_project/models/` returns nothing.
  So a second row MERGES per entity rather than duplicating, and an entity present only in the
  older payload survives. That is precisely the behaviour that would have preserved the shootout.

  downstream: no dbt file is changed by this MR. The raw table simply stops losing rows, so
  `base_apif__fixture_events` (and its sibling base models) see the union rather than only the
  newest payload. `dim_player` gains players it had lost; nothing loses rows.
  ⚠ `dbt ls` could NOT be run to confirm lineage: the dbt on PATH is the broken one and this clone
  has no `.venv` (#60). Lineage above is read from the model SQL and the yml declarations, and that
  limitation is stated rather than hidden (#904).

  layer_rules: `scripts/check_layer_contract.py` and `.claude/hooks/dbt_layer_gate.py` are
  unaffected — no model, no layer, no materialisation touched.

  deploy_order: takes effect on the next ingest. No warehouse migration, no backfill. The 29
  surplus fact rows are NOT deleted by this MR — they are real events and the only surviving
  record of them.

  blast_radius: `RAW_APIF_FIXTURE_DETAILS` keeps a second row for retried fixtures only (5 in the
  current window). No metric, no mart column, no number changes.

scope_paths:
  - ingestion/api_football/loads/batch_fixtures.py
  - tests/test_incomplete_fetch_no_supersede.py
  - docs/data_contract.md
  - .claude/task/escalations.log
  - .claude/active_work.md

decisions_taken: >
  CPO 2026-08-16, in sequence: "fix the two orphan rows" → "B" → "I want you to research thoroughly
  before you touch anything" → "yes, verify that and then build it". A retry that destroys real
  match events is a defect by any reading, and the fix is non-destructive.

  ⚠ TWO SELF-CORRECTIONS, recorded here and in escalations.log rather than quietly dropped:
  · "B" as I first described it ALREADY EXISTED. `base_apif__players` has unioned
    `base_apif__fixture_events` at `source_priority 3` all along. I recommended building something
    already built, having read `dim_player.sql` and not its source.
  · I then proposed making the fact mirror base. The measurement above shows that deletes real data.

  NEW MECHANISM: none. A DELETE is removed; an existing coverage query gains a GROUP BY.
  RECURRING COST: negligible and bounded — one extra raw row per RETRIED fixture (5 currently), no
  new job, no new schedule, no additional API calls. Strictly fewer destructive writes than today.

decisions_reserved:
  - ⛔ THE STANDING ORPHAN IS NOT CLEARED BY THIS MR, and I am not clearing it unilaterally. The
    provider no longer returns the lost events, so no ingest fix can restore player 544602 to
    `base_apif__players`. Clearing it needs one of: making player identity PERSIST across raw
    shrinkage (which means `materialized='incremental'` on a BASE model — and CLAUDE.md states
    materialisation is a LAYER decision set once in `dbt_project.yml` that a model "must never
    override per model, whatever the value", so it is a rule extension and the CPO's call); or a
    snapshot; or deleting the 29 fact rows (rejected above — they are real). Escalated separately
    with those alternatives.
  - Whether `_STATS_RETRY_DAYS = 3` is still the right window now that retries are non-destructive.
    Untouched here.

done_when:
  - `batch_fixtures.py` no longer deletes stored payloads on retry; `_delete_fixtures` is gone
    rather than left dead, and the module docstring no longer claims "exactly one row per
    (league_code, fixture_id)".
  - `_read_fetched_coverage` aggregates per fixture (done when ANY stored row has statistics), so a
    surviving older empty-statistics row cannot cause a permanent retry loop.
  - New tests in `tests/test_incomplete_fetch_no_supersede.py` — the EXISTING #896 module, not a
    new file — FAIL if the guard is removed or if the delete stops being limited to returned
    fixtures; each demonstrated RED before green.
  - `python -m pytest tests/` passes.
  - escalations.log records both self-corrections and the reserved decision above.

amendments:
  - 2026-08-16: + docs/data_contract.md — authority: Class-1 rule 5 (a raw-contract change must
    land WITH the doc), raised by data-engineer-reviewer round 1. `data_contract.md:110` states the
    fixture-details table "always holds the latest payload per fixture". After this guard it holds
    the latest COMPLETE payload — an incomplete retry is discarded rather than superseding. Leaving
    that sentence would be a stale claim contradicting the code beneath it, the same defect this
    repo fixed in `!45`'s seed description.
  - 2026-08-16: tests/test_batch_fixtures_retry.py -> tests/test_incomplete_fetch_no_supersede.py
    — authority: standing rule, fold into the authoritative artifact rather than creating a new one
    (`feedback_doc_clutter_discipline`). Content: `test_incomplete_fetch_no_supersede.py` IS the
    #896 module; it already pins the same rule for /players. A second file would have split one
    ruling across two homes and hidden the fact that this is a PORT of an existing guard, not a
    new one.
