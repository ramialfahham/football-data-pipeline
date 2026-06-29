# Review — feat/530a-split-entity-dual-metrics — 2026-06-29

> Blinded review cycle (G3). Round 3 (final). All three required reviewers re-run fresh on the
> reverted diff. Required set for the staged paths (metric_catalogue.csv + dbt_project/**):
> scope-auditor (always) + analytics-engineer (dbt_project/**) + football-analytics-expert
> (metric_catalogue.csv).

diff_sha256: c3302cda40059d389631a312412d70a75be696a7c79e3bdc40d064007e0eea66

## scope-auditor
VERDICT: PASS
risks_checked:
- Prose-model-test alignment on finishing_efficiency [0,1]: the round-2 contradiction is resolved — the team + deferred-player descriptions now read "In [0, 1] … Null when … outside [0, 1]", matching the deployed model (int_team_season__metrics.sql:156-158 nulls <0 or >1), the dbt test (int_player_season_position.yml:21, "between 0 and 1"), and CPO Option A. No remaining doc-vs-warehouse divergence.
- Scope catalogue-only: diff is exactly 3 files (metric_catalogue.csv, schema.yml, contract.md); no model/ingestion/export/protected-path edits; impact_map correctly omitted (seed config, no structural surface). Formula purity upheld (no coalesce/countif/null-gate in any *_expr); decisions_reserved held (player finishing_efficiency ships blank/deferred; no new i18n keys; per-entity formulas rest on the recorded CPO sign-off).

## analytics-engineer-reviewer
VERDICT: PASS
risks_checked:
- Token resolution for all three resolvable rows: finishing_efficiency/team (goals_for, goals_penalty, goals_own, shots_on_goal) against int_legs__team_match (lines 113, 130-131, 116); duels_won_pct/team (duels_won, duels_total) against int_legs__team_from_players (lines 32-33); duels_won_pct/player (same) against int_legs__player_match (lines 71-72). No unresolved identifiers — assert_metric_catalogue_expr_resolvable will pass.
- Deferred finishing_efficiency/player correctly blank-base: goals_penalty is confirmed absent from int_legs__player_match, so the deferral is structurally mandatory (filling it would fail resolvability). CSV integrity: 14 fields/row, no broken quoting from the prose edits, base_relation accepted_values satisfied, (metric_id, entity) unique, team-meaning completeness holds (both team rows carry direction+interpretation), no coalesce/countif/null-gate in any *_expr.

## football-analytics-expert-reviewer
VERDICT: PASS
risks_checked:
- finishing_efficiency team formula column names (goals_for, goals_penalty, goals_own, shots_on_goal) verified present in int_legs__team_match; the [0,1] null-guard in int_team_season__metrics.sql:155-158 matches the description ("Null when the window is not fully shot-covered or the value would fall outside [0, 1]"); open-play numerator (goals minus penalties and own goals) is football-sound; direction=higher_better correct.
- duels_won_pct team vs player: same ratio sum(duels_won)/sum(duels_total) at team-aggregated (int_legs__team_from_players) vs player (int_legs__player_match) grain — no formula asymmetry; direction=higher_better correct; deferred player finishing_efficiency row is honest (goals_total already excludes own goals; shots_on matches the model column). The wireframe "never capped" line (metrics_display.md:107) is stale vs Option A — flagged for separate reconciliation, not a FAIL of this PR.

## escalations
- question: Should finishing_efficiency be described as bounded [0,1] (matching the deployed model + dbt test + CPO Option A) or "never capped / can exceed 100%" (matching a line in docs/wireframes/metrics_display.md:107)?
  CPO ANSWER: The CPO first directed "fix now" toward the never-capped wording (on the wireframe basis). On surfacing that the deployed model (int_team_season__metrics.sql:156-158), the dbt test (int_player_season_position.yml:21) and the "CPO Option A" ruling all enforce [0,1], the catalogue prose was reverted to [0,1] to match the deployed/tested behavior; the CPO did not object to that correction. The stale wireframe "never capped" line (metrics_display.md:107) is to be reconciled separately, not in this PR.
