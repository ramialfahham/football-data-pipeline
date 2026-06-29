# Task contract — metric-layer integrity tests (completeness + resolvability)

> Written on a CLEAN tree (branch feat/metric-layer-integrity-tests off main @ 1947301).
> CPO-approved this session (plan + the §10 atom copy + the team-only/player-exempt scope).

objective: >
  Add two CI singular tests guaranteeing metric_catalogue integrity: (1) meaning completeness —
  every TEAM metric carries direction + interpretation (player rows exempt, v1.x); (2) formula
  resolvability (#530 PR2) — every numerator_expr/denominator_expr column resolves against its
  base_relation. Plus fill the only 3 team meaning-gaps (the open-play component atoms) so the
  completeness test passes. Seed metadata + tests only — no model or consumer change.
refs: CPO-queued 2026-06-28 (governance follow-up from #596); #530 PR2 (resolvability); plan parsed-chasing-micali.md

scope_paths:
  - dbt_project/seeds/metric_catalogue.csv
  - dbt_project/seeds/schema.yml
  - dbt_project/tests/assert_team_metric_meaning_complete.sql
  - dbt_project/tests/assert_metric_catalogue_expr_resolvable.sql

impact_map: >
  No structural surface in scope (seeds + tests only; no dbt_project/models/**, no ingestion,
  no export/site). Included for transparency:
  writers: none — no model changed.
  blast_radius: NONE. The seed fill touches only `direction`/`interpretation` on 3 team rows; NO
    consumer reads those columns — export_metric_definitions_json.py reads only
    format/lower_is_better/label_i18n_key; export_site_data.py reads neither; the benchmark mart is
    direction-agnostic (mart_team_competition_benchmarks.sql:9 — direction is joined "at display",
    paused #391). `lower_is_better` is UNCHANGED. The 2 new singular tests are gate-only (no output).
  deploy_order: both tests run in ci-data-build after the seed + leg models build. Offline-verified
    they PASS on the current catalogue: completeness — after the fill, 0 team rows are blank;
    resolvability — all 106 exprs resolve against their base relations (token scan vs each leg's
    output columns). No deployed model breaks; additive.
  layer_rules: singular tests live in dbt_project/tests/ (the assert_no_uncatalogued_season_metric
    pattern); no schema.yml test config needed. Formula-vs-availability ruling: untouched (no *_expr
    edited; the resolvability test only READS exprs).

decisions_taken: >
  CPO-approved this session: (1) fill the 3 team component atoms (goals_penalty, goals_own,
  goals_open_play) with direction = higher_better (they are goals FOR the team — they help the
  result and often reflect attacking pressure) + the locked interpretation copy; lower_is_better
  stays false; no null clause (event-derived counts, never coverage-gated). (2) Completeness test
  scope = team only (entity in 'team','team and player'); PLAYER rows exempt (v1.x deferred, per the
  seed schema docs — an existing CPO position). (3) Resolvability test = #530 PR2; SQL-token stoplist
  grounded in the actual expr vocabulary (the only 12 non-column tokens) + a small defensive set.

decisions_reserved:
  - Player-metric direction/interpretation classification (the v1.x deferral) — a future task when
    the player benchmark matures; NOT in scope.
  - A new formula function (future) failing the resolvability stoplist is the intended explicit
    failure mode — adding the function to the stoplist is that future task's call, not pre-decided.

done_when:
  - 3 team atoms carry direction=higher_better + interpretation; the meaning-gap scan shows 0 team gaps.
  - assert_team_metric_meaning_complete.sql + assert_metric_catalogue_expr_resolvable.sql exist and
    pass (offline-predicted green; ci-data-build is the real gate).
  - schema.yml documents the completeness enforcement + the two integrity tests.
  - CSV column-count integrity holds (14 fields/row); check_layer_contract.py passes.
  - blinded review cycle PASS (scope-auditor + analytics-engineer + football-analytics-expert); CPO merges.

amendments: (none)
