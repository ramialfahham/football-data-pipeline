# Task contract — drop the `_season` suffix from season metric columns (#500 PR-d, step 5 / Stage 2)

> Governance G2/G3 contract. Written on a clean tree BEFORE any edit.
> Applies the LOCKED "model column == metric_id" rule to the team-season model (the momentum model already
> obeys it). This is the planned "#500 Stage 2" the drift-guard comment references. No new §10.

objective: >
  Drop the `_season` suffix from the team-season model's METRIC columns (goals_per_match_season →
  goals_per_match, etc.) so they match the catalogue ids, across the producer, 3 marts, a macro, schema yml,
  a DQ test, the drift-guard comment, the team-season page, and 1 wireframe doc. KEEP the `*_sum_season` raw
  intermediates (they mirror the momentum model's `*_sum_form` + are excluded from the drift guard). Internal
  naming consistency only — NOTHING ON SCREEN CHANGES. Changes warehouse columns + the live
  team_season_insights.json keys; affected models are table/view → normal rebuild, no --full-refresh.

refs: #500 PR-d step 5 / Stage 2 (follows #582/#583/#584/#585); CPO direction 2026-06-26 ("push on");
  plan C:\Users\Rami\.claude\plans\scalable-snuggling-lightning.md (approved).

scope_paths:
  - dbt_project/models/4_intermediate/domestic_league/team_season/int_team_season__metrics.sql
  - dbt_project/models/4_intermediate/domestic_league/team_season/int_team_season.yml
  - dbt_project/models/5_marts/domestic_league/mart_team_season_insights.sql
  - dbt_project/models/5_marts/domestic_league/domestic_league.yml
  - dbt_project/models/5_marts/shared/mart_team_profile.sql
  - dbt_project/models/5_marts/shared/mart_team_season_record.sql
  - dbt_project/models/5_marts/shared/shared.yml
  - dbt_project/macros/team_benchmark_metrics.sql
  - dbt_project/tests/assert_mart_team_season_insights_metric_consistency.sql
  - dbt_project/tests/assert_no_uncatalogued_season_metric.sql
  - site/team-season/index.html
  - docs/wireframes/02_team_profile.md

impact_map: >
  THE RENAME (metric columns only): drop `_season` via these patterns — `_per_match_season`→`_per_match`,
  `_accuracy_season`→`_accuracy`, `_ratio_season`→`_ratio`, `_capture_season`→`_capture`, `_share_season`→
  `_share`, `_efficiency_season`→`_efficiency`, `clean_sheets_season`→`clean_sheets`, `goals_penalty_season`→
  `goals_penalty`, `goals_own_season`→`goals_own`, `goals_open_play_season`→`goals_open_play`. NONE of these
  match `*_sum_season` (verified) — the 52 `_sum_season` intermediate occurrences MUST stay constant.
  COMPUTE/LINEAGE: int_team_season__metrics produces the metric columns (rename) + the `*_sum_season`
  intermediates (keep). mart_team_season_insights / mart_team_profile / mart_team_season_record select the
  metric columns (the record mart's `<m>_season as <m>` becomes `<m>`). The benchmark macro's pair 2nd
  element drops `_season` (pair → (X,X), acceptable). The DQ test
  (assert_mart_team_season_insights_metric_consistency) cross-checks metric vs `_sum_season` — its METRIC refs
  drop `_season`, its `*_sum_season` refs STAY. All affected models table/view → no --full-refresh.
  EXPORT (no change): export_pages_data.fetch_team_season_rows uses `SELECT *` (line 136) → renamed mart
  columns flow to the JSON keys automatically; export scripts untouched.
  GUARD: assert_no_uncatalogued_season_metric strips `_season` generically — after the rename that's a no-op
  for metrics (they match the catalogue directly); the `*_sum_season` exclusion still applies. Update its
  stale "until #500 Stage 2" comment; keep the strip as a harmless defensive no-op (minimal-risk).
  UI LOCKSTEP: the live team_season_insights.json keys (deploy-generated via SELECT *) change → the
  team-season page's `row.<metric>_season` reads rename to `row.<metric>`. Nothing visible changes.
  LOCAL DBT: validated via dbt MCP `parse`; the data side (renamed columns, the DQ test, the no-drift guard)
  by ci-data-build on the PR.

decisions_taken: >
  Execute the locked Stage-2 rename (metric column == metric_id). KEEP `*_sum_season` intermediates (mirror
  momentum's `*_sum_form`; not catalogue metrics). No metric definition/formula/displayed-value change. The
  export (SELECT *), the historical audit doc (docs/audits/2026-06_alignment_audit.md), and the macro
  pair-structure simplification are explicitly OUT.

decisions_reserved:
  - Step 6 (final teardown). The macro pair-structure simplification (a tidy-up follow-up). NONE here.

done_when:
  - `git grep` for the metric `_season` patterns over committed source = ZERO; `_sum_season` count = 52 (unchanged).
  - dbt MCP `parse` = OK; the team-season page reads the renamed columns.
  - The dbt side green in ci-data-build (the DQ consistency test + no-drift guard + the rebuild).
  - Routes to: scope-auditor + analytics-engineer (dbt_project/**) + bi-analyst (docs/wireframes/**). The
    commit carries contract.md → NOT artifact-exempt. CPO merges; never self-merge.

amendments: (none)
