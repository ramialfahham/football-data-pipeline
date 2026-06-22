# Task contract — Retire team dribbles_success_pct end-to-end (#510)

objective: >
  Finish the 2026-06-11 display ruling ("team dribbles dropped; stays a player metric") by
  retiring the team `dribbles_success_pct` metric end-to-end. CPO directed option (A) this session:
  remove it from EVERY team surface where it ships — not just the momentum surface #510 enumerated.
  Tracing showed it ships in TWO team surfaces (momentum W1 + season-record W2), NOT the three I
  first listed: the team-season model (int_team_season__full_season_metrics) has no team dribbles,
  and the int_team_season.yml:88 ratio test is the PLAYER one. The player dribbles_success_pct and
  the raw player dribbles_success count are untouched.

refs: >
  Issue #510. Ruling: docs/wireframes/metrics_display.md changelog 2026-06-11. CPO direction this
  session ("A" — end-to-end). The scope note on #510 (team competition benchmark unaffected — not a
  season metric) verified: int_team_season__full_season_metrics has no dribbles.

scope_paths:
  - .claude/task/**
  - dbt_project/seeds/metric_catalogue.csv
  - dbt_project/seeds/schema.yml
  - dbt_project/models/4_intermediate/shared/int_momentum__team.sql
  - dbt_project/models/4_intermediate/shared/int_season_record__team.sql
  - dbt_project/models/5_marts/shared/mart_momentum__team.sql
  - dbt_project/models/5_marts/shared/mart_season_record__team.sql
  - dbt_project/models/5_marts/shared/shared.yml
  - dbt_project/tests/assert_metric_catalogue_unique_by_entity.sql
  - dbt_project/macros/team_benchmark_metrics.sql

decisions_taken: >
  CPO-directed (this session): option (A) end-to-end retirement. Executes the existing 2026-06-11
  display ruling — not a NEW catalogue decision (removing an already-ruled-dropped metric). The
  orphaned raw `dribbles_attempts` + `dribbles_success` SUMS in the two team int models are removed
  too: they exist only to feed the retired pct, and there is no team catalogue metric for the raw
  counts (leaving them would be dead code). Player dribbles + raw player dribbles_success untouched.

decisions_reserved:
  - none. Retirement scope settled by the 2026-06-11 ruling + the CPO (A) direction; surfaces are
    source-verified.

impact_map: >
  Change class: RETIRE team `dribbles_success_pct` end-to-end (#510). Removes a SHIPPED mart column
  from two team surfaces — directed removal; before/after = the column disappears, no retained
  metric's value changes. No raw writer touched.
  Surfaces (traced): W1 momentum — mart_momentum__team (the pct col) + int_momentum__team (orphaned
  dribbles_attempts + dribbles_success sums) + the momentum_team_dribbles_success_pct_in_range test
  (shared.yml). W2 season-record — mart_season_record__team (the pct col) + int_season_record__team
  (orphaned sums) + the std_team_dribbles_success_pct_in_range test (shared.yml). Catalogue —
  metric_catalogue.csv `dribbles_success_pct,team` row + the seeds/schema.yml "retiring/#510"
  direction+interpretation notes. Team-season has NONE (verified).
  Downstream lineage (`dbt ls --select mart_momentum__team+ mart_season_record__team+`):
  mart_momentum__team -> mart_matchday_insights ONLY, which `select *`s the momentum form into a CTE
  but projects explicit renamed rate columns and never references/outputs dribbles_success_pct ->
  transparent, no breakage. mart_season_record__team is a leaf.
  Consumption verified: export_site_data.py references `dribbles_success` only as a PLAYER
  leaderboard/payload field; the team pct is surfaced nowhere -> site/export unaffected.
  Layer rules: check_layer_contract unaffected (column/test removals; no layer violation). Catalogue
  governance: executes the existing 2026-06-11 ruling (football-analytics + analytics-engineer review).
  Deploy ordering: shared warehouse — the two marts rebuild without the column, the seed reloads, and
  the 2 range tests drop on the next CI build; pure removal, no migration ordering.
  Blast radius: the two team marts lose dribbles_success_pct; metric_catalogue loses the team row;
  2 range tests removed; orphaned raw-dribbles sums removed from the 2 int models. Nothing else changes.

done_when:
  - The team dribbles_success_pct is gone from: metric_catalogue.csv (the team row); mart_momentum__team
    + mart_season_record__team (the pct columns); int_momentum__team + int_season_record__team (the
    orphaned dribbles_attempts/success sums + carry-throughs); shared.yml (both range tests);
    seeds/schema.yml (the "#510/retiring" notes). Player dribbles_success_pct untouched.
  - check_layer_contract passes; dbt parse green; the metric-catalogue seed test (uniqueness etc.)
    passes; reviewers PASS (scope-auditor + analytics-engineer + football-analytics-expert).
  - The doc-sync is COMPLETE — no stale "dribbles_success_pct,team" reference remains in any
    description, comment, or test (incl. seeds/schema.yml metric_id desc, the unique-by-entity
    test comment, and the team-benchmark macro comment).
  - Tree matches scope_paths.

amendments:
  - 2026-06-22: + dbt_project/tests/assert_metric_catalogue_unique_by_entity.sql
    + dbt_project/macros/team_benchmark_metrics.sql. Authority: analytics-engineer reviewer FAIL
    (doc-sync / retirement-completeness) + the standing doc-sync rule — both carry stale
    "dribbles_success_pct" comments (the test's both-entities example; the macro's "retiring"
    exclusion note) that the retirement must clear. Comment-only; neither is on the structural
    surface (not under dbt_project/models/), so the impact_map is unchanged. Also fixed the
    in-scope seeds/schema.yml metric_id description (same stale both-entities claim).
