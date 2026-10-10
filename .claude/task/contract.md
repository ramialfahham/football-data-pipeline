# Task contract — VL's split-season groups read as split rounds

objective: >
  The provider names VL 2026's split halves "Champion Group" and "Relegration Group". The
  standings_table_kinds seed reads them as groups, so assert_every_standings_section_has_a_table_kind
  fails the nightly. One seed row classifies them as split rounds.

refs: >
  The seed row's exact text: approved in chat, 2026-10-10.

scope_paths:
  - dbt_project/seeds/standings_table_kinds.csv
  - dbt_project/seeds/schema.yml
  - .claude/task/contract.md
  - .claude/task/review.md
  - .claude/task/review_input.patch
  - .claude/task/acceptance_evidence.md

impact_map: >
  writers: the seed is hand-authored; dbt seed loads it.
  downstream: `dbt ls --select standings_table_kinds+ --resource-type model` lists mart_standings,
  mart_fixture_standing_context and mart_matchday_insights; only mart_standings.sql reads
  table_kind. No export script reads table_kind; StandingsTable.astro drops only ranking sections.
  layer_rules: none change; no model file is touched.
  deploy_order: the seed loads at the next prod build after the merge; nothing breaks before it.
  blast_radius: measured on prod core.fct_standings, the new pattern matches two sections only,
  VL 2026 "Champion Group" and "Relegration Group" (6 teams each); their table_kind moves from
  group to split_round. No rendered page changes.

decisions_taken: >
  The seed row `15,champion group|relegr?ation group,split_round`: approved in chat, 2026-10-10.
  The seed description drops its stale row count and names the new section names among the
  split-season examples.

  THRESHOLD DECLARATIONS: NEW MECHANISM: none. RECURRING COST: none.

decisions_reserved:
  - Any other seed row, and any change to how a page renders a table kind.

done_when:
  - dbt parse passes; pytest tests/ passes.
  - The test's SQL run against prod with the five seed rows inline returns 0 rows.

amendments: (none)
