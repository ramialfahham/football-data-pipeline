# Task contract — a team id that did not play the match

objective: >
  `not_null_dim_team_team_name` is FAILING the prod build and has been since 2026-09-07. It is an
  error-severity test inside the nightly's bare `dbt build`, so every model below `dim_team` is
  marked skipped and prod stops refreshing. The cause is one provider stub: API-Football filed the
  away lineup of BSA fixture 1492362 under a team id that did not play, with a null name, and
  `base_apif__teams` minted a `dim_team` row from it that nothing can ever name.
  This generalises the correction mechanism that already exists for fixture EVENTS to the other two
  fixture-level sources, corrects both live mis-attributions, and adds the two guards that would
  have caught them at their origin.

refs: >
  Not an issue — a live prod-build failure found while diagnosing MR !156's pipeline (#410,
  job 16358273358). It is the SECOND error in that run; the first was !156's own and is fixed there.
  ⭐ **THE APPROVED FIX WAS NOT SUFFICIENT AND I SAID SO BEFORE BUILDING IT.** The CPO approved
  *"go with A"* — `base_apif__teams` stops admitting a team key that no source can name. Measured
  against prod, that alone trades one failure for another: `fct_fixture_player_stats` carries 21 rows
  with `team_sk = 22722` and `core.yml:725` has an error-severity `relationships` test on that
  column. 41 such tests point at `dim_team`, none filtered, all at error severity. The rows have to
  stop carrying the id; deleting the key is not a fix. Put back to him with the measurement, and the
  enlarged approach was approved in plan mode.
  ⭐ **The one decision that was his and not mine — the seed's NAME.** Generalising an overrides seed
  from one source to three makes `fixture_event_team_overrides` a lie, and a seed rename is permanent
  (it renames the BigQuery table). Asked with three options and a recommendation; he ruled
  **`fixture_team_id_overrides`**. Recorded in `escalations.log`.

scope_paths:
  - .claude/task/contract.md
  - .claude/task/acceptance_evidence.md
  - .claude/task/review.md
  - .claude/task/review_input.patch
  - .claude/task/escalations.log
  - dbt_project/seeds/fixture_event_team_overrides.csv
  - dbt_project/seeds/fixture_team_id_overrides.csv
  - dbt_project/seeds/schema.yml
  - dbt_project/models/2_base/api_football/base_apif__fixture_events.sql
  - dbt_project/models/2_base/api_football/base_apif__fixture_players.sql
  - dbt_project/models/2_base/api_football/base_apif__fixture_statistics.sql
  - dbt_project/models/2_base/api_football/base_apif__teams.sql
  - dbt_project/models/2_base/api_football/base.yml
  - dbt_project/models/3_core/fct_fixture_event.sql
  - dbt_project/tests/assert_event_team_in_fixture_participants.sql
  - dbt_project/tests/assert_player_stats_team_in_fixture_participants.sql
  - dbt_project/tests/assert_team_stats_team_in_fixture_participants.sql

