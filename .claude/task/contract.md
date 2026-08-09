# Task contract — #33 item 8b: merge-on-write for TRANSFERS, STANDINGS, TEAMS

objective: >
  Convert three append-only raw tables to merge-on-write keyed on `league_code`: append the
  fresh per-league snapshot, then delete that league's strictly-older rows. Raw stops growing
  with `competitions x runs` for these tables and becomes O(competitions). The prize is SCAN
  cost, not storage — `stg_apif__transfers` and its tests re-read the whole 6.99 GiB table on
  every build, and the two most expensive nodes in the warehouse are both scans of it.

  Scope is THREE tables, not the eight #33 names. Re-derived from the loaders and their
  consumers this session; two of the excluded tables are data-destruction hazards, not
  preferences. See decisions_taken.
refs: GitLab #33 item 8b (8a merged as !26, `main` @ 8ac63f6); #37 (the SQUADS exclusion)

scope_paths:
  - ingestion/api_football/bigquery.py
  - ingestion/api_football/loads/transfers.py
  - ingestion/api_football/loads/standings.py
  - ingestion/api_football/loads/teams.py
  - tests/test_raw_merge_on_write.py
  - docs/data_contract.md
  - .claude/task/contract.md
  - .claude/task/escalations.log
  - .claude/task/review.md
  - .claude/task/review_input.patch

