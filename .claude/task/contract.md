# Task contract — rename corners_conceded → corners_against end-to-end (#500 PR-d, step 4)

> Governance G2/G3 contract. Written on a clean tree BEFORE any edit.
> Applies the LOCKED `_against` naming convention to its last holdout. No new §10 (the convention is
> decided; the CPO directed this rename this session). Mirrors the existing `goals_against` exactly.

objective: >
  Rename the metric `corners_conceded_per_match` → `corners_against_per_match` across every layer (the
  catalogue SSoT, ~7 dbt models + their schema yml, the UI wiring, and 2 wireframe docs), plus its derived
  forms (`*_season`, `*_recent`, `home_*`/`away_*`, the i18n key). Internal naming consistency only —
  NOTHING ON SCREEN CHANGES (the displayed label already reads "Corners against"). Changes warehouse column
  names + published JSON keys; all affected models are table/view → normal rebuild, no --full-refresh.

refs: #500 PR-d step 4 (follows #582/#583/#584); CPO direction 2026-06-26 ("do it" — finish the locked
  _against convention); plan C:\Users\Rami\.claude\plans\scalable-snuggling-lightning.md (approved).

scope_paths:
  - dbt_project/seeds/metric_catalogue.csv
  - dbt_project/seeds/schema.yml
  - dbt_project/models/4_intermediate/domestic_league/team_season/int_team_season__metrics.sql
  - dbt_project/models/5_marts/shared/mart_team_momentum.sql
  - dbt_project/models/5_marts/domestic_league/mart_matchday_insights.sql
  - dbt_project/models/5_marts/domestic_league/mart_team_season_insights.sql
  - dbt_project/models/5_marts/shared/mart_team_profile.sql
  - dbt_project/models/5_marts/shared/mart_team_season_record.sql
  - dbt_project/macros/team_benchmark_metrics.sql
  - dbt_project/models/4_intermediate/shared/int_competition_benchmarks.yml
  - dbt_project/models/5_marts/shared/shared.yml
  - dbt_project/models/5_marts/domestic_league/domestic_league.yml
  - dbt_project/models/4_intermediate/shared/int_momentum.yml
  - site/i18n/en.json
  - site/i18n/de.json
  - site/i18n/fi.json
  - site/match-preview/metric_bindings.csv
  - site/match-preview/metric_manifest.json
  - site/match-preview/metric_definitions.json
  - site/team-season/index.html
  - docs/wireframes/02_team_profile.md
  - docs/wireframes/metrics_display.md

impact_map: >
  THE RENAME (one substitution, applied to every occurrence): corners_conceded_per_match →
  corners_against_per_match (+ `_season`, `_recent`, `home_`/`away_` forms, + the i18n key
  metrics.corners_conceded_per_match.label → metrics.corners_against_per_match.label). Evidence = the
  exhaustive grep over committed source (catalogue:1, dbt models:7, dbt yml:4, i18n:3, bindings/manifest/
  data-file/team-season:5, docs:2).
  COMPUTE / LINEAGE: the metric is computed in int_team_season__metrics (`_season` column) and
  mart_team_momentum (window column); selected downstream by mart_team_season_insights/_profile/_record;
  mart_matchday_insights aliases the momentum column to the live `home/away_*_recent` columns. The benchmark
  macro + 2 accepted_values yml lists enumerate the id. All affected models are materialized table/view
  (verified) → a column rename rebuilds cleanly with NO --full-refresh / no incremental NULLing.
  UI LOCKSTEP: the live data columns (matchday `*_recent`, team-season `*_season`) rename in the marts →
  the deploy-generated matchday_insights.json / team_season_insights.json keys change → the bindings
  (home/away_column) + the team-season page `row.*_season` read are renamed to match. The export is
  UNCHANGED (it composes the renamed bindings + catalogue); metric_definitions.json is regenerated.
  GUARDS: no-drift guard (assert_no_uncatalogued_season_metric) strips `_season` generically and has NO
  corners reference (verified) → passes (corners_against_per_match_season → corners_against_per_match =
  catalogue id). check_ui_i18n_metrics maps the shown stat through the bindings to the official id →
  metrics.corners_against_per_match.label (renamed) → resolves. test_metric_bindings: the binding's
  catalogue_metric_id resolves in the renamed catalogue; regen matches committed.
  CATALOGUE CHANGE = id + label_i18n_key ONLY; description/interpretation prose kept (mirrors goals_against,
  whose description reads "Average goals conceded per match"). DEPLOY: ci-data-build rebuilds state:modified+.
  LOCAL DBT BROKEN (No module named dbt.adapters.factory) → the dbt side (renames, no-drift guard, DQ) is
  validated by ci-data-build on the PR; will watch that check.

decisions_taken: >
  Execute the CPO-directed rename applying the locked _against convention to its last holdout. Target name
  corners_against_per_match. No metric definition/formula/prose changed; no displayed word changed. The
  corner_kicks/corners word asymmetry, opponent_corner_kicks (numerator), and first_conceded_rank (different
  concept) are explicitly OUT — separate questions, not folded in.

decisions_reserved:
  - team-season `_season` suffix drop (step 5); final teardown (step 6). NONE here.

done_when:
  - `grep -r corners_conceded` over committed source = ZERO remaining.
  - metric_definitions.json regenerated; its diff shows only corners id/label/columns moving to against.
  - i18n guard + test_metric_bindings + JSON validity + full python suite green locally; the dbt side green
    in ci-data-build on the PR.
  - Routes to: scope-auditor + analytics-engineer (dbt_project/**) + football-analytics (metric_catalogue.csv)
    + bi-analyst (site/i18n/** + docs/wireframes/**). Commit carries contract.md → NOT artifact-exempt.
    CPO merges; never self-merge.

amendments:
  - 2026-06-26 (post-CI): ci-data-build surfaced a PRE-EXISTING failure UNRELATED to corners —
    accepted_values_metric_catalogue_entity (dbt_project/seeds/schema.yml) accepts only ["team","player"]
    but the catalogue legitimately carries the locked "team and player" entity (2 rows: finishing_efficiency,
    duels_won_pct). The slim CI re-ran that test because this PR modifies metric_catalogue.csv (so the
    seed's tests rebuild). The corners rename did NOT touch the entity column (diff confirms). Fold the
    one-line fix — add "team and player" to that accepted_values list — into this PR to unblock. Authority:
    CPO direction (the entity value is locked per [[project-metric-layer-two-seeds]]; CPO OK'd folding the
    one-liner in). schema.yml added to scope_paths.
