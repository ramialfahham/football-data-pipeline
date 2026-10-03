# Acceptance evidence — #190 How step 1, the metric layer's rules stated once

Read from `dbt_project/target/manifest.json` after `dbt parse` (the descriptions as dbt renders
them and persist_docs writes them to BigQuery), from the files on disk, from the two GitLab issues,
and from exit codes read bare. No warehouse query was run.

criteria_demonstrated:
  - ONE PLACE PER QUESTION, READABLE IN BIGQUERY. The manifest renders the `metric_catalogue` block
    as the seed metric_catalogue's description (2,087 characters, lines R1 to R7); the
    `cleaning_rules` block on base_apif__fixture_players and base_apif__fixture_statistics; the
    `ranking_rules` block on mart_leaderboards, mart_team_leaderboards,
    mart_player_competition_benchmarks, mart_team_competition_benchmarks,
    int_player_competition_benchmarks, int_team_competition_benchmarks and
    int_team_competition_benchmark_metrics_long; every one of the 10 `window_type` columns carries
    one of the two window blocks (6 the form block, 4 the season-record block), and the form block
    is also int_team_momentum_window's description of its selection. `docs/metric_layer.md` is 55
    lines: the pointer table, plus the two rules the contract keeps there.
  - R1 TO R7 AS #190 STATES THEM. A script compares each rendered R line of the catalogue
    description with the same line of `glab issue view 190`, whitespace and backticks ignored:
    R1 True, R2 True, R3 True, R4 True, R5 True, R6 True, R7 True.
  - THE STANDARD IS CITED. `engineering_standards.md` section 2, "A metric's description", cites
    ISO/IEC 11179-4 (states what the thing is, stands alone, no rationale or procedure) and
    ASD-STE100 (one word with one meaning, short sentences, active voice), each with its link, and
    lists a window among what a description leaves out.
  - NO OTHER PLACE RESTATES A RULE. "NULL unless every input" is carried by 59 blocks of `main`'s
    metric_columns.md and by 0 now; 0 of the 1,941 rendered model-column descriptions carry it, and
    `metric_columns.md` holds "NULL" 104 times on main and 0 times now. The 51 metric columns
    described by hand or renamed in a mart (the year-over-year columns of int_team_profile__yoy
    and mart_team_profile, the home and away form columns of mart_matchday_insights, the three
    `points` columns, `goals_total` and `goals_assists`) show their metric's block; a script over
    every yml finds no hand-described metric column left beyond per-match facts, the provider's
    table and competition tallies. The listed ymls and the model, macro and test headers point to
    the blocks (`git grep "rule R[1-7]"`).
  - COMPILED SQL UNCHANGED. A script compares every changed file under dbt_project with main's:
    27 SQL files equal main's with comments stripped, 15 ymls equal main's with their descriptions
    removed, 5 files are doc blocks or docs; result "differ beyond comments/descriptions: none".
    No model reads a description at compile time, and dbt_project.yml carries no run hook.
  - THE CPO'S DOCUMENTS CHANGE AS POINTERS ONLY. `git diff main` on CLAUDE.md: 2 lines, the metric
    layer row's label and the form-window bullet ("which matches a window holds is
    docs/metrics_context_model.md section 4"); north_star.md: 1 line, the window sentence becomes
    that pointer; metrics_display.md: lines 249-253 only, the restated finishing formula and null
    clamp become one pointer to the catalogue row and the catalogue table's rules.
  - #185 HANDS THE DOCUMENTS OVER; THE BLOCK #94 FILLS EXISTS. #185 How step 5 reads
    "`docs/metric_layer.md`, `engineering_standards.md` §2 and §3 and
    `dbt_project/seeds/schema.yml` are #190's", and this MR edits all four. The catalogue's doc
    block exists (`metric_catalogue` in `dbt_project/models/docs/metric_rules.md`); #94 states its
    id table goes there "WITH THE RENAMES", so it enters with them (the contract's reading).
  - CHECKS. `dbt parse` 0; check_layer_contract, check_registry_var_sync,
    check_competition_type_seed, check_ui_i18n_metrics, check_copy_gate, check_description_hygiene
    0; `sync_metric_docs_blocks.py --check` 0; `generate_metric_sql.py --check` 0; ruff with
    `.ruff-ci.toml` "All checks passed!"; pytest "1350 passed, 2 skipped"; sqlfluff with the dbt
    templater on the 21 changed models, exit 0.
