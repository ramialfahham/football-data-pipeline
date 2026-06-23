# Task contract — remove the unapproved performance_vs_results_gap metric

objective: >
  Remove the uncatalogued, unapproved `performance_vs_results_gap` metric from mart_team_profile. It is a
  derived "deserved-vs-actual" gap (= shot_share_season − points_capture_season) introduced in #324
  (commit 296f449, 2026-06-10 — BEFORE the G3 review cycle existed) that was never added to
  metric_catalogue and never CPO-approved — a metric-catalogue governance violation, and substantively a
  crude proxy (two non-commensurable [0,1] shares with different baselines). CPO ordered immediate removal.
  Keep the two catalogued input metrics (shot_share_season, points_capture_season) as plain season metrics;
  de-claim the "deserved vs actual" framing in the mart doc + drop its yml column doc and range test.
refs: >
  CPO directive this session ("Remove it immediately. ... I didn't approve this."). Violates
  metric-catalogue governance ([[feedback-metric-catalogue-governance]] — never invent a metric in a mart;
  catalogue-first). The missing CI enforcement is tracked by #530. The proper deserved-vs-actual REDESIGN
  is a SEPARATE design thread (not this PR).

scope_paths:
  - dbt_project/models/5_marts/shared/mart_team_profile.sql
  - dbt_project/models/5_marts/shared/shared.yml
  - .claude/task/**

impact_map: >
  writers: mart_team_profile (MODIFY — drop the single derived column performance_vs_results_gap + its doc;
    no other model writes it).
  downstream: mart_team_profile is a LEAF dbt model — `dbt ls --select mart_team_profile+ --resource-type
    model` (venv dbt 1.7.19) → only itself. The sole consumer is scripts/export_site_data.py, which does
    `select * from mart_team_profile` (line 342) but NEVER references performance_vs_results_gap by name
    (`grep -rn performance_vs_results scripts/` → no match), so the exported payload is unaffected; the v2
    site (#391) is PAUSED regardless.
  layer_rules: 5_marts consumption; no layer change. The two retained inputs stay catalogued metrics.
  deploy_order: mart is a view — dropping a column rebuilds on the next run; the export `select *` simply
    returns one fewer column. No migration ordering risk; nothing breaks pre-merge.
  blast_radius: removes ONE uncatalogued column + its range test + doc lines. shot_share_season and
    points_capture_season (both catalogued, approved) are RETAINED. No catalogued number changes; no
    user-facing surface today (site paused). Reversible.

decisions_taken: >
  CPO ordered the removal. SURGICAL scope: remove ONLY the uncatalogued derived gap + its doc/test + the
  "deserved vs actual" framing in the mart header comment. Do NOT remove shot_share_season /
  points_capture_season (they are catalogued, approved season metrics — removing them would be scope creep).
  Do NOT touch metric_catalogue.csv (no catalogue row to remove; the inputs' rows stay). Do NOT redesign
  deserved-vs-actual here.

decisions_reserved:
  - The proper deserved-vs-actual REDESIGN (deepen the team signal beyond raw shot_share into a real,
    catalogued chance-quality composite; the player analog) is a §10 + football-analytics-owned design
    thread, to be scoped in its own issue. NOT decided or built in this PR.

done_when:
  - `grep -rn performance_vs_results_gap dbt_project/ scripts/` → no matches (outside target/).
  - `dbt build --select mart_team_profile` green (model rebuilds; the dropped column's range test is gone).
  - mart header comment no longer claims a "deserved vs actual" differentiator; shared.yml mart description
    + the column doc + the range test for performance_vs_results_gap are removed.
  - SQLFluff clean. Full G3 review: scope-auditor + analytics-engineer-reviewer PASS.

amendments: (none)
