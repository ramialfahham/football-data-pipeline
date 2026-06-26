# Task contract — #500 PR2-player: entity-first renames of the 4 player momentum/season models

> Written on a clean tree BEFORE any edit. See docs/working_agreement.md §1, §2, §10;
> plan C:\Users\Rami\.claude\plans\quiet-meandering-lerdorf.md (CPO-approved).

objective: >
  Finish the entity-first naming mirror of #574 (team) on the PLAYER side. Pure rename of
  four models — int_momentum__player -> int_player_momentum__metrics; int_season_record__player
  -> int_player_season_record; mart_momentum__player -> mart_player_momentum;
  mart_season_record__player -> mart_player_season_record — plus the ref()s, the player-half yml
  entries, in-file comment cross-refs, and the v2 export reference. ZERO logic/number change.
refs: #500 PR2; CPO ruling 2026-06-26 (both recommended options confirmed); plan quiet-meandering-lerdorf.

scope_paths:
  - dbt_project/models/4_intermediate/shared/int_momentum__player.sql
  - dbt_project/models/4_intermediate/shared/int_player_momentum__metrics.sql
  - dbt_project/models/4_intermediate/shared/int_season_record__player.sql
  - dbt_project/models/4_intermediate/shared/int_player_season_record.sql
  - dbt_project/models/5_marts/shared/mart_momentum__player.sql
  - dbt_project/models/5_marts/shared/mart_player_momentum.sql
  - dbt_project/models/5_marts/shared/mart_season_record__player.sql
  - dbt_project/models/5_marts/shared/mart_player_season_record.sql
  - dbt_project/models/4_intermediate/shared/int_momentum.yml
  - dbt_project/models/4_intermediate/shared/int_season_record.yml
  - dbt_project/models/5_marts/shared/shared.yml
  - scripts/export_site_data.py

impact_map: >
  writers: each of the 4 models is its own single SELECT (one writer each); no other model writes them.
  downstream (EVIDENCE — `dbt ls --select int_momentum__player+ int_season_record__player+
    mart_momentum__player+ mart_season_record__player+ --resource-type model`, run 2026-06-26 on this
    branch off main, dbt=1.7.19, 88 models): the closure is EXACTLY the four models themselves —
      4_intermediate.shared.int_momentum__player
      4_intermediate.shared.int_season_record__player
      5_marts.shared.mart_momentum__player
      5_marts.shared.mart_season_record__player
    i.e. each int feeds ONLY its own mart; both marts are LEAF (no dbt model downstream). The only
    non-dbt consumer is scripts/export_site_data.py (the PAUSED v2 export), which reads
    mart_momentum__player at line ~193 (comment) + ~437 (query) — confirmed by grep; it does NOT read
    mart_season_record__player or either int builder. The LIVE match-preview build
    (build_match_preview_site.sh + extract_preview_json.py + export_pages_data.py) reads NONE of them.
  layer_rules: ints stay in 4_intermediate/shared, marts in 5_marts/shared (no layer move);
    no per-competition staging touched (check_layer_contract unaffected); each model's
    config(materialized=…) is preserved (3 tables + mart_season_record=view); a yml `name:` must
    match its model or `dbt parse` fails (so the 3 yml renames are mandatory, not optional).
  deploy_order: shared BigQuery. The renamed models build fresh under the new names; the 4 OLD-named
    relations become orphaned (mirrors #574) -> pending CPO `bq rm` (deny-listed):
    intermediate.int_momentum__player, intermediate.int_season_record__player,
    marts.mart_momentum__player, marts.mart_season_record__player. NONE are incremental ->
    no --full-refresh needed. ci-data-build (state:modified+) builds the renamed set on the PR.
  blast_radius: NONE — pure rename, no formula/grain/column change. Numbers byte-identical by
    construction; verified new-vs-prod on both marts (grain upcoming_fixture_sk, team_sk, player_sk),
    expect 0 mismatches; the two builders are literal 1:1 copies (compile-only). Live MVP untouched
    (no live consumer); the v2 export emits the same data from the renamed source.

decisions_taken: >
  CPO ruling 2026-06-26 — both recommended options confirmed: (1) rename all FOUR models incl.
  int_season_record__player -> int_player_season_record (finish the mirror; the team halves were
  renamed in #574). (2) RENAMES ONLY — no formula-dedup, no new model, no macro. The two player
  season models legitimately do NOT merge (int_player_season__metrics is per-(player,season) across
  clubs + per-90s; the season-record path is per-(team,player,league,season)); all three ratio sites
  are different grains, so the 4 ratios stay INLINE in both marts (as mart_team_momentum keeps its
  own). MVP-safe: only the paused v2 export reads these. No product/metric/§10 decision introduced.

decisions_reserved:
  - None new — this renames CPO-confirmed names with zero logic change. (Stale old-name mentions in
    layering.md / site_architecture.md / active_work.md are DEFERRED to the doc-consolidation PR-c per
    the CPO scope list — not touched here. The orphaned old BQ tables are a CPO `bq rm` action.)

done_when:
  - `.venv/Scripts/dbt parse` + `dbt compile` clean (88 models; all renamed ref()s resolve).
  - sqlfluff clean on the 4 renamed model files.
  - New-vs-prod byte-identical check: 0 mismatches on mart_player_momentum vs prod mart_momentum__player
    AND mart_player_season_record vs prod mart_season_record__player (FULL OUTER JOIN on the grain).
  - Required reviewers PASS: scope-auditor + analytics-engineer-reviewer (dbt_project/**) +
    cto-reviewer (scripts/export_*.py). CPO merges — never self-merge.

amendments: (none)
