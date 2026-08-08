# Task contract — Gate 0.2 + Wave 1 items 5 and 6 (#33)

> Branch `chore/gate0-truth-and-dbt-deadwood` from `main` (`6352d7d`), in the worktree
> `D:\Projects\fdp-pipeline`. No PROTECTED path, so no `protected_override`.
> `dbt_project/models/**` IS the structural surface, so an `impact_map` is REQUIRED and is
> below. No `site_v2/src/`, so no `acceptance_criteria`.

objective: >
  Land Gate 0.2 and Wave 1 items 5 and 6 of GitLab issue #33 — the pipeline cost/scalability
  plan. Three separable things that share one reviewer set and touch disjoint files from the
  other two Wave 1 MRs:

  (a) GATE 0.2 — correct four statements in `CLAUDE.md` that are false today, plus the stale
  headline of the memory file `project_dbt_shared_ci_prod_datasets.md`. #33 puts this first
  because every later item is reviewed against these statements, and three of the four would
  actively mislead a reviewer judging the rest of the plan.

  (b) ITEM 5 — drop the `source_json` column from the 9 staging models that emit it. It has
  zero consumers. Near-free today because BigQuery prunes an unused output column of a view,
  but staging becomes a TABLE in Wave 2 item 9, at which point this column is the dominant
  stored bytes. #33 makes item 5 a hard prerequisite of item 9; this is that prerequisite.

  (c) ITEM 6 — delete zero-caller / zero-use deadwood: two macros, a documented pre-filter
  that exists in no model, and the `dbt_expectations` package.

  CONSULTED BEFORE BUILDING (§2 norm): `dbt ls` for the real downstream closure rather than
  memory; `dbt_project/docs/layering.md` for what staging may and may not do; the actual
  `qualify` forms in all 15 staging models before rewriting the data contract's description
  of them.

refs: >
  GitLab issue #33 (the working brief for the pipeline stream) — Gate 0.2, Wave 1 items 5
  and 6. Supersedes the ranking in #32. Related: #892 (why a time-based raw pre-filter is
  unsafe), #547 (base materialised as table, 2026-08-02).

scope_paths:
  - CLAUDE.md
  - docs/data_contract.md
  - dbt_project/packages.yml
  - dbt_project/package-lock.yml
  - dbt_project/macros/apif_latest_source_partition.sql
  - dbt_project/macros/domestic_league_codes_in_clause.sql
  - dbt_project/models/1_staging/api_football/stg_apif__fixtures_next.sql
  - dbt_project/models/1_staging/api_football/stg_apif__fixture_events.sql
  - dbt_project/models/1_staging/api_football/stg_apif__fixture_players.sql
  - dbt_project/models/1_staging/api_football/stg_apif__fixture_statistics.sql
  - dbt_project/models/1_staging/api_football/stg_apif__leagues.sql
  - dbt_project/models/1_staging/api_football/stg_apif__lineups.sql
  - dbt_project/models/1_staging/api_football/stg_apif__players.sql
  - dbt_project/models/1_staging/api_football/stg_apif__standings.sql
  - dbt_project/models/1_staging/api_football/stg_apif__teams.sql

