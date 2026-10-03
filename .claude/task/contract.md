# Task contract — the metric layer's rules, each stated once and shown in BigQuery

objective: >
  How step 1 of the issue "Metric layer: every rule in one place, plain descriptions, a map an AI
  can read" (#190). The rules for computing metrics (R1 to R7), for cleaning the provider's values,
  for who enters a ranking and for what each window holds are each written once, in a dbt doc
  block shown as the description of the table that carries them in BigQuery. The description
  standard is written once, in engineering_standards.md section 2, citing ISO/IEC 11179-4 and the
  ASD-STE100 writing rules. docs/metric_layer.md becomes an index of pointers. Every other place
  that restates one of these rules (yml, doc blocks, model and test headers, the sentence the docs
  script appends to every team rate, the documents the CPO named) changes to a pointer or goes.
  No model's logic changes.

refs: >
  #190, approved by the CPO in chat on 2026-10-03 ("yes"), and its two standards lines ("yes",
  the same day). Inventory of where each rule lives: an independent agent's read-only sweep, in
  #190's exploration detail. Research: #190's exploration detail and its sources.

acceptance_criteria:
  # The issue's checklist lines this MR delivers, verbatim.
  - "Each question has one place that answers it, readable in BigQuery; every other place points there (the table in #190: the catalogue, the rules R1 to R7 in one doc block, each model method on its model, the ranking block, the cleaning block, the window_type block, metrics_context_model.md section 4, engineering_standards.md section 2, docs/metric_layer.md as pointers only)."
  - "The rules, stated once: R1 to R7 as #190 states them."
  - "Descriptions follow ISO/IEC 11179-4 (a definition states what the thing is, stands alone, and leaves out rationale and procedure) and the writing rules of ASD-STE100 (one word, one meaning; short sentences; active voice); `engineering_standards.md` section 2 cites both."
  - "No other place restates a rule above: each place listed below the fold changes to a pointer or goes, including the sentence the docs script appends to every team rate (\"NULL unless every input of its formula is present…\")."
  - "Every model's compiled SQL equals `main`'s apart from comments; where it does not, its values equal prod's on matches before a cutoff, at a relative 1e-9."
  - "Documents the CPO owns change as pointers only: `CLAUDE.md` and `north_star.md` (the window line), `metrics_display.md` (locked: its restated finishing formula and null clamp, lines 249-253)."
  - "#185's How step 5 hands `docs/metric_layer.md`, `engineering_standards.md` sections 2 and 3 and `seeds/schema.yml` to this issue; #94's id pattern goes into the catalogue's doc block."