impact_map: >
  writers: no ingestion code touched. The raw tables are unchanged — the provider's bytes stay
  exactly as received, and the correction is applied in BASE, which is where this repo has ruled
  entity corrections belong (CPO, 2026-07-27: base prepares, the dim propagates).
  layer_rules: `check_layer_contract.py`. A provider id mis-attribution is a correction to the
  entity, not a metric, so it belongs in base and not in core, a mart or the export. Staging keeps
  parsing what the provider sent; nothing here rewrites raw.
  ⛔ **THE OVERRIDE MUST BE APPLIED BEFORE EACH MODEL'S DEDUP, NOT AFTER.** Both target models
  dedupe on a key containing `team_id` — statistics on `(league_code, fixture_id, team_id)`, players
  on `(league_code, fixture_id, team_id, player_id)` — and both carry a uniqueness test on that
  grain. Remapping after the dedup can emit two rows for one `(fixture, team)` if the correct id
  already has one; remapping before it lets the model's existing "latest ingest wins" rule resolve
  the collision. Neither live case collides today (checked: fixture 1492362 has no rows for 132,
  fixture 1100382 none for 1544), so this is a rule for the next one, not a fix for these.
  ⚠ `base_apif__fixture_players`' cross-team collision guard (`min(team_id) = max(team_id)` over the
  fixture and player) reads `team_id`, so it now sees corrected ids. That is the intended direction:
  a player appearing under both a wrong id and its correct one was never a real collision.
  downstream of the two corrected base models:
      base_apif__fixture_players     -> fct_fixture_player_stats -> int_legs__player_match,
                                        int_player_* , mart_player_* , mart_roster
      base_apif__fixture_statistics  -> fct_fixture_team_stats   -> int_legs__team_match,
                                        int_team_* , mart_team_*
  None of them is EDITED. They see 22 rows change their `team_sk` and nothing else; no column is
  added, renamed or retyped anywhere in the chain.
  ⚠ `base_apif__teams` also reads the fixture-level sources, but from STAGING, so a correction
  applied in base would not reach it and the nameless key would be minted again. Its KEY union takes
  the corrected ids. Its four NAME sources are left reading staging deliberately —
  `base_apif__fixture_players` and `base_apif__fixture_statistics` drop `team_name` at base, so
  re-pointing the name CTEs would silently remove a name path other teams may depend on.
  ⛔ **deploy_order: A ONE-OFF `--full-refresh` OF THE TWO FACTS IS REQUIRED, AND WITHOUT IT THIS
  MR BREAKS THE NIGHTLY.** An earlier version of this paragraph said `fct_fixture_event` was the
  only incremental model in the chain. That was written from memory and is FALSE.
  `fct_fixture_player_stats` and `fct_fixture_team_stats` are BOTH `materialized='incremental'`,
  both filtered on a bare `raw_ingested_at` high-water mark, and neither has the self-heal clause
  #526 added to the events model. A finished fixture's stats never get a newer `raw_ingested_at`,
  so on a bare `dbt build` the corrected rows are never re-processed: `base_apif__teams` (a table,
  rebuilt nightly) would stop emitting 22722 while the fact kept 21 rows carrying it — the exact
  orphan this MR exists to prevent, plus both new guards red in prod.
  ⚠ **Copying the events self-heal would NOT fix it**, and that is a property of the keys rather
  than of the predicate. `fixture_player_stat_sk` is hashed on
  `(fixture_id, league_code, team_id, player_id)` and `fixture_team_stat_sk` on
  `(fixture_id, league_code, team_id)` — correcting `team_id` CHANGES the unique key, so an
  incremental merge inserts the corrected row and strands the old one, which dbt never deletes.
  The events self-heal works only because `event_sk` is hashed on `(fixture_id, event_index)` and
  excludes `team_id`.
  ⭐ A full refresh of these two is SAFE, and that is measured rather than assumed: both facts have
  exactly the row count of their base tables (1,875,238 and 99,140), so nothing accumulated there is
  absent from base. `fct_fixture_event` does NOT have that property — 858,032 against 858,015, 17
  rows it retains that base no longer produces — which is why its incrementality is load-bearing and
  why this MR does not touch it. Combined size to rebuild: 0.39 GiB, about 0.3% of one night's
  measured pipeline volume.
  The command is the CPO's to run, once, at merge; `dbt build` is banned here.
  blast_radius: 22 rows across two facts, in two fixtures, in two competitions, plus TWO team keys
  removed from `base_apif__teams` — `(BSA, 22722)` and, unforeseen when this contract was first
  written, `(UEL, 2263)`. The second is Riga FC's duplicate provider id, an `alias` row in the seed
  since #526 whose correction had never reached the entity dimension because the override was wired
  to events only. ⭐ **No team's slug moves**: recomputing the whole slug ladder over the corrected
  key set gives 0 slugs changed across 3,329 teams, 0 rows added, 0 nameless rows. The two removed
  rows take their own slugs (`riga-fc`, `team-22722`) with them and no surviving team's URL changes.
  Asserted by running both chains against prod, not by reading the SQL.

