# Task contract — `board_leader_order`: the last ordering rule leaves the frontend

objective: >
  Add one served column to `mart_leaderboards` so a consumer showing a board of league leaders can
  order it with `ORDER BY <one column>` and encode no rule of its own. This finishes what MR A
  (`!164`) started: A moved the WITHIN-league pick into the warehouse (`league_leader_order`); the
  ACROSS-league row order stayed in the export as a three-key ORDER BY, and
  `analytics-engineer-reviewer` FAILed #40 MR B for it — correctly, because the CPO's rule is
  unconditional. This is MR C of three.
refs: >
  `.claude/task/escalations.log`, 2026-09-09 — RULING 1: *"All ranking and ordering lives in the
  warehouse. The page renders the order it is served."* and RULING 2, the fewer-minutes tie-break.
  `dbt_project/docs/layering.md` §Consumption layer, which MR A rewrote to state Ruling 1 without
  exception. GitLab #40 (the consumer), #112 (the meaningless last-resort key, MINOR).
  MR A merged as `943c9f2`; #40 MR B is parked in stash `TEMP-40-mrB-await-C`.

scope_paths:
  - dbt_project/models/5_marts/shared/mart_leaderboards.sql
  - dbt_project/models/5_marts/shared/shared.yml
  - dbt_project/tests/assert_mart_leaderboards_board_leader_order_is_total.sql
  - .claude/task/contract.md
  - .claude/task/review.md
  - .claude/task/review_input.patch
  - .claude/task/acceptance_evidence.md
  - .claude/task/escalations.log
  - .claude/active_work.md

