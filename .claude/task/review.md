# Review — refactor/500-pr-b — 2026-06-25 (PR-b1: deep atom renames)

> G3 Lock artifact. Reviewers spawned cold (blinded) on the cumulative branch diff
> (`.claude/task/review_input.patch`). Required set for the staged paths (dbt_project/models/**
> + dbt_project/seeds/metric_catalogue.csv): scope-auditor (always) + analytics-engineer-reviewer
> (dbt) + football-analytics-expert-reviewer (metric_catalogue.csv). cto-reviewer NOT required
> (no scripts/tests/hooks/workflows touched).

diff_sha256: cbb5a40fccc4e2c2a1d82fd4a9b89de8d78db2656712230e61ddae48e1e11b29

## scope-auditor
VERDICT: PASS
risks_checked:
- Incremental-fact column-rename deploy hazard: fct_fixture_player_stats is materialized=incremental
  with on_schema_change='sync_all_columns', so a normal incremental run after the rename would DROP
  goals_saves/goals_conceded and ADD saves/goals_against as NULL for all historical rows. The contract
  flags the one-time `--full-refresh` requirement in deploy_order + decisions_reserved D1 + done_when,
  for CPO coordination at merge. Risk is structural (inherent to the rename), correctly owned/documented.
- Collision-resolution soundness (mart_player_match_log DROP): the dropped player goals_conceded is a
  GK-exclusive atom (escalations.log records the source-of-record finding — only the keeper carried a
  non-zero value, outfielders 0; catalogue row 54 labels it GK-relevant; code pairs it with saves). In a
  per-match log it is redundant with the match-scoreline goals_against already shown. The CPO ruling
  (drop) is recorded in escalations.log; scope (the slice, the rename targets) is CPO-authorised.

## analytics-engineer-reviewer
VERDICT: PASS
risks_checked:
- mart_player_match_log collision: the player goals_conceded is gone from BOTH the joined CTE and the
  final SELECT; the scoreline goals_against (if home/away from fct_fixture) is independent and UNTOUCHED;
  the W/D/L CASE references the scoreline goals_against only; no duplicate goals_against column. Verified
  on disk.
- Rename completeness + no-drift guard: grep for goals_saves/goals_conceded/shots_on_target across model
  .sql + .yml returns zero matches in business logic (only the guard's historical comment, exempted); the
  JSON extraction paths ($.goals.saves / $.goals.conceded) are unchanged (alias-only rename); the guarded
  season models output the SAME column set (saves/goals_against are the pre-existing PR-a aliases; only
  internal atoms renamed) so assert_no_uncatalogued_season_metric is unaffected; the incremental
  --full-refresh requirement is correctly identified and all downstream models are tables/views.

## football-analytics-expert-reviewer
VERDICT: PASS
risks_checked:
- Identity preservation of the derived GK formulas: shots_on_goal_against numerator saves + goals_against
  still equals shots-on-target faced; save_pct = saves / (saves + goals_against) is unchanged and
  self-bounded to [0,1] (safe_divide handles the zero-denominator no-shots-on-target case); saves_per90 /
  the player goals_against row are renamed atoms, same quantity. Every catalogue formula is algebraically
  identical to the pre-rename version — a rename, not a redefinition.
- Football correctness + deferral honesty: the player goals_against (goals conceded while the GK was on
  the pitch) is a correct GK stat paired with saves; lower_is_better=true is correct. The description /
  label_i18n_key prose retaining legacy wording ("goals conceded", "shots on target") is the deliberately
  DEFERRED display/i18n work (PR-c/PR-d per the locked sequence), not an un-deferred redefinition.

## escalations
(none)
