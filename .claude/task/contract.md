# Task contract — a test that detects EVENT LOSS (#75 part C)

objective: >
  Add the one guard whose absence is why #75 was found by accident. `fct_fixture_event` is
  incremental and accumulates; `base_apif__fixture_events` is rebuilt from current raw. When a
  fixture's raw payload loses events, the fact keeps them and base does not — and NOTHING in the
  test suite notices. The 29 lost events sat undetected for days and surfaced only as an unrelated
  `dim_player` FK orphan, which is why it first looked like a player problem.

  This adds a singular test that flags any event the fact holds which base no longer has.
refs: GitLab #75, !56 (the ingestion guard), !53

impact_map: >
  WHAT THIS TEST READS: `fct_fixture_event` (core, incremental) and `base_apif__fixture_events`
  (base, table). It is a leaf assertion — nothing reads it, it writes nothing, and it changes no
  model, column, grain or materialisation. `dbt ls` could not be run (broken dbt on PATH, no
  `.venv` — #60), so this is read off the model files; stated rather than hidden (#904).

  MEASURED AGAINST PROD, 2026-08-17, before writing the assertion:
    · Event-index-level comparison finds **29 lost events across exactly 5 fixtures**
      (1564793 CIT, 1564791 CIT, 1564795 CIT, 1490377 MLS, 1507028 KL1) — the same set #75
      documents, reproduced independently by this test's own logic.
    · With the cutoff at 2026-08-17, **1 row still flags**: one damaged fixture was re-ingested
      this morning because its 3-day retry window (kickoff 2026-08-15) is still open.

  SCOPE IS TAKEN FROM THE FIXTURE (kickoff date), NOT FROM BASE — corrected in round 1.
  analytics-engineer-reviewer FAILED the first draft, which grouped `max(raw_ingested_at)` over
  `base_apif__fixture_events` itself: if a fixture loses ALL its events base holds zero rows, the
  grouped CTE yields nothing, and the inner join silently drops that fixture — the TOTAL-loss case,
  undetectable at any cutoff, forever. My prod measurement could NOT have caught it (the known
  incident was PARTIAL for all 5 fixtures); it was found by reading the join. Scoping on
  `fct_fixture` (one row per fixture, always present) removes the dependency on base surviving.
  A kickoff date also never moves, unlike an ingest timestamp — the damaged fixtures kept
  refreshing `raw_ingested_at` while their retry window stayed open, which is why the ingest-time
  cutoff still flagged 1 row when measured on 2026-08-17.
  ⚠ CONSEQUENCE, STATED NOT HIDDEN: the test is **inert for fixtures before the cutoff**. Its logic
  is proven against real damage (29 rows across 5 fixtures at an earlier cutoff, under BOTH scoping
  designs), but a green run over a window containing no fixtures is not evidence.

  TWO SIBLING TESTS WERE DESIGNED AND REJECTED ON THE DATA, recorded so they are not re-proposed:
    · "a PEN fixture must carry shootout events" — **371 of 753** PEN fixtures in prod have none.
      The provider does not supply them for many competitions. It would have turned half the
      penalty shootouts in the warehouse red.
    · "goal events must reconcile with the fixture score" — not written. After the PEN result there
      is no evidence it is clean across own goals, disallowed goals and shootout exclusion, and
      shipping it unverified would repeat the same mistake.

  layer_rules: `scripts/check_layer_contract.py` / `.claude/hooks/dbt_layer_gate.py` — a singular
  test in `dbt_project/tests/` touches no layer. `severity = 'error'`, consistent with the other
  integrity guards (`assert_event_team_in_fixture_participants`).

  deploy_order: none. It runs in the existing singular-test steps of `data:build:mr`,
  `data:build:main` and the nightly. No backfill, no migration.

  blast_radius: no mart, no column, no row changes. One new assertion.

scope_paths:
  - dbt_project/tests/assert_no_event_loss_since_cutoff.sql
  - dbt_project/dbt_project.yml
  - .claude/task/escalations.log
  - .claude/active_work.md

decisions_taken: >
  CPO 2026-08-17: "do C", then — on being shown that two of the three designed tests died against
  the data and the third goes red on the existing backlog — "scope it to new data". This builds the
  third test only, scoped by ingest time, as instructed.

  NEW MECHANISM: none. A singular test, the same shape as the existing integrity guards.
  RECURRING COST: one additional singular test per build. It reads two existing tables; no new
  object, no schedule change.

decisions_reserved:
  - The 5 damaged fixtures are NOT repaired by this and are deliberately outside the cutoff. Whether
    a COMPLETE provider response carrying strictly less data may supersede stored data remains the
    CPO's open question (#896 rules it the other way today) — that is plan part A, not this.
  - Whether the cutoff should later be lowered once the backlog is resolved. Left as a var so it is
    a one-line change with a recorded reason, not a code rewrite.

done_when:
  - The test returns 0 rows against prod at the shipped cutoff, and returns the 29 known rows when
    the cutoff is moved back — demonstrated by running BOTH, not asserted.
  - `python scripts/check_layer_contract.py` passes; SQLFluff clean on the new file from the repo
    root with the full rule set.
  - escalations.log records the two rejected sibling tests with their measured reasons.

amendments: (none)