impact_map: >
  WRITERS of the changed surface.
  `source_json` is emitted by exactly 9 models and by nothing else. Verified by repo-wide
  grep, not from memory:
      $ grep -rn "source_json" --include=*.sql --include=*.yml --include=*.py --include=*.md \
          --include=*.json . | grep -v node_modules
      ./dbt_project/models/1_staging/api_football/stg_apif__fixtures_next.sql:25
      ./dbt_project/models/1_staging/api_football/stg_apif__fixture_events.sql:38
      ./dbt_project/models/1_staging/api_football/stg_apif__fixture_players.sql:80
      ./dbt_project/models/1_staging/api_football/stg_apif__fixture_players.sql:126
      ./dbt_project/models/1_staging/api_football/stg_apif__fixture_statistics.sql:33
      ./dbt_project/models/1_staging/api_football/stg_apif__leagues.sql:65
      ./dbt_project/models/1_staging/api_football/stg_apif__lineups.sql:32
      ./dbt_project/models/1_staging/api_football/stg_apif__players.sql:49
      ./dbt_project/models/1_staging/api_football/stg_apif__standings.sql:49
      ./dbt_project/models/1_staging/api_football/stg_apif__teams.sql:25
  The two hits in `stg_apif__fixture_players.sql` are one column carried through an internal
  CTE (line 80 defines it, line 126 re-selects it in the final select of the same model), not
  two columns. Upstream of these models the raw writers are the ingestion loaders under
  `ingestion/api_football/loads/`; they are NOT touched by this task and the raw `payload`
  column they write is unchanged, so `source_json` disappearing changes nothing about what is
  stored in `raw`.

  DOWNSTREAM — the full closure, pasted from the command, not asserted:
      $ dbt ls --resource-type model --select stg_apif__fixtures_next+ stg_apif__fixture_events+ \
          stg_apif__fixture_players+ stg_apif__fixture_statistics+ stg_apif__leagues+ \
          stg_apif__lineups+ stg_apif__players+ stg_apif__standings+ stg_apif__teams+
      Found 94 models, 870 tests, 6 seeds, 11 sources, 0 exposures, 0 metrics, 853 macros
      -> 78 models: the 9 changed + 69 downstream.
      Counted mechanically, not by hand — the first version of this map said 79/70 with a
      "4_intermediate (24)" header over a 23-item list, `analytics-engineer-reviewer` FAILed it
      at round 1, and it was right (a #904-class recurrence). The count now comes from:
        $ dbt ls --resource-type model --select <the 9>+ | grep "^football_data_pipeline\." > closure.txt
        $ wc -l < closure.txt                      -> 78
        $ for L in 1_staging 2_base 3_core 4_intermediate 5_marts; do grep -c "\.$L\." closure.txt; done
                                                   -> 9, 12, 11, 23, 23
      1_staging (9): stg_apif__fixture_events, stg_apif__fixture_players,
        stg_apif__fixture_statistics, stg_apif__fixtures_next, stg_apif__leagues,
        stg_apif__lineups, stg_apif__players, stg_apif__standings, stg_apif__teams
      2_base (12): base_apif__competition_seasons, base_apif__fixture_events,
        base_apif__fixture_players, base_apif__fixture_statistics, base_apif__fixtures_next,
        base_apif__league_entity, base_apif__leagues, base_apif__player_team_season,
        base_apif__players, base_apif__standings, base_apif__teams, base_apif__teams_global
      3_core (11): dim_competition_season, dim_league, dim_player,
        dim_player_team_season_mapping, dim_team, dim_team_competition_season_mapping,
        fct_fixture, fct_fixture_event, fct_fixture_player_stats, fct_fixture_team_stats,
        fct_standings
      4_intermediate (23): int_legs__player_match, int_legs__team_from_players,
        int_legs__team_match, int_player_club_season__metrics,
        int_player_competition_benchmarks, int_player_momentum__metrics,
        int_player_profile__contribution, int_player_profile__yoy, int_player_season__metrics,
        int_player_season__team, int_player_season_position__metrics, int_player_season_record,
        int_team_competition_benchmark_metrics_long, int_team_competition_benchmarks,
        int_team_momentum__metrics, int_team_momentum_window, int_team_profile__streaks,
        int_team_profile__yoy, int_team_season__deserved_vs_actual, int_team_season__metrics,
        int_team_season__metrics_cumulative, int_team_season__standings_primary,
        int_team_season_record
      5_marts (23): mart_fixture_standing_context, mart_head_to_head, mart_leaderboards,
        mart_matchday_insights, mart_player_career, mart_player_competition_benchmarks,
        mart_player_fixture_stats, mart_player_match_log, mart_player_momentum,
        mart_player_profile, mart_player_season_record, mart_roster, mart_standings,
        mart_team_competition_benchmarks, mart_team_fixture_stats, mart_team_fixtures,
        mart_team_market_value, mart_team_momentum, mart_team_momentum_window,
        mart_team_profile, mart_team_season, mart_team_season_insights,
        mart_team_season_record

  BLAST RADIUS: none. No mart column, no displayed number, no test changes.
  The claim is "no consumer exists", so the search is as wide as the claim — every model
  layer, every macro, every singular test, every seed, the export scripts, the built
  frontend, and the python test suite:
      $ grep -rn "source_json" dbt_project/models/2_base dbt_project/models/3_core \
          dbt_project/models/4_intermediate dbt_project/models/5_marts dbt_project/macros \
          dbt_project/tests dbt_project/seeds scripts site_v2/src tests
      (no output; exit 1)
      $ grep -rn "source_json" --include=*.yml dbt_project/
      (no output; exit 1)
  So no schema.yml documents or tests the column either — dropping it removes no test.
  The 69 downstream models above are the set CI will rebuild under `state:modified+`; that
  build is the executable proof of this "none", because a consumer would fail to compile.

  The two deleted MACROS have zero callers in compiled code:
      $ grep -rn "apif_latest_source_partition\|domestic_league_codes_in_clause" \
          --include=*.sql --include=*.yml --include=*.py --include=*.md .
      ./.claude/active_work.md:160                       (a note saying to delete it)
      ./.github/workflows/pages-match-preview.yml:21     (path filter, dormant tree)
      ./dbt_project/macros/apif_latest_source_partition.sql:23,31  (its own docstring + def)
      ./dbt_project/macros/domestic_league_codes_in_clause.sql:1   (its own def)
      ./docs/product_direction_threads.md:12             (dated log of a CLOSED thread)
  No model, test or seed invokes either.

  `dbt_expectations` is used nowhere. Repo-wide, excluding the installed package tree:
      $ grep -rn "dbt_date\|dbt_expectations" . | grep -v /dbt_packages/ | grep -v /node_modules/
      ./dbt_project/package-lock.yml:4,6
      ./dbt_project/packages.yml:4
  Removing it also removes its TRANSITIVE dependency `godatadriven/dbt_date` (observed in
  `dbt deps` output), which is likewise referenced by nothing. `dbt-labs/dbt_utils` stays and
  IS used.

  LAYER RULES that apply. `scripts/check_layer_contract.py` (run in `validate:governance`):
  no per-competition staging subdirectory; no per-model materialisation override in `2_base`.
  Neither is affected — no directory is added, no `materialized` config is touched.
  `dbt_project/docs/layering.md` §1_staging: staging is raw cleanup only. Removing a
  passthrough column and deleting the doc's prescription of a pre-filter that no model
  implements both move toward that rule, never away from it.

  DEPLOY ORDER on the shared warehouse. Staging is `view`, so the models are re-created, not
  migrated — there is no window in which a downstream model reads a dropped column, because
  no downstream model reads it. The nightly (`data:nightly`) is unreachable today: no GitLab
  schedule exists (creating one is #33 item 7, Wave 2), so there is no 04:00 run to sequence
  around. `data:build:main` rebuilds the full prod warehouse on merge to main, which
  re-creates all 9 views with the new column list in one build.

decisions_taken: >
  AUTHORITY FOR EVERY ITEM BELOW. The durable record is
  `.claude/task/escalations.log`, entry "2026-08-08 — GitLab #33: the CPO approves the whole
  pipeline cost/scalability plan, in advance" — appended in this branch, and appended BECAUSE
  `scope-auditor` FAILed round 1 for its absence and was right. This contract is overwritten by
  the next task, so quoting a ruling here is not recording it (the CPO's own rule, escalations.log
  2026-07-31 and 2026-08-01). That entry also names the §10-class items the approval covers
  individually, and states its own limit: it approves a PLAN, not whatever a builder later decides
  an item means. Quoted from the CPO's instruction of 2026-08-08:
  "Every item in #33's Gate 0, Wave 1, Wave 2 and Wave 3 is APPROVED, including the two that
  would normally be CPO-class: raw merge-on-write with the raw_archive backup first (item 8),
  and staging materialised as a table (item 9). The CPO said 'yes' to all three headline
  decisions on 2026-08-08 and then approved the full recommendation set." That instruction
  also supplies the §1 Confirm for this task: "Work through the plan without checking in on
  anything #33 already settles."

  THRESHOLD DECLARATIONS (no gate parses this field; an omission is a defect, not an
  oversight).
  - DEPENDENCY CHANGE: this REMOVES `metaplane/dbt_expectations` and, transitively,
    `godatadriven/dbt_date` from `dbt_project/packages.yml` and `package-lock.yml`. It adds
    no dependency. `packages.yml` matches no routing row, so `cto-reviewer` is not required
    on this diff and would only see this if declared here. Authority: #33 item 6, approved
    as above. Evidence of zero use is in the impact_map.
  - MECHANISM REMOVED, not added: two macros are deleted. Nothing new is introduced — no UDF,
    no lifecycle hook, no library, no workflow step (cf. Appendix A3).
  - RECURRING COST: unchanged by this MR, in either direction. Item 5's saving is not
    realised until staging becomes a table (Wave 2 item 9); today BigQuery prunes the unused
    view output column, so this is a prerequisite, not a saving. No schedule, cadence, API
    budget or history depth is touched.
  - ONE-OFF COST, disclosed: this MR modifies 9 staging models, so `data:build:mr` selects
    `state:modified+` = the 78-model closure above plus the full singular DQ suite. That is
    the most expensive shape an MR build takes. It is also the point — it is the executable
    proof that no consumer of `source_json` existed.

  SCOPE JUDGEMENTS I made rather than escalated (all below §10; stated so a reviewer can
  attack them):
  - `.github/workflows/pages-match-preview.yml:21` lists a deleted macro in a `paths:`
    filter. NOT edited. `CLAUDE.md` and `.github/workflows/README.md` both say that tree is a
    deliberately frozen pre-migration snapshot that runs nothing; a path filter naming a file
    that no longer exists is inert. Editing it to "keep it in sync" is the exact thing
    `CLAUDE.md` forbids.
  - `docs/product_direction_threads.md:12` names `apif_latest_source_partition` under
    "Thread 1 — Cost at scale (CLOSED 2026-05-25)". NOT edited. It is a dated record that PR
    #222 added the macro, which remains true. #33 lists the `data_contract.md` lines because
    that document is PRESCRIPTIVE and a reader would restore the behaviour from it; a closed
    thread log is not prescriptive.
  - `data_contract.md:61` introduces the SQL block being deleted, so deleting the block alone
    would leave a dangling sentence. That sentence is rewritten to describe what the 15
    staging models actually do, verified by reading all of them: 6 apply
    `qualify row_number() over (partition by league_code order by ingested_at desc) = 1`
    (fixtures_next, leagues, squads, standings, teams, transfers) and NONE applies the
    7-day `where DATE(ingested_at) >= ...` pre-filter the doc prescribes. Editorial
    correction of a statement that is false; not a design change.

  A CORRECTION TO #33, on evidence, per the CPO's instruction to say so plainly. #33 says the
  memory file "records the fix as still needed". It does not: it carries a
  "RESOLVED — PR #668 (MERGED 2026-07-08)" section. What is stale is its `description:`
  frontmatter and its "How to apply:" line, which still assert the shared-dataset hazard as
  live and are what a recall surfaces first. Those two are corrected; the body's history is
  left intact. (That file lives outside the repo, so it is not in `scope_paths` and does not
  appear in this diff.)

decisions_reserved:
  - The fate of `stg_apif__lineups`, `stg_apif__squads` and `stg_apif__player_teams` — zero
    `ref()` anywhere, 12 tests between them (#33 "Later, still open", item 17). Deleting a
    model is permanent and is a §10 call. NOT decided here: `stg_apif__lineups` keeps its
    place in this diff and only loses the unused column, exactly like the other 8.
  - Whether `data_contract.md` should positively PRESCRIBE a cheap latest-snapshot read shape
    now that the 7-day pre-filter is deleted. This MR only removes a false statement. What
    the correct prescribed shape is depends on Wave 2 items 8 and 9 (merge-on-write makes the
    question different), so writing one now would be inventing a rule ahead of its evidence.

done_when:
  - `grep -rn "source_json"` over the repo (excluding node_modules and dbt_packages) returns
    no hits at all.
  - `dbt deps` succeeds and installs only `dbt_utils`, and `dbt_packages/` afterwards contains
    only `dbt_utils` — so the two removed packages are physically gone, not merely undeclared.
  - `dbt compile --exclude resource_type:test` exits 0 over all 94 models.
    **`dbt parse` is NOT the check here and must not be substituted for it.** Measured on this
    branch: with a deliberate `{{ dbt_expectations.type_column_list('x') }}` probe inserted into
    `stg_apif__lineups.sql`, `dbt parse` exited **0** — it does not render model bodies — while
    `dbt compile` exited **2** with "'dbt_expectations' is undefined". The probe was then
    reverted. A green `parse` would have proved nothing about the package removal; `compile` is
    what makes the claim falsifiable.
    (Full `dbt compile` including tests fails locally for an unrelated reason: the singular test
    `assert_metric_catalogue_expr_resolvable` is introspective and queries the dev dataset, which
    is now `dev_scratch` and does not exist after Gate 0.1. That is Gate 0.1 working as intended —
    before it, the same introspective test silently queried prod's `dbt_analytics`. CI is
    unaffected: it runs `--target ci`/`--target prod`, whose datasets exist.)
  - `dbt ls --resource-type model --select <the 9 models>+` still resolves 78 models — no
    broken `ref()` introduced by the deletions. Count it with `wc -l`, never by reading the list.
  - `python -m sqlfluff lint <the 9 changed models> --templater jinja --dialect bigquery`
    from the REPO ROOT reports nothing that is not also present on `main` for the same files.
  - `python scripts/check_layer_contract.py` and `python scripts/check_registry_var_sync.py`
    both exit 0 (exit code read directly, not inferred from output).
  - `python -m pytest tests/ -q` exit code read directly; green.
  - CI `validate:governance` and `data:build:mr` green on the MR. The `state:modified+` build
    over the 78-model closure plus the full singular DQ suite is the executable proof of the
    impact_map's "blast radius: none".

amendments: (none)
