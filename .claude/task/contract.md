# Task contract — TEAM deserved-vs-actual read (SoT rank-space gap)

> Copy to `.claude/task/contract.md` BEFORE touching any file. The contract gate
> denies every edit outside `scope_paths`. Written on a clean tree (branch
> feat/team-deserved-vs-actual off main @ 8097388). CPO-approved this session
> (plan + 4 §10 sub-calls + 4 catalogue rows + interpretation copy).

objective: >
  Build the TEAM deserved-vs-actual read: rank-space gap between a team's actual league
  position and its position deserved by shots-on-target difference. Catalogue-first — add 4
  CPO-approved metric_catalogue rows (sot_difference, shots_on_goal_against_per_match,
  deserved_rank, sot_rank_gap), then the intermediate model chain that computes them.
  Intermediate-only (no mart, no i18n, no frontend — #391 paused).
refs: SoT correlation sweep (memory project_team_metric_rank_correlation_sweep); prerequisite #596 (formula formalization); plan parsed-chasing-micali.md

scope_paths:
  - dbt_project/seeds/metric_catalogue.csv
  - dbt_project/models/4_intermediate/shared/int_team_season_record.sql
  - dbt_project/models/4_intermediate/domestic_league/team_season/int_team_season__metrics.sql
  - dbt_project/models/4_intermediate/domestic_league/team_season/int_team_season__deserved_vs_actual.sql
  - dbt_project/models/4_intermediate/domestic_league/team_season/int_team_season.yml

impact_map: >
  TOOLING NOTE: dbt CLI is broken locally + the dbt MCP is not connected this session, so the
  lineage below is the authoritative ref() DAG traced from source (Grep over dbt_project/), not
  `dbt ls` output. CI ci-data-build is the real build/test gate.

  writers (models I edit/add):
    - int_team_season_record (shared, table) — cumulative team-season record; reads int_legs__team_match
      (which already carries opponent_shots_on_goal) + int_legs__team_from_players. ADD 2 cumulative
      columns: opponent_shots_on_goal (sum), games_with_opp_sot_stats (coverage count).
    - int_team_season__metrics (domestic_league, table) — whole-season rollup = last row of
      int_team_season_record. ADD 2 catalogued metric columns: sot_difference,
      shots_on_goal_against_per_match (gated inline off the new upstream columns; the raw opponent
      cols are NOT output — the assert_no_uncatalogued_season_metric drift guard requires every
      non-exempt/non-_sum_season/non-_sk output column be a catalogue metric_id).
    - int_team_season__deserved_vs_actual (NEW, domestic_league, table) — composes
      int_team_season__metrics (gated sot_difference) + int_team_season__standings_primary
      (standing_rank = actual_rank). Never recomputes sot_difference.

  downstream (ref() consumers — source-traced):
    - int_team_season_record → int_team_season__metrics, int_team_profile__yoy.
    - int_team_season__metrics → int_team_competition_benchmark_metrics_long,
      tests/assert_no_uncatalogued_season_metric, mart_team_season_insights (LIVE MVP),
      mart_team_profile, mart_team_season_record, mart_team_season.
    - int_team_season__deserved_vs_actual → NONE yet (intermediate-only; consumer deferred).

  layer_rules: 4_intermediate may not ref mart_* (check_layer_contract.py). The new model is a
    team-season rollup helper (int_team_season__*), the sanctioned intermediate naming (layering.md).
    Availability handling (coverage gates) lives in the model, NEVER in the catalogue formula
    (formula-vs-availability ruling).

  deploy_order: both edited models + the new model are full-refresh `table` (no incremental →
    NO --full-refresh hazard). Edits are purely ADDITIVE (new columns/model; explicit-column
    SELECTs downstream are untouched), so deployed models do not break until merge. CI ci-data-build
    rebuilds in its isolated dataset; prod via the 04:00 scheduled run.

  blast_radius: NO existing metric/number changes — every existing column output is byte-identical
    (additive selects only). Marts select explicit columns, so the LIVE team_season_insights.json
    keys are unchanged. New surface = 2 raw cols on int_team_season_record, 2 metric cols on
    int_team_season__metrics, 1 new model. Column existence verified by reading the model SQL:
    int_legs__team_match has shots_on_goal + opponent_shots_on_goal; standings_primary has standing_rank.

decisions_taken: >
  CPO-approved this session: (1) the 4 catalogue rows verbatim incl. interpretation copy
  (sot_difference per-match, shots_on_goal_against_per_match per-match, deserved_rank + sot_rank_gap
  rank-derived/blank-expr); (2) gap name = sot_rank_gap; gap direction = neutral; companion name =
  shots_on_goal_against_per_match; deserved_rank IS catalogued (4 rows). (3) Build scope = intermediate
  only (no mart/i18n/frontend, #391 paused). (4) Edge case = require FULL-table SoT coverage per
  league-season (else null deserved_rank/sot_rank_gap for that league-season). (5) Method CPO-locked:
  deserved signal = sot_difference; gap = actual_rank − deserved_rank (positive = under-performing);
  TEAM only, no xG. (6) Formula-vs-availability ruling: per-match denom = count(*); no coverage/coalesce
  in any *_expr. No hardcoded competition filter — the standings-coverage gate generically restricts
  the read to competitions with a full league table (league_code partition rule).

decisions_reserved:
  - rank() tie semantics on equal sot_difference (ties share a deserved_rank, next skips) — the
    approved plan specifies rank(); flag only if the CPO wants dense_rank/row_number instead.
  - The queued governance follow-up (direction/interpretation completeness test scoped to displayed
    metrics + #530 PR2 resolvability) is OUT of scope — its own PR (CPO ruled "queue separately").

done_when:
  - 4 rows appended to metric_catalogue.csv in the formalized structure; resolvability holds
    (sot_difference/companion *_expr columns ∈ int_legs__team_match; deserved_rank/sot_rank_gap blank-expr).
  - int_team_season_record + int_team_season__metrics carry the new columns (additive); the new
    int_team_season__deserved_vs_actual computes deserved_rank + sot_rank_gap under the full-table gate.
  - int_team_season.yml documents the new model + columns with grain/integrity tests; the
    assert_no_uncatalogued_season_metric drift guard still passes (new metric cols are catalogued;
    raw cols are not output).
  - CI ci-data-build green (build + DQ tests); blinded review cycle PASS (scope-auditor +
    analytics-engineer + football-analytics-expert); CPO merges.

amendments: (none)
