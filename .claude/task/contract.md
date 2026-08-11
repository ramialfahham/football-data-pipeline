# Task contract — #53: correct the Macau/Mação event mis-attribution

objective: >
  The prod nightly has been FAILING and it recurs every 04:00 until this lands.
  `assert_event_team_in_fixture_participants` returned 10 rows on the 2026-08-11 run, `dbt build`
  halted on the error, and **540 of 970 nodes SKIPped**. Ingestion keeps succeeding, so `raw` is
  current while `dbt_analytics` silently is not.

  All 10 events sit in two WCQAS fixtures (1100381, 1100382 — the same two nations home and away)
  and every one is attributed to team 4767 (Mação, a Portuguese municipality) instead of 1544
  (Macau, the AFC member association). This appends ONE row to the existing CPO-owned override
  seed. **No model, macro or SQL changes** — the mechanism that consumes the seed already exists
  (`base_apif__fixture_events`, #526) and already carries two rows of exactly this class.
refs: >
  GitLab #53 (the failure, the evidence and the CPO RULING comment of 2026-08-11T12:02:55Z);
  GitLab #33 "SESSION END 2026-08-11" names this the first action. Refs #526 (the override
  mechanism and the guard), #546 (the standing DQ scan that keeps the class covered).

scope_paths:
  - dbt_project/seeds/fixture_event_team_overrides.csv
  - .claude/task/contract.md
  - .claude/task/escalations.log
  - .claude/task/review.md
  - .claude/task/review_input.patch

