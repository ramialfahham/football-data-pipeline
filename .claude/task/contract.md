# Task contract — teams level on points stand in their league's tie-break order

objective: >
  The league table serves each team's place in its league's own tie-break order wherever our
  table equals the provider's, instead of the provider's order of teams level on points. The
  Table page, the Team page and the match page read the same place. A dbt test holds the served
  place to the rule's place.

refs: >
  #237 (the issue text, approved in chat, 2026-10-31; the plan, approved in chat, 2026-10-31).

scope_paths:
  - dbt_project/models/4_intermediate/domestic_league/team_season/int_team_season__table_by_time.sql
  - dbt_project/models/4_intermediate/domestic_league/team_season/int_team_season__standings_primary.sql
  - dbt_project/models/4_intermediate/domestic_league/team_season/int_team_season.yml
  - dbt_project/models/4_intermediate/shared/int_standings__official_rank.sql
  - dbt_project/models/4_intermediate/shared/int_standings__official_rank.yml
  - dbt_project/models/5_marts/shared/mart_standings.sql
  - dbt_project/models/5_marts/shared/mart_next_matchday.sql
  - dbt_project/tests/assert_standings_rank_follows_league_rule.sql
  - dbt_project/tests/assert_one_match_that_matters_per_competition.sql
  - dbt_project/models/5_marts/shared/shared.yml
  - dbt_project/models/docs/metric_rules.md
  - dbt_project/docs/layering.md
  - docs/metric_layer.md
  - .claude/task/contract.md
  - .claude/task/review.md
  - .claude/task/review_input.patch
  - .claude/task/acceptance_evidence.md

impact_map: >
  `int_team_season__table_by_time` gains `place_by_rules`; its existing readers
  (`int_team_profile__yoy`, the published-tables test) read named columns and are unchanged.
  The new `int_standings__official_rank` reads `fct_standings` and `int_team_season__table_by_time`.
  Three readers switch to it from `fct_standings`: `mart_standings`, `mart_next_matchday` and
  `int_team_season__standings_primary`. The test `assert_one_match_that_matters_per_competition`
  recomputes `mart_next_matchday`'s flag from the table positions and switches with it.
  `dbt ls --select int_standings__official_rank+ --resource-type model` lists 14 models: the new
  one, the three readers and the ten below. Downstream:
  `mart_team_competitions`, `mart_fixture_standing_context` and `mart_matchday_insights` (through
  `mart_standings`); `mart_competition_fixtures`, `mart_competition_index` and `mart_match_days`
  (through `mart_next_matchday`); `mart_team_season`, `int_team_season__deserved_vs_actual`,
  `mart_team_profile` and `mart_team_season_insights` (through `int_team_season__standings_primary`).
  `int_team_season__table_state` keeps reading `fct_standings` for `previous_position`.
  blast_radius: the place of teams level on points changes where the provider's order differs
  from the league's rule and our table equals the provider's; every other value is unchanged.
  Cost: about 60 MB a night more, approved in chat, 2026-10-31.

acceptance_criteria:
  - "On the Table page, teams level on points stand in the order of their league's own tie-break rule, for Liga Portugal, the Saudi Pro League and every league with rule rows."
  - "Teams the rule cannot separate keep the provider's order."
  - "The Team page and the match page show the same place as the Table page."
  - "A test fails when a served place differs from the place the league's rule gives, wherever the rule decides."
  - "The MR lists every place that changes, per league, measured on prod before the change."
  - "Rule R7 and docs/metric_layer.md say that the order of teams level on points follows the league's published rule."

decisions_taken: >
  The plan approved in chat, 2026-10-31: the rule's order applies only to a section where every
  team's points and games played equal the provider's row, otherwise the provider's rank stands;
  the exact mart_standings header sentence; the R7 and docs/metric_layer.md sentences, split to
  the sentence-length limit, approved in chat, 2026-10-31; the recurring cost of
  about 60 MB a night. Both leagues' rules checked against their own sources, recorded on #237.

decisions_reserved:
  - "none: every changed sentence and the shipped-number change were approved in the plan"

done_when:
  - dbt parse passes; the changed models pass SQLFluff.
  - The offline gates of validate-local pass.
  - On prod, read-only, the new model's SQL lists every changed place and the new test's SQL returns 0 rows.

amendments: (none)
