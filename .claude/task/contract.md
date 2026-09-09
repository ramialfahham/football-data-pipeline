# Task contract — the three served columns the Top teams block needs

objective: >
  Give `mart_team_leaderboards` the three columns the Home Top teams block requires, so the export
  filters and orders on served columns and computes nothing. The player mart got these one at a time
  across two MRs because each was discovered late; here all three are known up front and go in
  together. This is the warehouse half of Top teams — the block itself follows in its own MR.
refs: >
  `.claude/task/escalations.log` — 2026-09-09 Ruling 1: *"All ranking and ordering lives in the
  warehouse. The page renders the order it is served."* And the team tie-break ruling of the same
  day, recorded in this branch.
  `docs/wireframes/10_home.md` §0 — the composition: next matches, Top players, Top teams.
  `dbt_project/docs/layering.md` §Consumption layer. `!164` and `!165` are the player-side
  precedent, both merged. GitLab #114 (a real team tie-break, LOW). #40 MR B (`!166`) is the Top
  players block, open and green; this branch does not depend on it and it does not depend on this.

scope_paths:
  - dbt_project/models/5_marts/shared/mart_team_leaderboards.sql
  - dbt_project/models/5_marts/shared/shared.yml
  - dbt_project/tests/assert_mart_team_leaderboards_one_leader_per_league.sql
  - .claude/task/contract.md
  - .claude/task/review.md
  - .claude/task/review_input.patch
  - .claude/task/acceptance_evidence.md
  - .claude/task/escalations.log
  - .claude/active_work.md

impact_map: >
  writers: `mart_team_leaderboards` is written only by the dbt build — `data:build:main` /
    `fdp-nightly`, and per-MR `data:build:mr`. No ingestion path touches it. It is
    `materialized='view'`, so writing it is a view redefinition, not a table rebuild.

  downstream: LEAF, run against this checkout
    (`.venv/Scripts/dbt.exe ls --select mart_team_leaderboards+`, dbt 1.7.19 / bigquery 1.7.2,
    DBT_PROFILES_DIR on a scratchpad profile with only a `dev`/`dev_scratch` target —
    `~/.dbt/profiles.yml` holds ANOTHER project's profile and was not touched):
      `--resource-type model` -> football_data_pipeline.5_marts.shared.mart_team_leaderboards (itself, only)
      `--resource-type all`   -> 22 nodes = the model + 21 tests, ZERO downstream models
    NO consumer exists yet: `scripts/export_site_data.py` does not read this mart at all today, so
    nothing can break. That is the safest possible moment to add columns to it.

  layer_rules: `check_layer_contract.py` applies (`dbt_project/models/**` in scope). No
    per-competition subdirectory, no per-model `+materialized` override introduced.

  deploy_order: must merge and `data:build:main` must run before the Top teams block can query the
    columns, exactly as `!164` and `!165` did. Cheap and twice demonstrated: the model is a VIEW, so
    the columns exist as soon as the view is recreated — no table rebuild, no `--full-refresh`, no
    incremental fact touched.

  blast_radius: NO existing column changes and NO number moves. `rank` keeps its DENSE_RANK
    definition. Three columns are ADDED. Nothing reads this mart yet, so the blast radius outside
    the model itself is empty.

decisions_taken: >
  ⛔ THE MART IS MISSING ALL THREE, MEASURED NOT ASSUMED. `mart_team_leaderboards` has 13 columns
  (`INFORMATION_SCHEMA.COLUMNS`, prod). It has no `is_current_season`, no `league_leader_order` and
  no `board_leader_order`. Without them the export would have to pick a season and compute an order
  itself — the two defects that between them cost the player block four failed review rounds.

  RULING 1 IS WHAT THIS IMPLEMENTS. Ordering lives here, so the block orders by one served column.

  ⭐ THE TEAM TIE-BREAK HAS NO SPORTING CRITERION, AND THAT IS THE CPO's RULING OF 2026-09-09, NOT
  MY INFERENCE. The player rule — fewer minutes played — does NOT transfer, because teams have no
  minutes. I proposed `season_games_played` as the analogue and he rejected it: *"will not work most
  of the time"*. He is right on two counts, and the second is the real one:
    · It barely discriminates. Measured over 235 league-seasons: 3.6 distinct game counts per
      league-season on average, and in 72 of them every team has played exactly the same number.
    · It asserts the wrong thing. For a RATE, fewer games is not better, it is LESS EVIDENCE for the
      same rate. Fewer minutes for an equal goal tally is efficiency; fewer games for an equal
      goals-per-match is a smaller sample.
  So there is no criterion. The order falls straight to `team_sk`, which is stable and MEANINGLESS
  and is labelled as such in the model, exactly as `player_sk` is on the player side. His words on
  the disposition: *"yes, let's a separate issue to build something smarter at some later point"* —
  filed as **#114**. Scale: 2 of 259 league-board-seasons currently tie.

  THRESHOLD — NEW MECHANISM: none. Two `row_number()` windows and one `rank()` beside the existing
  `dense_rank()`, in a model that already ranks, mirroring `mart_leaderboards` exactly. No new
  model, macro, seed, dependency, job or gate.

  THRESHOLD — RECURRING COST: negligible. The model is a VIEW, so nothing is stored; the added cost
  is three window functions over the same scan when a consumer queries it, plus one singular test
  per build. Nothing queries it yet at all.

decisions_reserved:
  - A real tie-break for equal per-match rates — #114, LOW, explicitly deferred by the CPO.
  - Whether the Top teams rows link to team pages. The block MR settles it; my call there is
    unlinked, because `[lang]/teams/[team].astro` builds one page per committed
    `src/data/teams/*.json` and only one team is committed, so links would fail `audit-seo` check 8.
    Not this MR's to answer and not answered here.

done_when:
  - `dbt parse` clean, and SQLFluff from the REPO ROOT with the full rule set on both changed files,
    exit code read BARE and unredirected.
  - ⭐ THE COMPILED MODEL IS DRY-RUN AGAINST PROD BEFORE PUSHING. `dbt compile --select
    mart_team_leaderboards`, rewrite the dev dataset identifiers to the prod ones, pipe to
    `bq query --dry_run`. This is the check that was MISSING on `!165`, where a trailing comma
    reached CI because `dbt parse` does not compile SQL and SQLFluff cannot see past this file's
    `dbt_utils` line. A dry run bills zero and validates syntax and every column reference.
  - `check_layer_contract.py` and `check_description_hygiene.py` exit 0.
  - The new singular test is MUTATION-TESTED and watched RED, with the row count it returns.
  - Measured against prod: exactly one row per (league_code, season_api_year, metric_key) carries
    `league_leader_order = 1`; `board_leader_order` is unique within a board and NULL on every
    non-leader; `is_current_season` is true on exactly one season per league.

amendments: (none)