acceptance_criteria:
  - The 21 `fct_fixture_player_stats` rows on BSA fixture 1492362 move from `team_sk` 22722 to 132,
    and the 1 `fct_fixture_team_stats` row on WCQAS fixture 1100382 moves from 4767 to 1544.
    Measured against LIVE PROD by composing the changed chain, not asserted from the seed.
  - **No other row in either fact changes its `team_sk`.** Reported two-sided — the count that
    moves AND the count that does not — over the full tables, not as a spot check.
  - `base_apif__teams` emits EXACTLY TWO fewer keys than main and no new ones: `(BSA, 22722)` and
    `(UEL, 2263)`, with 4,618 unchanged. ⚠ This criterion originally read "no longer emits 22722,
    and emits the same key set as main otherwise" — written before the measurement and false once
    the measurement existed, because applying the seed's `alias` mode to the key union also retires
    Riga FC's duplicate id. Corrected rather than reworded: the second removal is a real
    consequence and it belongs in the criterion, not in a footnote.
  - **No team's slug changes.** The slug ladder is recomputed over the corrected key set and
    compared against `dim_team` row by row: 0 changed, 3,329 unchanged, 0 added. A slug is assigned
    once and is a URL (#852), so a key removal that reshuffled a surviving team's slug would be a
    far bigger change than this MR is entitled to make.
  - **The corrected rows actually reach prod.** Both target facts are incremental on a
    `raw_ingested_at` high-water mark that a finished fixture never advances, so the deploy REQUIRES
    a one-off `--full-refresh` of `fct_fixture_player_stats` and `fct_fixture_team_stats`. Shown
    safe by both facts having exactly their base tables' row counts, so a rebuild loses nothing.
  - No orphan is created: every `team_sk` in both facts still resolves to a `dim_team` row, so the
    41 error-severity `relationships` tests pointing at `dim_team` stay green.
  - `assert_player_stats_team_in_fixture_participants` and
    `assert_team_stats_team_in_fixture_participants` return 0 rows on the corrected chain, and
    return 21 and 1 rows respectively when the corrections are reverted. **Watched RED**, not
    assumed — a passing test proves nothing until it has failed.
  - The renamed seed keeps its `not_null` / `unique` / `accepted_values` tests, and **GAINS a
    `relationships` test** from `correct_team_api_id` to `dim_team.team_api_id`. ⚠ This criterion
    first claimed the seed already HAD that test. It never did, under either name — I misattributed
    a `relationships` block belonging to `team_name_overrides` and asserted a safety net that did
    not exist. The hole is real: `correct_team_api_id` is hand typed, and a typo does not fail
    loudly, it silently re-points a fixture's rows at whichever real team the mistyped id names.
    The participant guards cannot catch that — they only ask whether the team played the fixture.
    Written rather than deleted, because the criterion described the right check.
  - `dbt parse` exits 0; SQLFluff passes from the repo root on every changed model, exit code read
    BARE and unredirected; `check_layer_contract.py`, `check_registry_var_sync.py`,
    `check_description_hygiene.py` and `check_competition_type_seed.py` all pass.

decisions_taken: >
  ⭐ **GENERALISE THE MECHANISM, REGISTER THE INSTANCE.** The seed is the correction registry and a
  new mis-attribution is one hand-written row in it, reviewed once, with a staleness test — the
  pattern every other override seed in this repo already follows (`team_name_overrides`,
  `country_name_overrides`, `league_name_overrides`). What was missing was not a smarter rule, it was
  the same rule wired to all three fanout sources instead of one.
  ⛔ **NO AUTOMATIC RE-ATTRIBUTION.** It is tempting to reassign a non-participant block to
  "whichever participant has no rows", which would have fixed both cases with no seed row at all.
  Rejected: it is a derivation that invents attribution from an absence, it fires silently, and the
  first time the provider sends a genuinely unknown team it would launder junk into a real club's
  record. A correction a human has not looked at is not a correction.
  ⛔ **INLINE SQL, NOT A MACRO.** The override join is now repeated in three base models. A macro is
  the obvious DRY move and is deliberately not taken — the recorded preference in this repo is
  inline SQL and the COMPOSE pattern over Jinja macros, because a macro hides the join condition
  from the reader of the model that depends on it. The three copies are near-identical by design and
  the two new guards are what keeps them honest.
  ⛔ **`not_null` ON `dim_team.team_name` IS NOT TOUCHED.** It is the backstop and it did its job —
  loudly, and at the worst possible moment, which is what a backstop is for. The new guards catch
  the class earlier and name the fixture; loosening the last line because a better check now exists
  upstream is exactly the move that ships a silent hole.
  ⛔ **KEEP BOTH FACTS INCREMENTAL AND PAY A ONE-OFF FULL REFRESH — the alternative was measured and
  is worse.** Making them tables would guarantee every future seed correction lands with no manual
  step, and it would cost about 0.39 GiB a night, which is nothing. It was rejected on evidence:
  `fct_fixture_event` holds 17 rows its base table no longer produces, so an incremental fanout fact
  DOES accumulate rows that staging has stopped returning. These two match their bases exactly today,
  but that is a fact about today's payloads, not a property of the design — dropping them to tables
  would trade a loud, one-off deploy step for silent data loss the first time the provider stops
  returning a fixture. A manual step that fails LOUDLY beats an automatic one that fails quietly.
  ⭐ **THE SECOND INSTANCE WAS FOUND BY THE GUARD, NOT BY THE BUG REPORT.** Running the
  event guard's predicate against the other two facts before writing anything turned up Mação 4767
  on WCQAS fixture 1100382 — a mis-attribution already diagnosed under #53, already written into the
  seed, and never applied to team statistics because the override join existed only for events. It
  is wrong in prod today. Fixed here because it is the same class and the same mechanism, and
  leaving it would mean shipping the guard that fails on it.

decisions_reserved: >
  - **The freshness guard.** `assert_fct_fixture_no_stale_live` is the OTHER nightly failure and
    stays open. ⭐ It is not an unrelated coincidence: because everyone knew why the nightly was red,
    this defect rode along unnoticed for three nights. A permanently red test is not one broken
    check, it is cover for the next one.
  - **`base_apif__players` has the identical latent exposure.** It unions three name sources,
    prefers the most authoritative NAMED one, and drops nobody whose name is null everywhere — while
    `dim_player.player_name` carries the same error-severity `not_null`. The player line has simply
    not been unlucky yet. Not fixed here: it is a different entity, a different set of sources, and
    folding it in would double an MR that is already correcting two facts.
  - **The handover correction.** `.claude/active_work.md` still says the nightly put
    `is_current_season` in prod; it was `data:build:main`. Unrelated to this branch, still owed.
