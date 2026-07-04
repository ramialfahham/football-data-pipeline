# Task contract — enrich player YoY block with a full-season prior-year reference

> Written on a CLEAN tree (branch feat/player-yoy-full-season-reference off main @ a6b90e9).
> dbt-only enrichment of the already-wired player YoY block. Plan approved via ExitPlanMode
> (plan: C:\Users\Rami\.claude\plans\unified-pondering-music.md).

objective: >
  Add the prior season's FULL-season totals as a context anchor to the appearances-aligned
  player YoY (int_player_profile__yoy, #638). For each of the existing 5 YoY metrics
  (goals / assists / shots_on_goal / key_passes / defensive_actions) expose the prior
  season's complete cumulative total (max match_number, no cutoff cap) plus an
  appearances_prev_full count, so the profile can anchor the pace-matched delta against how
  big last season actually was. Context only — NO delta-vs-full is computed. Surface the new
  columns in mart_player_profile; they auto-carry to the v2 player export (select * + the
  _strip_identity season-block spread — verified, no export edit).

refs: #638 (int_player_profile__yoy base); mirrors int_team_profile__yoy pattern. Plan approved this session.

scope_paths:
  - dbt_project/models/4_intermediate/shared/int_player_profile__yoy.sql
  - dbt_project/models/5_marts/shared/mart_player_profile.sql
  - dbt_project/models/4_intermediate/shared/int_player_profile.yml
  - .claude/task/**
  - .claude/active_work.md

impact_map: >
  dbt-only, additive. (1) int_player_profile__yoy gains a `prev_full` CTE (prior season at
  the same club, max match_number, WITHOUT the `<= appearances_cutoff` cap) + 6 new nullable
  columns (appearances_prev_full + 5 *_prev_season_full). Grain unchanged
  (team_sk, player_sk, league_code, season_api_year); existing columns/deltas untouched.
  (2) mart_player_profile selects the 6 new `y.` columns into its YoY block; grain
  (player_sk, season_sk) unchanged; the existing left join key unchanged. (3) The 6 columns
  auto-carry to scripts/export_site_data.py's player payload via `select *` + the generic
  `_strip_identity` season-block spread — NO export edit. NO metric_catalogue.csv change (these
  are uncatalogued windowed variants, exactly like the existing *_prev_season / *_delta_yoy;
  the drift guard assert_no_uncatalogued_season_metric covers only the season-metrics models,
  not this one). NO new model, NO live-MVP (site/) change, NO v2 frontend. New DQ test
  (dbt_utils.expression_is_true): full-season cumulative total >= the pace-matched figure.

decisions_taken: >
  - Full-season figures are CONTEXT only; NO delta-vs-full (a part-season-so-far minus a full
    prior season is apples-to-oranges — the model header already warns against it). The
    existing pace-matched *_delta_yoy stays the only delta.
  - Keep the #638 5-metric set exactly; do NOT re-open it.
  - Naming: `_prev_season_full` / `appearances_prev_full` (CPO accepted the proposal at ExitPlanMode).
  - Domestic-leagues-only + primary-club scope inherited from the base model, unchanged.

decisions_reserved:
  - Widening the delta metric set beyond the 5 (CPO declined for this PR; a later toggle if wanted).
  - A dedicated YoY display/wireframe screen (separate #391 gap, not this PR).

done_when:
  - int_player_profile__yoy exposes appearances_prev_full + goals/assists/shots_on_goal/key_passes/defensive_actions _prev_season_full, NULL when no prior season at the club.
  - mart_player_profile carries the 6 new columns in its YoY block.
  - int_player_profile.yml documents the columns + adds the full >= pace-matched invariant DQ test.
  - scope-auditor PASS + analytics-engineer-reviewer PASS (>=2 named risks each); review.md diff_sha256 binds; ci-data-build green. CPO merges.

amendments: []
