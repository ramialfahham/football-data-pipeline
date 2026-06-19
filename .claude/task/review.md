# Review — feat/mart-leaderboards — 2026-06-19

> PR 2b of the split leaderboards build: mart_leaderboards (LONG, 9 count boards) + full consolidation
> (retire mart_top_scorers + mart_player_season, drop mart_player_profile's 3 rank columns, repoint both
> export paths). Round 2: round-1 analytics-engineer FAIL resolved — the 3 composites (scorer_points /
> defensive_actions / cards_total) were computed in the mart's base CTE but dropped from the final SELECT;
> added them to the SELECT + shared.yml + the export _LB_KEEP; and the stale mart_top_scorers references
> (layering.md illustration + docs/site_architecture.md + docs/ui_design_brief.md) updated to
> mart_leaderboards (contract amended to bring the 2 product docs into scope). Required reviewers for the
> staged paths (dbt_project/** + scripts/export_*.py + tests/** + always): scope-auditor +
> analytics-engineer-reviewer + cto-reviewer — all PASS.

diff_sha256: b58102611b931eb2db23927dbbfe60528cf9a99440bba72d54e00bb610242101

## scope-auditor
VERDICT: PASS
risks_checked:
- Amendment legitimacy: the clean-tree amendment adds docs/site_architecture.md + docs/ui_design_brief.md to scope on the analytics-engineer FAIL authority; proportionate (one-token mart_top_scorers -> mart_leaderboards reference fixes, no content drift); every edit is within the amended scope_paths.
- Grain enforcement post-consolidation: mart_leaderboards' (player_sk, season_sk, metric_key) unique key is dbt-tested; rank locked 1-10; metric_key locked to the 9 catalogued boards (accepted_values); an upstream change that breaks cardinality or adds an uncatalogued board is caught by CI.
- No §10 regression: the diff materialises only the pre-approved decisions (LONG shape, 9 count boards, full consolidation, drop the 3 profile rank columns); no new metric/mechanism/naming decision; PR 2a defined the metrics.

## analytics-engineer-reviewer
VERDICT: PASS
risks_checked:
- SELECT/YML column parity for the 3 composites (round-1 finding 1): scorer_points / defensive_actions / cards_total are now in base, in the final SELECT, in every UNION ALL branch via base.*, in shared.yml's mart_leaderboards columns, and in the export _LB_KEEP — the documented column set == the SELECT column set (no undocumented column, none documented-but-absent).
- Retired-model reference hygiene (round-1 finding 2): zero live ref()/query string to mart_top_scorers or mart_player_season in models/ or scripts/; remaining occurrences are intentional "retired" docstring text; the export queries mart_leaderboards on both paths; the 3 docs updated to mart_leaderboards.
- No regression: grain unique, UNION ALL branches aligned (base.* carries the 3 added columns uniformly), the dim_player LEFT join does not fan out, tests intact.

## cto-reviewer
VERDICT: PASS
risks_checked:
- KeyError / projection safety on _LB_KEEP: the 3 new composites are present on mart_leaderboards rows and in _LB_KEEP; shape_leaderboards uses r.get(k) for every key, so a missing column yields None, not a crash; the boards dict is pre-seeded {m: [] for m in metrics} so the caller never hits a missing-key error.
- Consumption-layer compliance + stale-ref elimination: shape_leaderboards groups by metric_key and orders by the warehouse-supplied rank only (no Python ranking); zero remaining mart_top_scorers / scorer_rank / *_rank references in the script or tests; test_shape_competition_payload_sorts_sections asserts s["rank"]; both export paths repointed to mart_leaderboards.

## escalations
(none)
