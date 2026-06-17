# Task contract — feat: consolidate player-season aggregation (#480, narrow scope)

> CPO-directed this conversation (2026-06-17), NARROW scope chosen. Consolidates the three overlapping
> player-season aggregations onto one shared intermediate model, applying the catalogue-correct
> (weighted) pass-accuracy and removing the duplicated inline rollups. Builds on metrics_context_model.md
> §8 (the player performance surface, merged #491). Read-only verification this session established the
> blast radius: `mart_player_season` feeds ONLY `mart_top_scorers` (goals/assists/etc. — NOT pass
> accuracy or rating); the export does not read `mart_player_season`. So its `pass_accuracy_avg_percent`
> + `rating_avg` are currently UNCONSUMED — the avg→weighted fix is a latent-correctness change to an
> unconsumed column, not a live/v2 surface change. `mart_player_profile` is already weighted, so it stays
> byte-identical. Reviewers: scope-auditor (always) + analytics-engineer-reviewer (dbt). Numbers: no
> consumed number changes; the weighted pass-accuracy already matches the catalogue + football-analytics's
> spec-review sign-off.

objective: >
  One shared player-season aggregation; both marts consume it; fix the divergent pass accuracy; remove
  duplication. Keep today's grain (per player-competition-season). DEFER the per-club grain, this/last
  side-by-side, and the appearance block (the full §8.3 model) to a follow-up.
  (a) `dbt_project/models/4_intermediate/domestic_league/team_season/int_player_season__metrics.sql`
      (MODIFIED, promoted from orphan to the canonical shared int): fix passes_accurate floor()->round()
      (catalogue-correct, matches mart_player_profile); add `league_sk` + `season_sk` (from fct_fixture);
      add the union of raw aggregates both marts need (starts, substitute_appearances, shots_total,
      rating_avg, + the existing catalogue counts); match mart_player_profile's computations exactly
      (coalesce(0) on counts; appearances = count(*); round-based passes_accurate) so the profile stays
      byte-identical. Grain unchanged: (player_sk, league_code, season_api_year) + league_sk/season_sk.
  (b) `dbt_project/models/5_marts/shared/mart_player_profile.sql` (MODIFIED): replace the inline `agg`
      CTE with a select from `int_player_season__metrics`; KEEP the dim_player identity join, the
      modal_position CTE, the leaderboard rank windows, and every output column + the surrogate key —
      output byte-identical.
  (c) `dbt_project/models/5_marts/shared/mart_player_season.sql` (MODIFIED): replace the inline `agg`
      CTE with a select from `int_player_season__metrics` (+ dim_player identity); preserve the consumed
      columns exactly (those mart_top_scorers reads); replace `pass_accuracy_avg_percent` (naive avg,
      0-100, unconsumed) with the weighted catalogue `pass_accuracy_pct` (0-1, matches profile). Keep
      rating_avg (unconsumed, preserved).
  (d) schema yml + tests: update the int_player_season__metrics doc/tests (new columns, grain unique
      test) and the mart yml entries for the changed mart_player_season column; keep the existing grain +
      relationship tests.

refs: >
  #480. This conversation 2026-06-17 (narrow scope). Foundation = metrics_context_model.md §8 (#491).
  Delta verified read-only: avg vs weighted pass accuracy diverges (mean 3.9pts, tail to 62pts); the
  weighted value already lives in mart_player_profile.pass_accuracy_pct.

scope_paths:
  - dbt_project/models/4_intermediate/domestic_league/team_season/int_player_season__metrics.sql
  - dbt_project/models/4_intermediate/domestic_league/team_season/int_team_season.yml
  - dbt_project/models/5_marts/shared/mart_player_profile.sql
  - dbt_project/models/5_marts/shared/mart_player_season.sql
  - dbt_project/models/5_marts/shared/shared.yml
  - .claude/task/contract.md
  - .claude/task/review.md

decisions_taken: >
  CPO (this conversation, 2026-06-17): (1) NARROW scope — consolidate the three rollups to one shared
  weighted int + fix mart_player_season's avg→weighted; DEFER per-club grain / side-by-side / appearance
  block to a follow-up. (2) Canonical pass accuracy = the catalogue weighted ROUND definition (already in
  mart_player_profile + the catalogue; football-analytics confirmed it in the §8 spec review). (3) Output
  preservation: mart_player_profile byte-identical; mart_player_season preserves consumed columns;
  mart_top_scorers unaffected. (4) The orphan int is PROMOTED (consumed by both marts), not deleted —
  "retire the orphan" is satisfied by it no longer being orphaned.

decisions_reserved:
  - DEFERRED to a follow-up (NOT here): per-club grain (transfers split), this/last side-by-side, the
    appearance/playing-time block — i.e. the full §8.3 model. Keep today's grain.
  - Do NOT move int_player_season__metrics to a new folder in this PR (folder cleanup is the separate
    naming-consistency pass) — promote it in place.
  - If reproducing mart_player_profile from the shared int yields ANY value drift (it must be
    byte-identical), STOP and reconcile — do not ship a silent profile-number change.
  - If a consumer of mart_player_season's pass_accuracy_avg_percent / rating_avg is found beyond
    mart_top_scorers + the export (already checked: none), STOP and escalate before renaming.
  - Any §10 (a shipped-output change to a CONSUMED surface, a grain change, a new mechanism) -> escalate.

done_when:
  - dbt parse clean; sqlfluff lint passes; check_layer_contract green.
  - int_player_season__metrics is consumed by BOTH marts; no inline player-season agg remains in either
    mart; passes_accurate uses round() (not floor()).
  - mart_player_profile output is byte-identical to main (verified by compiled-logic equivalence or a
    read-only before/after compare on key columns incl. pass_accuracy_pct, goals, appearances, ranks).
  - mart_player_season preserves the columns mart_top_scorers consumes; pass accuracy is now the weighted
    pass_accuracy_pct; mart_top_scorers compiles unchanged.
  - ci-data-build green (full BQ build + DQ tests), incl. the grain/relationship tests on all three models.
  - reviewers: scope-auditor + analytics-engineer-reviewer PASS (>=2 named risks each), no FAIL, every
    ESCALATE has a recorded CPO ANSWER.

amendments: (none)
