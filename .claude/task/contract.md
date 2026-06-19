# Task contract — feat: mart_leaderboards + full consolidation (PR 2b)

> PR 2b of the split leaderboards build (CPO-directed 2026-06-19). Build the LONG leaderboards mart
> ranking by the 9 count boards (the v1 set; rate boards deferred #506), and FULLY CONSOLIDATE the
> leaderboard surface onto it: retire mart_top_scorers + orphaned mart_player_season, drop the 3 now-dead
> rank columns from mart_player_profile, repoint BOTH export paths. Builds on PR 2a's composites
> (#507, merged) — the mart ranks by scorer_points / defensive_actions / cards_total + the existing atoms.

objective: >
  Add mart_leaderboards — a LONG per-board player ranking (one row per player per board), season-to-date
  via int_player_season__metrics, top 10 per (league_code, season_api_year, metric_key), DENSE_RANK (ties
  share, top-10 inclusive of ties). 9 count boards: goals, scorer_points, shots_on_target,
  dribbles_success, passes_total, passes_key, duels_won, defensive_actions, cards_total. Then consolidate:
  delete mart_top_scorers + mart_player_season (orphaned once top_scorers retires); drop goals_rank /
  assists_rank / shots_on_target_rank (+ their tests) from mart_player_profile; repoint
  export_site_data.py's competition-hub top_scorers (now metric_key='goals' from mart_leaderboards) AND
  fetch_leaderboard_payloads / shape_leaderboards (now grouped by metric_key from mart_leaderboards).

refs: leaderboards v1 design (this conversation); PR 2a = #507 (the 3 composites); deferred rate boards = #506.

scope_paths:
  - dbt_project/models/5_marts/shared/mart_leaderboards.sql
  - dbt_project/models/5_marts/shared/mart_top_scorers.sql
  - dbt_project/models/5_marts/shared/mart_player_season.sql
  - dbt_project/models/5_marts/shared/mart_player_profile.sql
  - dbt_project/models/5_marts/shared/shared.yml
  - dbt_project/models/4_intermediate/domestic_league/team_season/int_player_season__metrics.sql
  - dbt_project/models/4_intermediate/domestic_league/team_season/int_team_season.yml
  - dbt_project/docs/layering.md
  - docs/site_architecture.md
  - docs/ui_design_brief.md
  - scripts/export_site_data.py
  - tests/test_export_site_data.py
  - .claude/task/contract.md
  - .claude/task/review.md

decisions_taken: >
  CPO-directed (2026-06-19): leaderboards v1 = 9 COUNT boards; FULL consolidation (single surface).
  mart_leaderboards composes int_player_season__metrics directly (the full atom set incl. PR 2a's
  composites), NOT mart_player_season (lacks duels/dribbles/tackles). LONG shape, metric_key = the
  catalogue metric_id, rank = DENSE_RANK over the metric desc within (league_code, season_api_year),
  ties share, where rank <= 10; only positive-value rows ranked (a leaderboard shows players with a
  positive count). Materialised as a view (thin ranking over the int table, like the retired
  mart_top_scorers). Identity from dim_player (name, nationality, photo, listed position). The mart
  carries the union of the 9 boards' display atoms so the export selects per board (marts contain what
  we show). Retiring mart_player_season is in scope (orphaned). The int model docstrings are updated to
  drop the now-dead mart_player_season reference (clean retirement). mart_player_profile loses 3 rank
  columns (a shipped-mart shape change) — the export no longer reads them after the repoint.

decisions_reserved:
  - The 5 rate boards + finishing_efficiency + the qualification floor are deferred (#506) — not here.
  - i18n: the catalogue label keys are not added to site/i18n here (deferred until UI-surfaced; the
    established convention) — no site/i18n / wireframe change, so no bi-analyst routing.
  - Leaderboard position badge: use dim_player.player_position (bio), not the season modal position_code
    (avoids replicating mart_player_profile's modal CTE). If a reviewer judges the modal is required for
    parity, that is a build-detail call — record it.
  - If retiring mart_player_season breaks any consumer not found by grep, STOP — do not force the delete.

done_when:
  - mart_leaderboards compiles; `dbt parse` clean; sqlfluff lint passes. Grain unique on
    (player_sk, season_sk, metric_key); metric_key accepted_values = the 9 board ids; rank >= 1 and <= 10;
    player_sk -> dim_player relationship; not_null on keys + league_code.
  - mart_top_scorers.sql + mart_player_season.sql deleted; their shared.yml + layering.md entries removed;
    no remaining dbt ref()/code usage of either model; the "upstream mart" references in
    docs/site_architecture.md + docs/ui_design_brief.md + the layering.md ranking illustration are
    updated to mart_leaderboards (clean retirement). The new mart docstrings' "retired mart_top_scorers"
    mentions are intentional; broader historical doc mentions are #505 doc-audit territory.
  - mart_player_profile no longer has goals_rank / assists_rank / shots_on_target_rank (+ their 3 tests).
  - export_site_data.py: both the competition-hub top_scorers and fetch_leaderboard_payloads read
    mart_leaderboards; no reference to mart_top_scorers or mart_player_profile rank columns remains.
  - tests/test_export_site_data.py updated to the new LONG/metric_key shapes; `pytest tests/test_export_site_data.py` passes.
  - `dbt parse` resolves with no dangling ref to the deleted models; the validate-local offline gates pass.
  - reviewers: scope-auditor + analytics-engineer-reviewer + cto-reviewer PASS (>=2 risks each); no FAIL; no ESCALATE.

amendments:
  - 2026-06-19: + docs/site_architecture.md + docs/ui_design_brief.md — authority:
    analytics-engineer-reviewer FAIL (round 1): the deleted mart_top_scorers was still named as the live
    upstream mart in these product docs. Clean retirement updates references to the retired model.
    Content: change the mart_top_scorers source references to mart_leaderboards (one token each). The same
    round-1 FAIL also surfaced that the 3 composite columns (scorer_points / defensive_actions /
    cards_total) were computed in the mart's base CTE but dropped from its final SELECT — added them to
    the SELECT + shared.yml + the export _LB_KEEP (all in the original scope). Plain docs/** routes only
    to scope-auditor — no new reviewer.