scope_paths:
  - dbt_project/models/docs/metric_rules.md
  - dbt_project/models/docs/cleaning_rules.md
  - dbt_project/models/docs/shared_columns.md
  - dbt_project/models/docs/metric_columns.md
  - dbt_project/seeds/schema.yml
  - dbt_project/docs/engineering_standards.md
  - docs/metric_layer.md
  - docs/metrics_context_model.md
  - docs/north_star.md
  - CLAUDE.md
  - docs/wireframes/metrics_display.md
  - scripts/sync_metric_docs_blocks.py
  - tests/test_sync_metric_docs_blocks.py
  - dbt_project/models/2_base/api_football/base.yml
  - dbt_project/models/2_base/api_football/base_apif__fixture_players.sql
  - dbt_project/models/2_base/api_football/base_apif__fixture_statistics.sql
  - dbt_project/models/3_core/core.yml
  - dbt_project/models/4_intermediate/shared/int_legs.yml
  - dbt_project/models/4_intermediate/shared/int_legs__team_match.sql
  - dbt_project/models/4_intermediate/shared/int_momentum.yml
  - dbt_project/models/4_intermediate/shared/int_momentum_window.yml
  - dbt_project/models/4_intermediate/shared/int_season_record.yml
  - dbt_project/models/4_intermediate/shared/int_player_club_season.yml
  - dbt_project/models/4_intermediate/shared/int_player_profile.yml
  - dbt_project/models/4_intermediate/shared/int_player_season_position.yml
  - dbt_project/models/4_intermediate/shared/int_team_profile.yml
  - dbt_project/models/4_intermediate/shared/int_competition_benchmarks.yml
  - dbt_project/models/4_intermediate/domestic_league/team_season/int_team_season.yml
  - dbt_project/models/4_intermediate/domestic_league/team_season/int_player_season__metrics.sql
  - dbt_project/models/4_intermediate/domestic_league/team_season/int_team_season__metrics_cumulative.sql
  - dbt_project/models/4_intermediate/domestic_league/team_season/int_team_season__deserved_vs_actual.sql
  - dbt_project/models/4_intermediate/shared/int_player_club_season__metrics.sql
  - dbt_project/models/4_intermediate/shared/int_player_momentum__metrics.sql
  - dbt_project/models/4_intermediate/shared/int_player_profile__contribution.sql
  - dbt_project/models/4_intermediate/shared/int_player_season_position__metrics.sql
  - dbt_project/models/4_intermediate/shared/int_player_season_record.sql
  - dbt_project/models/4_intermediate/shared/int_team_momentum__metrics.sql
  - dbt_project/models/4_intermediate/shared/int_team_momentum_window.sql
  - dbt_project/models/4_intermediate/shared/int_team_season_record.sql
  - dbt_project/models/4_intermediate/shared/int_player_competition_benchmarks.sql
  - dbt_project/models/4_intermediate/shared/int_team_competition_benchmarks.sql
  - dbt_project/macros/player_benchmark_metrics.sql
  - dbt_project/models/5_marts/shared/shared.yml
  - dbt_project/models/5_marts/domestic_league/domestic_league.yml
  - dbt_project/models/5_marts/shared/mart_team_momentum.sql
  - dbt_project/models/5_marts/shared/mart_team_profile.sql
  - dbt_project/models/5_marts/shared/mart_leaderboards.sql
  - dbt_project/models/5_marts/shared/mart_team_leaderboards.sql
  - dbt_project/models/5_marts/shared/mart_player_competition_benchmarks.sql
  - dbt_project/models/5_marts/shared/mart_team_competition_benchmarks.sql
  - dbt_project/tests/assert_form_window_rates_inputs_covered.sql
  - dbt_project/tests/assert_season_rates_inputs_covered.sql
  - dbt_project/tests/assert_player_metrics_follow_catalogue_formula.sql
  - dbt_project/tests/assert_team_metrics_follow_catalogue_formula.sql
  - dbt_project/tests/assert_awarded_matches_do_not_null_team_stats.sql
  - dbt_project/tests/assert_base_player_stats_cleaned.sql
  - dbt_project/tests/assert_momentum_awarded_matches_do_not_null_team_stats.sql
  - dbt_project/models/4_intermediate/shared/int_team_profile__yoy.sql
  - dbt_project/models/4_intermediate/shared/int_player_profile__yoy.sql
  - .claude/task/contract.md
  - .claude/task/review.md
  - .claude/task/review_input.patch
  - .claude/task/acceptance_evidence.md
  - .claude/task/rendered_page_evidence.md
  - .claude/task/audit_reviewer_outputs.md
  - docs/tracker/**

impact_map: >
  Docs, doc blocks, descriptions and SQL comments only; no model's logic changes. Evidence owed in
  done_when: every model's compiled SQL with comments stripped equals main's, proven offline with
  no warehouse query: every changed SQL file equals main's with its comments stripped, and every
  changed yml equals main's with its descriptions removed. What changes in the
  warehouse: the BigQuery descriptions persisted from the yml and doc blocks (persist_docs on every
  model and seed): the catalogue table's description carries R1 to R7, the two cleaned base
  tables' descriptions carry the cleaning rules, the ranking and benchmark tables' descriptions
  carry the ranking rules, every window_type column carries one description, the 233 metric
  column descriptions that ended in the appended null sentence end without it, and the metric
  columns described by hand or renamed in a mart show their metric's block. No value, row,
  column, test result or export changes. Layer rules: none touched. Deploy: the post-merge build
  rewrites the descriptions; nothing else.

decisions_taken: >
  #190 as the CPO approved it in chat on 2026-10-03 ("yes"), the issue's table, rules R1 to R7 and
  the fold's list of places to change; and its two standards lines, approved the same day ("yes"):
  ISO/IEC 11179-4 and the ASD-STE100 writing rules cited in engineering_standards.md section 2.
  This MR is How step 1; the reviewer brief, the 89 descriptions with their check, lower_is_better
  and the map are later MRs.

  Readings, under the CPO's delegation in chat on 2026-10-02, "Readings of approved rules are
  yours; apply the most plausible one and state it in one line": a column's own null meaning that
  no general rule states (no estimate loaded, no standings, no earlier season on a column that is
  not a year-over-year metric, whose blank R6 states) stays in its description, one sentence, as
  engineering_standards.md 3.1 asks; a code comment that explains
  the line beside it stays, and a header that restates a whole rule set points to its block; the
  rules live in two doc-block files, metric_rules.md (the catalogue's rules, rankings, windows) and
  cleaning_rules.md (the cleaning). #94's id pattern enters the catalogue's doc block with #94's
  renames, as #94 states ("WITH THE RENAMES: the table above goes into the catalogue's doc
  block"): today the catalogue's ids do not follow it, so this MR makes the block and #94 fills it.
  docs/metric_layer.md keeps two rules beside its pointers: "A group is defined once", because the
  locked metrics_display.md links that heading, and #129's rule that provider facts and catalogue
  metrics never mix in one block, to which #190's table gives no other home. A metric column
  described by hand, or renamed in a mart, references its metric's block and adds one sentence for
  its side, season or window.

decisions_reserved:
  - Any change to a model's logic, a test's result or a value is out of scope; found defects are
    filed, never fixed here.
  - metrics_display.md is locked: only its lines 249-253 change, as #190 names them.

done_when:
  - dbt parse, the offline gates (including description hygiene and the docs-block check), ruff,
    pytest and sqlfluff with the dbt templater on every changed model pass.
  - Every model's compiled SQL, comments stripped, equals main's.
  - The review cycle passes with every routed reviewer, review.md bound to --staged-hash.
  - data:build:mr is green.

amendments:
  - 2026-10-03: + dbt_project/models/4_intermediate/shared/int_team_profile__yoy.sql and
    + dbt_project/models/4_intermediate/shared/int_player_profile__yoy.sql — authority: #190 as
    the CPO approved it in chat on 2026-10-03 ("yes"), whose list of places to change names "the
    headers of the metric ... models"; content: the copies of R4 and R6 in their headers point to
    the rules.
  - 2026-10-03, recorded with the one above: three earlier changes to this contract were written
    while the tree was not clean — + dbt_project/tests/assert_base_player_stats_cleaned.sql (its
    header named docs/metric_layer.md as the home of the cleaning rules), the impact_map's evidence
    method (offline, no warehouse query) and the #94 reading in decisions_taken — authority: the
    same approval and the CPO's delegation of readings in chat on 2026-10-02.