impact_map: >
  writers: RAW_APIF_TRANSFERS is written ONLY by `loads/transfers.py:69` (one row per league,
    whole-league snapshot). RAW_APIF_STANDINGS only by `loads/standings.py:63`. RAW_APIF_TEAMS
    only by `loads/teams.py:69`. Verified by `grep -rn "raw_table(" ingestion/` — no second
    writer of any of the three, and no script under `scripts/` writes them.

  downstream: `dbt ls --project-dir dbt_project --select stg_apif__transfers+
    stg_apif__standings+ stg_apif__teams+ --resource-type model` (dbt 1.7.19, bigquery 1.7.2,
    94 models parsed) returns 29 models:

      1_staging: stg_apif__standings, stg_apif__teams, stg_apif__transfers
      2_base:    base_apif__standings, base_apif__teams, base_apif__teams_global,
                 base_apif__transfers
      3_core:    dim_player_team_season_mapping, dim_team, fct_standings, fct_transfer
      4_inter:   int_team_season__deserved_vs_actual, int_team_season__standings_primary
      5_marts:   mart_fixture_standing_context, mart_matchday_insights, mart_player_career,
                 mart_player_fixture_stats, mart_player_match_log, mart_player_profile,
                 mart_roster, mart_standings, mart_team_competition_benchmarks,
                 mart_team_fixture_stats, mart_team_fixtures, mart_team_market_value,
                 mart_team_momentum_window, mart_team_profile, mart_team_season,
                 mart_team_season_insights

  layer_rules: no dbt model, macro or seed is touched, so `check_layer_contract.py` and
    `check_registry_var_sync.py` are unaffected. The three staging models keep their
    `qualify row_number() over (partition by league_code order by ingested_at desc) = 1`
    unchanged — this task deliberately does NOT edit them.

  deploy_order: nothing breaks between merge and the next run. The raw SCHEMA is unchanged
    (`league_code, payload, ingested_at`); only row retention changes. The deployed staging
    models keep working against a table with one row per league exactly as they do against
    many. The first merge-on-write happens on the first nightly after merge (04:00 UTC,
    schedule 4379625). No backfill, no migration step, no dbt run required.

  blast_radius: NO mart number changes, and the reason is mechanical rather than empirical.
    All three staging models already select ONLY the latest row per `league_code`; the rows
    this task deletes are strictly older than the row written in the same call
    (`ingested_at < @before`, where `@before` is that write's own timestamp), so every deleted
    row is one the qualify was already discarding. The 29 models above read the same input
    before and after. Baseline for the post-merge check, `bq show` 2026-08-09:
      RAW_APIF_TRANSFERS  1,143 rows  6.986 GiB
      RAW_APIF_STANDINGS  1,673 rows  0.089 GiB
      RAW_APIF_TEAMS      1,673 rows  0.078 GiB
    45 active competitions, so each should settle at ~45 rows. Proportionally TRANSFERS lands
    near ~0.27 GiB; #33 predicts ~0.12 GiB. Rows are not uniform in size, so neither figure is
    asserted — the post-merge `bq show` settles it.
    REVERSIBLE: `raw_archive` holds `RAW_APIF_{TRANSFERS,STANDINGS,TEAMS}_20260808`,
    row-for-row verified (item 8 step 0, 2026-08-08).

decisions_taken: >
  CPO approved #33 item 8 on 2026-08-08 ("yes" to items 7, 8 and 9). Item 8 was then SPLIT into
  8a (the #896 completeness guard, merged as !26) and 8b (this task) on being shown that the
  approved change would destroy production data; the split is recorded in escalations.log,
  entry "2026-08-08 — #33 item 8 SPLIT into 8a/8b".

  This contract pre-approves the conversion of exactly THREE tables: TRANSFERS, STANDINGS,
  TEAMS. #33's text says "the eight append-only raw tables"; there are TEN, and the safe set is
  three. Excluded, with the reason each:
    - COACHES — `stg_apif__coaches.sql:1-7` reads ALL snapshots by an explicit CPO ruling
      (escalations.log, 2026-06-23) to preserve every coach ever seen; latest-per-league would
      drop ~120 coaches whose teams left our pull. A league-keyed delete destroys exactly that.
      A SECOND data-destruction hazard inside item 8, same class as the one that forced 8a.
    - SQUADS — the loader writes a TEAM SUBSET while staging reads latest-per-league. Verified
      in production 2026-08-09: WCQAF exposes 10 of 44 teams, CNL 2 of 22, AFCON 8 of 16.
      Filed as #37. Merge-on-write would make a recoverable staging bug permanent.
    - FIXTURES_NEXT — complete only via carry-forward and it has no #896 guard.
    - INJURIES — right shape, no guard, and #33 item 15 proposes deleting the endpoint.
    - LEAGUES — safe but tiny; no benefit against the added risk surface.
    - PLAYER_PROFILES, PLAYER_TEAMS — accumulate per player (`players_needing()` writes only
      newly-seen players). A league-keyed delete erases every player from earlier runs. NEVER.

  Reducing an approved item's scope is itself recorded in escalations.log with this task, per
  the 8a precedent (scope-auditor FAILed 8a round 1 for leaving the scope only in contract.md).

  `docs/data_contract.md` is edited under the CPO STANDING RULE of 2026-08-08: "Updating a
  reference that an approved change itself breaks is part of that change, not a scope
  extension — provided the update is confined to the reference and changes no behaviour."

  # THRESHOLD DECLARATIONS
  NEW MECHANISM — none. Merge-on-write already exists in this repo and this task adds no new
  class of thing: `loads/squads.py:43-74` (`_delete_superseded_player_rows`, keyed on
  `(league, team, season)`) and `RAW_APIF_FIXTURE_DETAILS` (keyed on `(league, fixture_id)`)
  both do it today, and `docs/data_contract.md:40-44` already documents merge-on-write as an
  established write mode. `delete_superseded_league_rows` is the whole-league variant of an
  existing function, placed in `bigquery.py` beside the other write helpers rather than copied
  into three loaders.

  RECURRING COST — YES, declared. This adds one DELETE query job per (league, table) per run:
  45 competitions x 3 tables = ~135 extra jobs per nightly. BigQuery bills DML at a 10 MB
  minimum, so ~1.35 GB/night ≈ $0.008/night ≈ $0.25/month at on-demand rates. This is a real
  increase and is offset by the scan reduction it buys (`base_apif__transfers` and
  `not_null_stg_apif__transfers_raw_ingested_at` were the two most expensive nodes measured, at
  $0.60 each per 6 days, both scanning the 6.99 GiB table). Declared here because a recurring
  cost is CTO-threshold and appears in no routing row.

decisions_reserved:
  - Whether FIXTURES_NEXT is ever converted. It needs a #896-style completeness guard first,
    because its snapshot is complete only via the carry-forward at `loads/fixtures.py:225-250`.
    Not decided here; not attempted here.
  - How #37 (the SQUADS subset/latest-row defect) is fixed — read it as accumulation
    (UNION ALL, like `stg_apif__player_profiles`) or make the loader carry forward. Entangled
    with #33 item 17, which asks whether `stg_apif__squads` should exist at all given zero
    `ref()`. Both are CPO calls; this task only excludes the table.
  - Whether INJURIES is converted or the endpoint is dropped (#33 item 15).
  - The COACHES all-snapshot read is CPO-ruled (2026-06-23) and is NOT revisited here.

done_when:
  - `pytest tests/ -q` exits 0 (baseline on main is 702 passed, 1 skipped; this adds cases).
  - `ruff --config .ruff-ci.toml ingestion/ tests/` exits 0.
  - Every new test verified by BREAKING its subject and confirming WHICH cases go red:
    remove the delete call (write/param/pinning cases fail); move the delete above the 8a
    completeness guard (the discard case fails); drop the `ingested_at <` bound (the
    survives-own-write case fails).
  - No `dbt build`, no `dbt run`, no ingest executed at any point.
  - Post-merge only (not on this branch): after one nightly,
    `SELECT league_code, COUNT(*) FROM raw.RAW_APIF_TRANSFERS GROUP BY 1 HAVING COUNT(*) > 1`
    returns zero rows, and `bq show` shows the table shrunk.

amendments: (none)
