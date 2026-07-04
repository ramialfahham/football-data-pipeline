# Task contract — #530(b): fill the two deferred player metric rows

> Written on a CLEAN tree (branch feat/530b-player-penalty-openplay-catalogue off main @ f7a7d13).
> Metric-catalogue completion. Plan approved via ExitPlanMode this session
> (plan: C:\Users\Rami\.claude\plans\unified-pondering-music.md).

objective: >
  Complete the two player metric_catalogue rows that carry a label + description but blank formula fields:
  `goals_penalty` (player) and `goals_open_play` (player). Fill base_relation = int_legs__player_match,
  numerator_expr (sum(goals_penalty); sum(goals_total - goals_penalty)), direction = higher_better, and a
  short interpretation — mirroring the already-filled TEAM rows (#600) and the player finishing_efficiency
  row. Then sync the seeds/schema.yml base_relation note that still lists these two as "still-deferred".
  No new metric, no model change; the player values already flow from int_player_season__metrics.

refs: #530(b) leg-gap follow-up; unblocked by #621 (goals_penalty atom on int_legs__player_match); mirrors #600/#604 team rows.

scope_paths:
  - dbt_project/seeds/metric_catalogue.csv
  - dbt_project/seeds/schema.yml
  - .claude/task/**

impact_map: >
  Seed-only, catalogue completion. (1) metric_catalogue.csv: fill blank base_relation / numerator_expr /
  direction / interpretation on exactly two existing rows (goals_penalty player; goals_open_play player);
  denominator_expr + importance_tier + group_display_order stay blank (count metrics, matching the team rows).
  numerator_expr stays a PURE formula (no coalesce/countif/null-gate). (2) seeds/schema.yml: drop the
  "still-deferred player rows goals_penalty, goals_open_play (#530 …)" clause from the base_relation column
  description; the numerator/denominator "Blank for the deferred rows above" notes stay valid (rank-derived +
  raw-count rows). No dbt model, no export, no site change. The two metric_ids are ALREADY catalogued, so the
  drift guard assert_no_uncatalogued_season_metric is unaffected; filling base_relation+expr brings them into
  assert_metric_catalogue_expr_resolvable's coverage (it must confirm goals_penalty + goals_total resolve
  against int_legs__player_match — both are exposed there and already used by finishing_efficiency player).

decisions_taken: >
  - Formulas mirror the team rows + the player finishing_efficiency row: goals_penalty = sum(goals_penalty);
    goals_open_play = sum(goals_total - goals_penalty) (player goals_total already excludes own goals).
  - direction = higher_better for both — INHERITS the settled #600 team ruling (these are goals FOR the
    player; they help the result). Direct analog, NOT a new §10 metric decision.
  - Keep the existing (correct) description text; fill only the blank fields.

decisions_reserved:
  - Any change to the metric DEFINITION beyond completing the deferred fields (out of scope).

done_when:
  - Both player rows have non-blank base_relation (int_legs__player_match), numerator_expr, direction, interpretation.
  - schema.yml no longer calls goals_penalty/goals_open_play "still-deferred".
  - scope-auditor + analytics-engineer-reviewer + football-analytics-expert-reviewer PASS (>=2 named risks each);
    review.md diff_sha256 binds; ci-data-build green (resolvability guard passes). CPO merges.

amendments: []