impact_map: >
  writers: `mart_leaderboards` is written only by the dbt build — `data:build:main` /
    `fdp-nightly`, and per-MR `data:build:mr`. No ingestion path touches it. It is
    `materialized='view'`, so writing it is a view redefinition, not a table rebuild.

  downstream: LEAF, re-run against THIS checkout (post-A), not carried over from MR A:
    (`.venv/Scripts/dbt.exe ls --select mart_leaderboards+`, dbt 1.7.19 / bigquery 1.7.2,
    DBT_PROFILES_DIR pointed at a scratchpad profile carrying only a `dev`/`dev_scratch` target —
    `~/.dbt/profiles.yml` holds ANOTHER project's profile and was not touched):
      `--resource-type model` -> football_data_pipeline.5_marts.shared.mart_leaderboards (itself, only)
      `--resource-type all`   -> 29 nodes = the model + 28 tests, ZERO downstream models
    29 and not A's 27 because A added two tests. The only non-dbt consumer is
    `scripts/export_site_data.py`, which SELECTs named columns; adding a column cannot break it.

  layer_rules: `check_layer_contract.py` applies (`dbt_project/models/**` is in scope). No
    per-competition subdirectory, no per-model `+materialized` override introduced. The column is
    computed in the MART, which is the point of the change — it moves the last ordering rule INTO
    the layer the contract names.

  deploy_order: this must merge and `data:build:main` must run before #40 MR B can re-export
    `landing.json`, exactly as A did. Cheap and already demonstrated on A: the model is a VIEW, so
    the column exists as soon as the view is recreated — no table rebuild, no `--full-refresh`, and
    none of the three incremental facts is touched. A's cycle took 9m49s end to end.

  blast_radius: NO existing column changes and NO number moves. `rank` (DENSE_RANK, ties share) and
    `league_leader_order` (A's within-league pick) are both untouched. One column is ADDED, NULL on
    every row that is not a league leader.
    ⚠ VERIFIED AGAINST PROD BEFORE BUILDING: the new ordinal reproduces the order #40 MR B already
    renders, exactly. Running the window over prod and filtering to the elite pool gives
    goals PD,SA,LP,L1,ED,BL1,PL / assists PD,SA,ED,PL,LP,L1,BL1 / passes LP,ED,PL,PD,SA,L1,BL1 /
    key passes PD,ED,SA,LP,L1,PL,BL1 — identical to the committed `landing.json`. So MR B's payload
    does not change when it switches to this column; only the code does.
    ⚠ `mart_team_leaderboards` has the same shape and the same latent gap. NOT fixed here — Top
    teams (#41) is unbuilt, and widening this MR would put an unreviewed change in a model nothing
    consumes. Flagged, not folded in.

decisions_taken: >
  ⛔ THIS MR EXISTS BECAUSE I WAS WRONG, AND THE ERROR IS RECORDED RATHER THAN QUIETLY FIXED. Both
  MR A's contract and #40 MR B's said the cross-league order COULD NOT live in the mart, because the
  order is pool-scoped and the pool (`competition_group = 'elite'`, rotating nightly under #101) is
  not a concept `mart_leaderboards` knows. That reasoning is false. The ruled order — value, then
  fewer minutes, then `player_sk` — is a TOTAL order, and restricting a total order to any subset
  preserves the relative order of what remains. So the mart can rank every league leader on a board
  globally, and a consumer filtering to any pool inherits the correct order for free. The pool never
  enters into it. `decisions_reserved` in both earlier contracts should be read with that
  correction, and MR B's is amended when it rebases.

  RULING 1 IS WHAT THIS IMPLEMENTS, and it is unconditional: *"All ranking and ordering lives in the
  warehouse. The page renders the order it is served."* After this, #40 MR B's query carries
  `order by l.board_leader_order` — one served column — and no comparison of its own.

  THE ORDINAL IS SEASON-AGNOSTIC AND GLOBAL, DELIBERATELY. It partitions by `metric_key` alone, over
  every league leader on that board. It does NOT partition by season, because `is_current_season` is
  per-league and different leagues sit in different `season_api_year` values, so partitioning by
  season would split leagues that a consumer shows side by side. The consequence is visible and
  intended: filtered to seven leagues the numbers come out SPARSE (17, 18, 21, 31, 36, 40, 41 on the
  assists board), because they are positions in a global order. Sparse is the tell that it is global;
  contiguity is not a property any consumer needs, and manufacturing it would require knowing the
  pool, which is the mistake this MR corrects.

  NULL ON NON-LEADERS, not a number. The ordinal is only defined among league leaders, so every
  other row carries NULL rather than a position in a sequence it is not part of. A number there
  would be meaningless and would invite a consumer to order by it.

  THRESHOLD — NEW MECHANISM: none. A second `row_number()` beside two existing window functions in a
  model that already ranks. No new model, macro, seed, dependency, job or gate.

  THRESHOLD — RECURRING COST: negligible, stated rather than assumed. The model is a VIEW, so
  nothing is stored. The added cost is ONE window function over the same scan when a consumer
  queries it, plus one singular test per build.
  ⚠ This sentence said "one window function and one SELF-JOIN" and that was wrong — it described the
  first implementation, which ranked the leaders in their own CTE and joined back. That form was
  abandoned (SQLFluff forbids `USING` via ST07 and demands forty qualified references without it),
  and the shipped version has no join at all. Corrected after `scope-auditor` caught the leftover in
  round 1; it overstated the cost rather than hiding it, but a contract that misdescribes its own
  change is wrong either way.
  Scale reference: the export's whole Home query over this view is 29.8 MB by dry run, against
  ~129 GB/day for the two scheduled jobs.

decisions_reserved:
  - The last-resort tie-break itself. `player_sk` is stable and meaningless; GitLab #112 is filed at
    MINOR priority. This MR inherits that key rather than choosing it, and nothing here depends on
    the answer.
  - Whether `mart_team_leaderboards` gets the same pair of columns, and when. Same latent gap, no
    consumer yet.
  - Whether `site_v2/src/lib/competitionOrder.mjs` is rewritten or deleted. It is a violation under
    Ruling 1; which one depends on what the competitions index should order by. Filed, not decided.

done_when:
  - `dbt parse` clean, and SQLFluff passes from the REPO ROOT with the full rule set on both changed
    files (exit code read BARE and unredirected — it exits 1 on success when stdout is redirected).
  - `check_layer_contract.py` and `check_description_hygiene.py` exit 0. The new column carries a
    description and `persist_docs` is on, so BigQuery's 1,024-character column limit applies and a
    breach fails the prod build.
  - The new singular test is MUTATION-TESTED and watched RED, not merely green: dropping the
    `minutes` leg from the ordinal's ORDER BY must make it fail, and the evidence must show the row
    count it returns.
  - Measured against prod: the ordinal is unique within a board, NULL on every non-leader, and
    filtering it to the elite pool reproduces the exact league order #40 MR B already renders.

amendments: (none)
