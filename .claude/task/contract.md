# Task contract — player contribution-share (int_player_profile__contribution + catalogue)

> Written on a CLEAN tree (branch feat/player-contribution-share off main @ c375a99).
> Phase D "bonus" flagship read (content_architecture §6.4): a player's goal-involvement share of the team's
> WHOLE-SEASON goals ("involved in X% of Bayern's goals"). Scope widened post-review to CATALOGUE the new ratio
> metric (analytics-engineer A1 finding, CPO-confirmed) — adds metric_catalogue.csv + the football-analytics reviewer.

objective: >
  Build int_player_profile__contribution (a player-profile differentiator, mirroring int_player_profile__yoy) +
  compose it into mart_player_profile + CATALOGUE contribution_share (the new ratio metric). Numerator = goal
  involvements (scorer_points = goals + assists); denominator = the team's whole-season goals_for. Grain
  (player_sk, team_sk, season_sk); attached via the primary club; auto-carries to the export via select *.
refs: #391 Phase D bonus; content_architecture §6.4; mirrors #638 (player YoY) + int_team_season__deserved_vs_actual (#598 catalogued deserved_rank/sot_rank_gap)

scope_paths:
  - dbt_project/models/4_intermediate/shared/int_player_profile__contribution.sql
  - dbt_project/models/4_intermediate/shared/int_player_profile.yml
  - dbt_project/models/5_marts/shared/mart_player_profile.sql
  - dbt_project/seeds/metric_catalogue.csv
  - .claude/task/**

impact_map: >
  writers: NEW int_player_profile__contribution (4_intermediate/shared, table) reads int_legs__player_match +
    int_legs__team_match (composing intermediate; atoms not recomputed). mart_player_profile gains a contribution
    CTE + a left join + 3 columns (scorer_points, team_goals_season, contribution_share). metric_catalogue.csv
    gains ONE row: contribution_share (a NEW player ratio metric).
  downstream: int_player_profile__contribution -> mart_player_profile (the ONLY consumer) -> the v2 player export
    (`select *`, auto-carry, NO export edit). metric_catalogue.csv -> the catalogue-integrity CI tests
    (assert_metric_catalogue_expr_resolvable SKIPS blank-base_relation rows, so contribution_share is skipped like
    deserved_rank; assert_team_metric_meaning_complete exempts PLAYER rows; assert_metric_catalogue_unique_by_entity).
    The drift guard assert_no_uncatalogued_season_metric scans only the 3 season rollups — unaffected. dbt ls is
    CI-only; ref-graph cited from the files.
  layer_rules: intermediate reads two int legs (no mart ref) — layering.md compliant. check_layer_contract passes offline.
  deploy_order: ADDITIVE — a NEW model + 3 NEW nullable mart columns + 1 NEW catalogue row. No rename/drop of any
    EXISTING column/row. ci-data-build builds it; the catalogue seed reloads. No shared-warehouse migration hazard.
  blast_radius: mart_player_profile gains scorer_points + team_goals_season + contribution_share (existing columns/
    numbers UNCHANGED); the export gains them via select *; the catalogue gains contribution_share. No other
    mart / number / metric changed.

decisions_taken: >
  Metric definition (CPO AskUserQuestion 2026-07-03, logged in escalations.log): numerator = goal involvements
  (goals + assists); denominator = the team's WHOLE-SEASON goals_for; DIRECTION = NEUTRAL (high share = central to
  the team's output but position-dependent; no good/bad colour; mirrors the 7 neutral benchmark metrics).
  contribution_share = safe_divide(scorer_points, team_goals_season); NULL when the team scored 0; invariant
  0 <= share <= 1. Grain (player_sk, team_sk, season_sk); NOT domestic-restricted. NAMING:
  int_player_profile__contribution (mirrors int_player_profile__yoy + shares int_player_profile.yml). The numerator
  atom is named `scorer_points` (the EXISTING catalogued metric goals+assists — reconciled per the analytics-engineer
  A1 finding, NOT a new duplicate name). CATALOGUE: contribution_share added to metric_catalogue.csv with BLANK
  base_relation / numerator_expr / denominator_expr — the deserved_rank/sot_rank_gap flagship-output pattern (the
  formula lives in the description prose + the model; the resolvability guard skips blank-base_relation rows);
  entity=player, format=percent, direction=neutral, metric_group=goals. team_goals_season is the ratio's DENOMINATOR
  COMPONENT carried for the "X of Y team goals · Z%" display triple (like the benchmark's carried num/den atoms) —
  not a standalone metric. Composed into mart_player_profile via the primary club (ta.team_sk). Auto-carry via
  select * (#606). Honest limit (CPO-accepted): the whole-season denominator vs the covered-appearance numerator
  understates the share where the player's match stats are missing — documented in the model header.

decisions_reserved:
  - A contribution-share SCREEN (wireframe + explicit export shaping) is a later gap, not this brick.
  - All §10 settled by the three AskUserQuestion rulings (numerator, denominator, direction). No other open decision.

done_when:
  - int_player_profile__contribution builds; grain unique; keys not_null; 0 <= share <= 1 holds; ci-data-build green.
  - mart_player_profile gains scorer_points + team_goals_season + contribution_share; EXISTING numbers unchanged.
  - metric_catalogue.csv has the contribution_share row; the catalogue-integrity tests pass (blank-base_relation skip).
  - python scripts/check_layer_contract.py passes.
  - bq spot-check: a focal striker (Kane, BL1) ~32%; a squad player much lower.
  - scope-auditor + analytics-engineer-reviewer + football-analytics-expert-reviewer PASS (>=2 named risks each);
    review.md diff_sha256 binds; CPO merges.

amendments:
  - 2026-07-03: post-review scope widening (analytics-engineer A1 FAIL that contribution_share ships uncatalogued;
    CPO-confirmed via the direction AskUserQuestion) — added dbt_project/seeds/metric_catalogue.csv to scope
    (catalogue contribution_share; rename the goal_involvements atom -> the existing catalogued scorer_points).
    Authority: the AE A1 finding (governance-required) + the CPO ruling. Pulls in football-analytics-expert-reviewer.
