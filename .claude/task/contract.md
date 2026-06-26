# Task contract — #500 PR-c: crown the metric-definition SSoT (seed); retire the competing prose doc

> Governance G2/G3 contract. Written on a clean tree BEFORE any edit.
> Docs + provenance-comment consolidation; ZERO metric logic/formula change.

objective: >
  Make the single source of truth for metric definitions unambiguous (the agent kept drifting
  because several docs each claimed to define metrics). Crown the `dbt_project/seeds/metric_catalogue.csv`
  seed as THE definition SSoT in `docs/metric_layer.md` (which becomes the one map/index), DELETE
  the competing claimant `docs/player_metrics_catalogue.md` (it specs the retired
  mart_matchday_player_insights, #321), add a one-line deferral header to the other metric docs,
  repoint every reference to the retired doc to the seed, and clear the deferred #577 + #574
  old-name doc debt. No metric definition/formula/logic changes anywhere.
refs: #500 (PR-c); follows #574 (team renames) + #577 (player renames); CPO-approved plan 2026-06-26.

scope_paths:
  - docs/metric_layer.md
  - docs/player_metrics_catalogue.md
  - docs/wireframes/metrics_display.md
  - docs/metrics_context_model.md
  - docs/content_architecture.md
  - docs/site_architecture.md
  - docs/wireframes/99_gaps_register.md
  - docs/wireframes/01_fixture_page.md
  - dbt_project/docs/layering.md
  - dbt_project/models/4_intermediate/domestic_league/team_season/int_player_season__metrics.sql
  - dbt_project/models/4_intermediate/domestic_league/team_season/int_team_season.yml

impact_map: >
  writers: none — the two `dbt_project/models/**` touches change only a code comment
    (int_player_season__metrics.sql ~L13) and a yml description (int_team_season.yml ~L74, which
    documents the int_player_season__metrics model), both repointing a retired-doc reference
    ("Atoms follow docs/player_metrics_catalogue.md") to the metric_catalogue.csv seed. The
    compiled SQL of every model is byte-identical; no table content changes.
  downstream: EVIDENCE — `.venv/Scripts/dbt ls --project-dir dbt_project --resource-type model
    --select int_player_season__metrics+` (run 2026-06-26 on this branch) →
    int_player_career__metrics, mart_leaderboards, mart_player_career, mart_player_profile.
    None are affected (comment/description only).
  layer_rules: none triggered — no model added/moved/rematerialised, no metric column
    added/renamed; check_layer_contract + the no-drift season-metric guard are unaffected.
  deploy_order: none — comment/description-only; compiled SQL unchanged → no rebuild, no break
    to the deployed model; safe at any time vs the 04:00 nightly. The rest of the PR is docs only.
  blast_radius: none — zero compiled-SQL change; no mart/number changes anywhere.

decisions_taken: >
  CPO-approved plan (2026-06-26): the seed is THE metric-definition SSoT; `player_metrics_catalogue.md`
  is retired (deleted); `metric_layer.md` becomes the map; `metrics_display.md` (CPO-locked #391)
  and `metrics_context_model.md` are KEPT with a one-line deferral header; all references to the
  retired doc repoint to the seed; the #577/#574 old-name doc debt is cleared in the same PR.

decisions_reserved:
  - metrics_display.md is a CPO-LOCKED contract — edits are pointer-only (repoint dead-doc
    references + the deferral header + one stale model name); every ruling is preserved VERBATIM.
    If any reword would touch a ruling, stop and escalate (§11) — do not.
  - Seed `metric_catalogue.csv` description enrichment (provider-semantics nuances) is OUT of scope
    here → a separate football-analytics-expert-reviewed follow-up. (The pass-accuracy rounding
    caveat already lives in the int_player_season__metrics comment, so nothing is lost on deletion.)

done_when:
  - `.venv/Scripts/dbt parse` clean (docs/comment/description changes; the model graph is untouched).
  - Repo grep returns ZERO: (a) any remaining `player_metrics_catalogue` reference; (b) any old
    mart name `mart_momentum__player|mart_season_record__player|mart_momentum__team|mart_season_record__team`.
  - No data rebuild (no model logic/formula touched).
  - Routes to scope-auditor (always) + analytics-engineer-reviewer (dbt_project/**) +
    bi-analyst-reviewer (wireframes/display contract). 4-step review cycle → commit gate. CPO merges.

amendments: (none)
