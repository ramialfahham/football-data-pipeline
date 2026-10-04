# Task contract — every catalogue description in plain words, held by a check; lower_is_better gone

objective: >
  How step 3 of the issue "Metric layer: every rule in one place, plain descriptions, a map an AI
  can read" (#190). All 89 descriptions in metric_catalogue.csv are rewritten to
  engineering_standards.md section 2: one plain sentence saying what the metric counts and per
  what, on cleaned data. scripts/sync_metric_docs_blocks.py fails the build on a description over
  200 characters, with a snake_case name or with a listed word, and regenerates the metric column
  blocks from the new texts. The legacy column lower_is_better goes: direction alone says which
  way is better, and the documents that name lower_is_better point to direction.

refs: >
  #190, approved by the CPO in chat on 2026-10-03 ("yes"). The CPO's instruction in chat on
  2026-10-02: "Rewrite every catalogue description yourself: what the metric means, on cleaned
  data, in plain words; no caveats, null conditions, display notes, history, provider trivia or
  jargon. I will not read 89 descriptions." #190 steps 1 and 2 are merged (!243, !245); the
  football reviewer judges this MR.

acceptance_criteria:
  # The issue's checklist lines this MR delivers, verbatim.
  - "Every catalogue description is one plain sentence, at most 200 characters, saying what the metric counts and per what, on cleaned data, with no null condition, caveat, display note, history, provider detail, snake_case name or jargon. A team metric and its player twin read alike where their formulas match. A check fails the build on a description over 200 characters, with a snake_case name or with a listed word."
  - "`lower_is_better` is gone; `direction` alone says which way is better."
  - "Documents the CPO owns change as pointers only: `CLAUDE.md` and `north_star.md` (the window line), `metrics_display.md` (locked: its restated finishing formula and null clamp, lines 249-253), three wireframe lines and one in `ui_design_brief.md` that name `lower_is_better`."

scope_paths:
  - dbt_project/seeds/metric_catalogue.csv
  - dbt_project/seeds/schema.yml
  - dbt_project/models/docs/metric_columns.md
  - scripts/sync_metric_docs_blocks.py
  - tests/test_sync_metric_docs_blocks.py
  - dbt_project/tests/assert_metric_direction_lower_is_better_agree.sql
  - dbt_project/tests/assert_metric_meaning_complete.sql
  - scripts/export_metric_definitions_json.py
  - docs/ui_design_brief.md
  - docs/wireframes/00_overview.md
  - docs/wireframes/01_fixture_page.md
  - docs/wireframes/02_team_profile.md
  - .claude/task/contract.md
  - .claude/task/review.md
  - .claude/task/review_input.patch
  - .claude/task/acceptance_evidence.md
  - .claude/task/rendered_page_evidence.md
  - .claude/task/audit_reviewer_outputs.md
  - docs/tracker/**

impact_map: >
  `dbt ls --select metric_catalogue+`: mart_team_leaderboards (it reads direction for rank_order)
  and the catalogue's tests (accepted_values on base_relation, computation_kind, direction,
  entity, format, importance_tier and metric_group; assert_metric_catalogue_expr_resolvable,
  assert_metric_catalogue_unique_by_entity, assert_metric_meaning_complete,
  assert_metric_direction_lower_is_better_agree, the formula and coverage tests). No model selects
  lower_is_better or description; the one test that reads lower_is_better goes with it. What
  changes in the warehouse: the seed table loses its lower_is_better column, and the description
  of the seed's rows and of every metric column that shows a generated block (persist_docs)
  becomes the new text. Consumption: scripts/export_metric_definitions_json.py, which feeds the
  retired legacy site, reads lower_is_better today and derives it from direction instead, so its
  output is unchanged; site_v2 reads direction only. No value, row, model SQL or export output
  changes. Layer rules: none touched.

decisions_taken: >
  #190 as the CPO approved it on 2026-10-03, its description standard (engineering_standards.md
  section 2, merged in !243) and its check; the CPO's instruction of 2026-10-02 to rewrite every
  description without reading them. Readings, under the CPO's delegation in chat on 2026-10-02
  ("Readings of approved rules are yours; apply the most plausible one and state it in one
  line"): the listed words are matched as whole words, any case; the export derives
  lower_is_better from direction (true exactly when direction is lower_better, which the removed
  lockstep test held) so the frozen legacy site's input does not change.

decisions_reserved:
  - Names, labels, order, direction values and format stay with #177; what a high or low value
    means (interpretation) stays with #187; metric ids and their pattern stay with #94.
  - No model's logic changes.

done_when:
  - dbt parse, the offline gates (including description hygiene and the docs-block check), ruff,
    pytest pass.
  - The review cycle passes with every routed reviewer, the football reviewer among them,
    review.md bound to --staged-hash.
  - data:build:mr is green.

notes_for_owning_issues: >
  The football reviewer's notes on columns this MR does not change, recorded here as #190 asks.
  #177: the label "Open-play goals" and the interpretation of goals_open_play (team and player),
  and of finishing_efficiency_pct, say open play while the formula is goals minus penalties and own
  goals, set pieces included; the team goals_own label "Own goals" reads as the team's own goals;
  labels say "shots on goal" where descriptions say "shots on target"; finishing efficiency keeps
  penalty shots in its denominator while its numerator leaves penalty goals out. #184: the player
  saves_player_pct and shots_on_goal_against_player keep own goals in the goals conceded.

amendments:
  - 2026-10-03: notes_for_owning_issues added — authority: #190, "A defect it sees in a column the
    diff does not change (a label, an interpretation) is a note for #177 or #187, recorded in the
    contract, not a FAIL"; content: the football reviewer's round-1 notes.
