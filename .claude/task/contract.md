# Task contract — chore: remove the black-box player rating end-to-end

> CPO 2026-06-18: API-Football's per-player match `rating` is a vendor black box (opaque formula, can't be
> formula-verified, variable coverage). Decision: we don't carry it at all. Remove it end-to-end —
> ingestion → core fact → intermediate legs → the two marts that display it → the season aggregate
> (`rating_avg`) → doc mentions. Precursor to the metric-layer Phase 1 PR: keeps that PR's review
> boundaries clean and gives Phase 1 a rating-free base. Footprint is dbt + docs ONLY — verified by repo
> grep: NO site/, scripts/, i18n, or test references.

objective: >
  Drop the player `rating` field and its season aggregate `rating_avg` from the whole dbt chain and the
  docs that describe them, so nothing computes or surfaces the vendor rating. No behavioural change beyond
  the field's removal; no other column added, removed, or renamed.

refs: >
  This conversation 2026-06-18 (rating is a black box → remove entirely; precursor to metric-layer Phase 1).
  Footprint confirmed via repo grep: dbt models + core.yml/shared.yml + 3 docs; NO site/, scripts/, i18n,
  or tests references.

scope_paths:
  - dbt_project/models/1_staging/api_football/stg_apif__fixture_players.sql
  - dbt_project/models/2_base/api_football/base_apif__fixture_players.sql
  - dbt_project/models/3_core/fct_fixture_player_stats.sql
  - dbt_project/models/3_core/core.yml
  - dbt_project/models/4_intermediate/shared/int_legs__player_match.sql
  - dbt_project/models/4_intermediate/domestic_league/team_season/int_player_season__metrics.sql
  - dbt_project/models/5_marts/shared/mart_player_match_log.sql
  - dbt_project/models/5_marts/shared/mart_fixture_stats__player.sql
  - dbt_project/models/5_marts/shared/mart_player_season.sql
  - dbt_project/models/5_marts/shared/shared.yml
  - docs/wireframes/03_player_profile.md
  - docs/ui_design_brief.md
  - docs/api_football_ingestion_blueprint.md
  - .claude/task/contract.md
  - .claude/task/review.md

decisions_taken: >
  CPO 2026-06-18: remove the API-Football player rating ENTIRELY (it is a black-box metric). Confirmed
  product-wide, not just the season aggregate: the per-match rating shown in mart_player_match_log and
  mart_fixture_stats__player goes too. Done as its own precursor PR before the metric-layer Phase 1 work
  (1(a) binding-map; 2(rec) full_season_metrics) so the ingestion/display removal stays out of that PR.

decisions_reserved:
  - Touch ONLY rating / rating_avg. No other fields, no refactors, no metric_catalogue change (rating is
    not catalogued). No metric-layer mechanism here (that is Phase 1).
  - Removing a core-fact column changes downstream mart schemas — but ONLY the rating column; no other
    output column may change. If any consumer beyond those listed surfaces rating, STOP and surface it.

done_when:
  - `rating` is gone from staging -> base -> fct_fixture_player_stats -> int_legs__player_match -> the two
    fixture-grain marts; `rating_avg` gone from int_player_season__metrics + mart_player_season; the yml
    docs (core.yml, shared.yml) and the 3 docs no longer describe either.
  - No remaining whole-word `rating` reference in dbt_project/ or docs/ (excluding unrelated words).
  - dbt parse + sqlfluff lint green (validate-local). No other column added/removed/renamed.
  - reviewer: data-engineer PASS + analytics-engineer PASS + scope-auditor PASS (>=2 named risks each);
    no FAIL; no ESCALATE.
  - Branch chore/drop-player-rating; PR opened (CPO merges). Then resume metric-layer Phase 1 on the
    rating-free base.

amendments: (none)
