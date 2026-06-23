# Task contract — #500 team-season consolidation (Option A: rename + mart dedup)

objective: >
  #500 Option A (CPO: "Then it's A" + "Rename + fold that dedup"). (1) Rename
  int_team_season__full_season_metrics -> int_team_season__metrics, parallel to
  int_player_season__metrics (#480); keep the per-match record (int_season_record__team) and
  standings (int_team_season__standings_primary) as distinct surfaces, mirroring the player side.
  (2) Fold the one real redundancy: mart_team_season re-aggregates season W/D/L/goals from
  int_legs__team_match that the rollup already sums — add wins/draws/losses_sum_season to the
  rollup and have mart_team_season COMPOSE the rollup instead of re-aggregating. Byte-identical
  refactor — NO shipped-number change. Defer the `_season`-suffix / goals_saves COLUMN alignment
  (a larger separate cascade) to a follow-up.

refs: >
  #500 (team analog of #480). The catalogue drift-test comment earmarks the `_season`/goals_saves
  column alignment for #500 — deferred here (see decisions_reserved).

scope_paths:
  - dbt_project/models/4_intermediate/domestic_league/team_season/int_team_season__full_season_metrics.sql
  - dbt_project/models/4_intermediate/domestic_league/team_season/int_team_season__metrics.sql
  - dbt_project/models/4_intermediate/domestic_league/team_season/int_team_season.yml
  - dbt_project/models/5_marts/shared/mart_team_season.sql
  - dbt_project/models/5_marts/domestic_league/mart_team_season_insights.sql
  - dbt_project/models/5_marts/shared/mart_team_profile.sql
  - dbt_project/models/5_marts/shared/mart_competition_benchmarks__team.sql
  - dbt_project/models/4_intermediate/shared/int_competition_benchmarks__team.sql
  - dbt_project/macros/team_benchmark_metrics.sql
  - dbt_project/models/5_marts/shared/shared.yml
  - dbt_project/tests/assert_no_uncatalogued_season_metric.sql
  - docs/metric_layer.md
  - .claude/task/**

impact_map: >
  writers: int_team_season__metrics (renamed from __full_season_metrics) — SAME aggregation over
    int_legs__team_match + int_legs__team_from_players, PLUS three new counts
    wins_sum_season/draws_sum_season/losses_sum_season + the previously-internal clean-sheet count
    now EXPOSED in the final select as clean_sheets_sum_season (the `_sum_season` convention keeps
    them catalogue-exempt). mart_team_season — now COMPOSES int_team_season__metrics for the season
    counts (played=season_games_played, goals_for/against=*_sum_season, points=points_won_sum_season,
    clean_sheets=clean_sheets_sum_season, +W/D/L) and DROPS its own int_legs__team_match
    aggregation; keeps the dim_team + int_team_season__standings_primary joins.
  downstream: pasted from `dbt ls` this session (raw --output name):
    $ dbt ls --select int_team_season__full_season_metrics+ --resource-type model --output name
        int_competition_benchmarks__team
        int_team_season__full_season_metrics
        mart_competition_benchmarks__team
        mart_team_profile
        mart_team_season_insights
    $ dbt ls --select mart_team_season+ --resource-type model --output name
        mart_team_profile
        mart_team_season
        mart_team_season_insights
    (team_benchmark_metrics macro NAMES the model in a comment only — no ref(), confirmed by grep.)
  layer_rules: the rename is name-only. The dedup moves leg-aggregation OUT of the mart and makes
    the mart a consumer of the intermediate rollup — logic moves UP the layers (correct direction).
    No staging/core touched. check_layer_contract unaffected.
  deploy_order: all tables/views; ci-data-build does a full rebuild so int_team_season__metrics is
    created under the new name. The old int_team_season__full_season_metrics relation is orphaned in
    the shared warehouse (dbt does not drop a renamed model's old table) — harmless, swept by the
    next full-refresh; no consumer references it post-rename.
  blast_radius: NO shipped-number change intended. The rename is name-only. The mart_team_season
    dedup is byte-identical: the rollup's sums equal mart_team_season's prior agg over the SAME legs
    (SUM ignores nulls == SUM(coalesce(.,0)); finished legs carry non-null goals, so
    clean_sheets_count_season == countif(coalesce(goals_against,0)=0); count(distinct fixture_sk) ==
    count(*) at the one-row-per-(team,fixture) leg grain). wins/draws/losses are newly RELOCATED
    from the mart into the rollup. Byte-identity is established PRE-HOC by the column-equivalence
    reasoning above (each composed column maps 1:1 to an existing rollup sum); ci-data-build
    before/after = 0 diff on mart_team_season + mart_team_profile + mart_team_season_insights is the
    done_when CONFIRMATION gate (runs on the PR, not yet executed). The benchmark engine reads only
    the rate columns (unchanged), so int_competition_benchmarks__team / mart_competition_benchmarks__team
    are inert.

decisions_taken: >
  Option A approved by the CPO this session ("Then it's A"; "Rename + fold that dedup"). Mirror
  #480: int_team_season__metrics is the canonical season rollup; the per-match record and standings
  stay as separate surfaces (not merged). The mart_team_season aggregation dedup is folded in and
  must be byte-identical. New W/D/L counts use the `_sum_season` suffix (catalogue-exempt, matching
  the existing raw-sum columns).

decisions_reserved:
  - The `_season`-suffix / goals_saves COLUMN-name alignment (catalogue-test comment ties it to #500)
    is DEFERRED — a large separate cascade (the benchmark engine + marts + metric layer). CPO scoped
    THIS PR to rename + dedup. The drift-test keeps its `_season`/goals_saves normalisation until that
    follow-up.
  - If ci-data-build shows ANY delta on mart_team_season or its downstream, the dedup is NOT
    byte-identical -> stop and reconcile before merge; never ship a silent number change (§10).

done_when:
  - int_team_season__metrics exists; int_team_season__full_season_metrics gone; every ref updated
    (int_competition_benchmarks__team, mart_competition_benchmarks__team, mart_team_profile,
    mart_team_season_insights, the drift-test depends_on + model tuple); dbt parse + sqlfluff clean.
  - mart_team_season composes the rollup, no longer reads int_legs__team_match; same output columns
    + grain.
  - assert_no_uncatalogued_season_metric passes (W/D/L exempt via `_sum_season`).
  - validate-local passes; ci-data-build green; before/after diff on mart_team_season +
    mart_team_profile + mart_team_season_insights = 0 rows changed.

amendments: (none)
