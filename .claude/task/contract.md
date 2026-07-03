# Task contract — Phase C brick 1: player year-over-year (int_player_profile__yoy)

> Written on a CLEAN tree (branch feat/player-profile-yoy off main @ baef982).
> First Phase C brick: the PLAYER mirror of the shipped team YoY (int_team_profile__yoy, #324/#606). dbt-only.
> Backfill confirmed done this session (careers 5-10 seasons deep in mart_player_career) → YoY is meaningful.

objective: >
  Build int_player_profile__yoy (the player analog of int_team_profile__yoy) + compose it into
  mart_player_profile, so the player profile carries "this season vs last, at the same appearance count"
  deltas for goals / assists / shots_on_target / key_passes / defensive_actions (the CPO metric set,
  AskUserQuestion 2026-07-03 "broader per-position set"). Domestic-leagues only, appearance-aligned, per-club
  grain, attached via the player's primary club. Auto-carries to the v2 player export via select * (the team
  A1/#606 precedent); a YoY SCREEN is a later wireframe gap.
refs: #391 Phase C brick 1; #480 §8 (player-season analogs); mirrors #324/#606 (team YoY)

scope_paths:
  - dbt_project/models/4_intermediate/shared/int_player_profile__yoy.sql
  - dbt_project/models/4_intermediate/shared/int_player_profile.yml
  - dbt_project/models/5_marts/shared/mart_player_profile.sql
  - .claude/task/**

impact_map: >
  writers: NEW int_player_profile__yoy (4_intermediate/shared, materialized=table) reads
    int_player_season_record (per-club appearance-cumulative; its header: "Carries ... match_number for the
    deferred year-over-year surface") + competition_registry (seed). Exact mirror of int_team_profile__yoy.
    mart_player_profile.sql gains a `yoy` CTE + a left join + the YoY output columns.
  downstream: int_player_profile__yoy -> mart_player_profile (the ONLY consumer) -> the v2 player export
    (scripts/export_site_data.py:588 `select * from mart_player_profile` — auto-carry, NO export edit).
    dbt ls is CI-only locally; ref-graph cited from the files (Grep: only mart_player_profile will ref it).
  layer_rules: intermediate = table, preparation for marts, may NOT ref mart_* (layering.md L15/L51) —
    this model reads one int + one seed only, compliant. `python scripts/check_layer_contract.py` passes offline.
  deploy_order: ADDITIVE only — a NEW model + NEW nullable columns on mart_player_profile (a full-refresh
    table, not incremental). No rename/drop; historical rows unaffected. ci-data-build (dbt_analytics) builds
    it in isolation; prod = the 04:00 scheduled run. No shared-warehouse migration hazard.
  blast_radius: mart_player_profile gains ~17 NEW YoY columns (5 metrics x this/prev/delta + yoy_appearances_cutoff
    + appearances_prev); EXISTING mart columns/numbers UNCHANGED. The player export payload gains those columns
    via select *. No other mart or number changes. The drift guard (assert_no_uncatalogued_season_metric) is
    unaffected — YoY is a profile/differentiator model, not the season-metrics rollup (like int_team_profile__yoy).

decisions_taken: >
  Metric set = goals / assists / shots_on_target / key_passes / defensive_actions (CPO AskUserQuestion
  2026-07-03). defensive_actions = tackles_total + tackles_interceptions + tackles_blocks (the T+I+B aggregate,
  GAP-11). Grain (team_sk, player_sk, league_code, season_api_year); appearance-aligned (match_number = the
  player's appearance number; current season through N vs the prior season's first N); domestic-leagues only;
  deltas NULL when no prior season (transfer/first year) — an EXACT mirror of int_team_profile__yoy. Composed
  into mart_player_profile via the primary club (ta.team_sk from int_player_season__team / GAP-16), so the
  profile carries the player's main-club YoY (only the latest season per club-league matches; older seasons
  get NULL — mirrors the team). Tests (int_player_profile.yml): unique_combination(grain) + not_null(keys +
  cutoff) + relationships player_sk->dim_player, team_sk->dim_team (a safe superset of int_team_profile.yml,
  which has unique+not_null only). Auto-carry to the export via select * (no export edit; #606 precedent).

decisions_reserved:
  - The rare same-league two-club-in-one-season case surfaces the primary club's YoY only (documented honest
    limit in the model header) — an accepted engineering trade-off, not a CPO question.
  - A YoY SCREEN (wireframe + explicit export shaping) is a later gap, not this brick.
  - Brick 2 (player streaks) + season models are separate later PRs.
  - All §10 unchanged; the metric set is the only product decision and it is locked above.

done_when:
  - int_player_profile__yoy builds; grain unique; keys + cutoff not_null; relationships hold; ci-data-build green.
  - mart_player_profile gains the YoY columns; EXISTING numbers unchanged; drift guard unaffected.
  - python scripts/check_layer_contract.py passes.
  - bq spot-check: a long-tenured player (2+ seasons one league) has *_delta_yoy = cur - prev through the
    aligned cutoff, and NULL for a first-season/transfer case.
  - scope-auditor + analytics-engineer-reviewer PASS (>=2 named risks each); review.md binds; CPO merges.

amendments: (none)
