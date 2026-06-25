# Review — fix/incomplete-data-null — 2026-06-25

> Governance G3 Lock artifact. Reviewers spawned cold (blinded) on the cumulative
> branch diff (`.claude/task/review_input.patch`). Required set for the staged paths
> (dbt_project/**): scope-auditor (always) + analytics-engineer-reviewer. cto-reviewer
> not required (no scripts/tests/hooks/workflows); football-analytics not required
> (the metric_catalogue is untouched — only NULL behaviour changes, no metric created
> or redefined).

diff_sha256: d448a8a800982c920ffc62eb92dc51d97eb434d11ed96d0eee8bf406d8f5ddcf

## scope-auditor
VERDICT: PASS
risks_checked:
- Team-feed vs player-derived boundary preserved: the diff gates only the genuine team-feed
  stats (shots/passes/corners/saves + their season count totals) on their own coverage buckets,
  and DELIBERATELY leaves the player-derived team metrics (key_passes/tackles/interceptions/
  blocks/defensive_actions/duels/duels_won_pct) ungated on games_with_player_stats in both
  marts — exactly the CPO ruling "missing player stats must not affect the team stats". The
  downstream live marts (mart_matchday_insights, mart_team_season_insights) are not edited →
  pure inheritance, no re-derivation.
- §10 decisions all recorded before implementation: Q2 (reverse #320 — a shipped-numbers change)
  and Q1 (include counts) are CPO-answered in escalations.log (AskUserQuestion 2026-06-25); the
  player side is DROPPED on the proven null=zero premise; no metric is created or redefined, so
  the catalogue is untouched and football-analytics review is not required. The int_season_record.yml
  scope addition rode in via a recorded amendment whose authority is the contract's approved scope
  category "schema docs for the touched models" (not reviewer-FAIL authority).

## analytics-engineer-reviewer
VERDICT: PASS
risks_checked:
- No-drift guard safety: the three new coverage-bucket columns (team_stat_coverage_season_games,
  opp_stat_coverage_season_games, save_stat_coverage_season_games) are computed in aggregated_season
  and pass through season_gated's `select *`, but the model's final SELECT (int_team_season__metrics
  lines 171-257) is a fully enumerated column list that contains none of them — so the materialised
  output schema gains no columns and assert_no_uncatalogued_season_metric is not tripped. Verified
  against the file.
- NULL-propagation correctness: gating the 9 team-feed sum columns in season_gated NULLs every
  dependent team-feed per-match rate/ratio via safe_divide(null, …) (e.g. shots_per_match_season,
  shot_accuracy_season, save_ratio_season), with no team-feed metric left ungated and no
  player-derived/scoreline metric wrongly NULLed. games_with_save_stats is correct in both builders
  (momentum countif; season-record cumulative sum(...) over w) and is carried through
  mart_season_record__team's matched/chosen to the explicit save_ratio CASE gate. The not_null tests
  on the new column are valid (countif / windowed 0-1 sum are never null).

## escalations
(none)