impact_map: >
  Not strictly gate-required — `dbt_project/seeds/**` is not on the structural surface
  (`ingestion/**`, `dbt_project/models/**`, `scripts/export_*.py`, `site*/`, protected paths).
  Written anyway, and evidenced rather than asserted, because this row CHANGES A SHIPPED NUMBER
  in a fact table and "seed, therefore trivial" is exactly the A6 dishonest-trivial tag.

  writers: the seed table `fixture_event_team_overrides` is written ONLY by `dbt seed`
    (`deploy/nightly/entrypoint.sh:53`, and `.gitlab-ci.yml`'s build jobs). No Python writes it.

  who READS it — exactly one model, confirmed by grep across the repo:
    `grep -rn "fixture_event_team_overrides" --include=*.sql --include=*.yml --include=*.py .`
    -> the only `ref()` is `dbt_project/models/2_base/api_football/base_apif__fixture_events.sql:88`.
    Every other hit is documentation (`base.yml:240`, `seeds/schema.yml:223`, a comment in
    `fct_fixture_event.sql:49`) or a compiled artefact under `target/`.
    NOTE `seeds/schema.yml:281` states explicitly that this seed is NOT part of the team-identity
    chain — an `alias` row here "folds no team, removes no URL and changes no slug". So nothing
    in `dim_team`, no page URL and no slug can move because of this change.

  downstream, PASTED from `dbt ls --select base_apif__fixture_events+ --resource-type model`
    (dbt 1.7.19 from the pinned venv, `DBT_PROFILES_DIR=C:/Users/Rami/.dbt`). **45 models**:
    2 base, 2 core, 22 intermediate, 19 marts. A first draft of this contract asserted a 7-model
    closure from memory and was wrong by a factor of six — the run is the evidence, the memory
    was not.

      2_base.api_football.base_apif__fixture_events
      2_base.api_football.base_apif__players
      3_core.dim_player
      3_core.fct_fixture_event
      4_intermediate.domestic_league.team_season.int_player_season__metrics
      4_intermediate.domestic_league.team_season.int_team_season__deserved_vs_actual
      4_intermediate.domestic_league.team_season.int_team_season__metrics
      4_intermediate.domestic_league.team_season.int_team_season__metrics_cumulative
      4_intermediate.shared.int_legs__player_match
      4_intermediate.shared.int_legs__team_from_players
      4_intermediate.shared.int_legs__team_match
      4_intermediate.shared.int_player_club_season__metrics
      4_intermediate.shared.int_player_competition_benchmarks
      4_intermediate.shared.int_player_momentum__metrics
      4_intermediate.shared.int_player_profile__contribution
      4_intermediate.shared.int_player_profile__yoy
      4_intermediate.shared.int_player_season__team
      4_intermediate.shared.int_player_season_position__metrics
      4_intermediate.shared.int_player_season_record
      4_intermediate.shared.int_team_competition_benchmark_metrics_long
      4_intermediate.shared.int_team_competition_benchmarks
      4_intermediate.shared.int_team_momentum__metrics
      4_intermediate.shared.int_team_momentum_window
      4_intermediate.shared.int_team_profile__streaks
      4_intermediate.shared.int_team_profile__yoy
      4_intermediate.shared.int_team_season_record
      5_marts.domestic_league.mart_matchday_insights
      5_marts.domestic_league.mart_team_season_insights
      5_marts.shared.mart_head_to_head
      5_marts.shared.mart_leaderboards
      5_marts.shared.mart_player_career
      5_marts.shared.mart_player_competition_benchmarks
      5_marts.shared.mart_player_fixture_stats
      5_marts.shared.mart_player_match_log
      5_marts.shared.mart_player_momentum
      5_marts.shared.mart_player_profile
      5_marts.shared.mart_player_season_record
      5_marts.shared.mart_roster
      5_marts.shared.mart_team_competition_benchmarks
      5_marts.shared.mart_team_fixtures
      5_marts.shared.mart_team_momentum
      5_marts.shared.mart_team_momentum_window
      5_marts.shared.mart_team_profile
      5_marts.shared.mart_team_season
      5_marts.shared.mart_team_season_record

    ⚠ THE CLOSURE IS WIDE, THE CHANGE IS NOT, and the two must not be conflated. That list is
    everything that would REBUILD, not everything whose numbers move — see blast_radius. It is
    wide because `base_apif__fixture_events` also feeds player discovery (`base_apif__players`
    -> `dim_player`), which pulls the whole player surface in.

  layer_rules: none engaged. No model file is touched, so `check_layer_contract.py` (which bans
    per-competition staging subdirectories and per-model materialisation overrides in `2_base`)
    has nothing to judge here. `check_registry_var_sync.py` governs `competition_registry.csv`,
    a different seed.

  deploy_order: nothing breaks at any point and NO backfill or `--full-refresh` is needed —
    `fct_fixture_event` is incremental, and `fct_fixture_event.sql:46-64` already carries a
    self-heal clause written for exactly this case (#526): it re-processes any fixture whose
    COMMITTED events violate the team-in-participants rule, so a seed-driven correction reaches
    rows committed before the fix. Self-limiting — once corrected the fixture no longer matches.
    ⚠ THE NIGHTLY RUNS AN IMAGE, NOT `main`. Cloud Run job `fdp-nightly` executes a container
    built from the repo, so merging alone does NOT deploy this. It needs
    `gcloud run jobs deploy fdp-nightly --source . --region europe-west1` from `main`
    (#39 Stage 3 — CI-side image build — is not built yet; #33 "Next, in order" item 5).

  blast_radius: **exactly 10 rows in `fct_fixture_event`**, measured against PROD on 2026-08-11,
    not asserted:
      · violating rows today: 10 — fixture 1100381 (7 events) + 1100382 (3 events), all
        `team_sk = 4767`, `league_code = WCQAS`.
      · events attributed to 4767 ANYWHERE else in the warehouse: **0**. The override's
        `wrong_team_api_id` matches nothing outside these two fixtures, so it cannot touch a row
        it was not written for.
      · fixtures where 4767 is a participant, warehouse-wide: **0**. So the
        `reattribute_if_cohabiting` guard "wrong id is NOT a participant" can never suppress a
        legitimate Mação event, because there are none.
      · `team_sk` on those 10 rows moves 4767 -> 1544. Both already exist in `dim_team`
        (4767 "Mação"/Portugal, 1544 "Macau"), so the `relationships` test on `team_sk` holds
        before and after.
    Downstream numbers that move: WCQAS only, and only for those two fixtures — Macau gains 10
    events it played, Mação loses 10 it did not. `mart_team_form` / `int_team_match_events` are
    keyed on the fixture's own participants, so a stat that was previously attributed to a
    non-participant was already unreachable there. Nothing else in the warehouse changes.

decisions_taken: >
  CPO ruling, GitLab #53 comment of 2026-08-11T12:02:55Z, verbatim: **"add the seed row"** —
  `reattribute_if_cohabiting`, NOT `alias`. Recorded durably in `.claude/task/escalations.log`
  (entry "2026-08-11 — #53") BEFORE this contract was written, and published on the issue before
  this branch existed, so a blinded reviewer can verify the ruling independently of this file.

  The mode is part of the ruling, not a builder choice, and the two are not interchangeable:
  `alias` replaces the id unconditionally and asserts "one club, two provider ids", which would
  permanently conflate a Portuguese municipality with a national team. `reattribute_if_cohabiting`
  fires only where the correct id IS a participant and the wrong id is NOT — the ASKO Kara
  precedent already in this seed.

  EXTERNAL VERIFICATION, required by this repo's standing rule before asserting two entity records
  relate: **Mação is a municipality in Portugal; Macau is an AFC member association.** A Portuguese
  municipality cannot play in the Asian section of World Cup qualifying. Both facts are externally
  checkable and were on #53 before the ruling. The internal evidence (0 fixtures as participant vs
  exactly the 2 mis-tagged) was re-measured against prod by this task rather than trusted from the
  issue text.

  ONE BUILDER DECISION, declared because it changes the row's bytes: the CPO's note text contains
  a comma ("Portuguese municipality, name collision") and this is a 4-column CSV, so unquoted it
  parses as 5 fields (counted with `csv.reader`, not eyeballed — a first draft said 6) and the
  seed breaks. The note is wrapped in double quotes — RFC 4180, already
  used in `team_name_overrides.csv` and `metric_catalogue.csv`. The VALUE is byte-identical to the
  CPO's; only the CSV framing differs.

  # THRESHOLD DECLARATIONS
  NEW MECHANISM — **no**. The override seed, both modes, the consuming join and the guard test all
  shipped under #526. This adds a third data row to an existing configuration table.
  RECURRING COST — **no new spend, and it removes waste**. The change is 1 row in a 3-row seed. It
  ends a nightly that currently burns a full ingest and 428 node builds and then throws the build
  away at the error, and it stops the `fdp-nightly execution failed` alert firing every morning on
  a known cause — an alert that fires daily on a known cause is one that gets muted.
  GUARD LOOSENED — **no**. `assert_event_team_in_fixture_participants` is untouched and stays
  `severity = 'error'`. The data is corrected so the guard passes; the guard is not moved to fit
  the data. A future occurrence of this class still fails the build.
  SHIPPED NUMBERS — **yes, 10 rows, quantified in blast_radius above**, which is why the impact_map
  is written in full rather than short-form.

decisions_reserved:
  - Whether `dim_team` should stop publishing Mação (4767) at all. It is a real Portuguese entity
    that never plays in our data, so today it exists only as an attribution artefact and, once the
    events move, as a team with no fixtures and no events. Product/URL surface — CPO-class, and
    out of scope for making the nightly green.
  - Whether the provider should be asked to correct the feed upstream. Every row in this seed is a
    permanent local patch for a defect we do not own.
  - Whether the two `RAW_APIF_*` snapshots behind these fixtures should be re-ingested rather than
    corrected downstream. Not proposed: the provider re-sends the same mis-attribution, which is
    the reason the override mechanism exists at all.

done_when:
  - The row is present in `dbt_project/seeds/fixture_event_team_overrides.csv` and the file still
    parses as 4 columns for EVERY row (`csv.reader`, assert every row has len == 4), with CRLF
    line endings and valid UTF-8 preserved.
  - `.venv/Scripts/dbt.exe parse` exits 0 (a malformed seed or schema is a parse error).
  - ⚠ THE MODE IS CONDITIONAL, SO THE SEED LANDING IN GIT IS NOT EVIDENCE. The override's join
    predicate is SIMULATED against PROD, read-only, by replaying
    `base_apif__fixture_events.sql`'s exact `reattribute_if_cohabiting` join with the proposed row
    UNIONed onto the live seed table, and the test predicate re-run over the result:
    **`assert_event_team_in_fixture_participants` must return 0 rows, and the 10 affected events
    must resolve to `team_id = 1544`.**
  - No `dbt build`, no `dbt seed`, no ingest and no `gcloud` resource is touched from this branch.
  - POST-MERGE, and NOT satisfiable from this branch (recorded so it is not mistaken for done):
    redeploy the `fdp-nightly` image from `main`, then run the real test SQL against prod and
    confirm `ERROR=0` on the next nightly rather than `ERROR=1 SKIP=540`.

amendments: (none)
