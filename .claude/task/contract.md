# Task contract — #530(a): split the 2 entity-dual metric_catalogue rows

> Written on a CLEAN tree (branch feat/530a-split-entity-dual-metrics off main @ 521be4a).
> Catalogue-only (seed CSV + its schema.yml prose). No structural surface touched.
> See docs/working_agreement.md §2 (contract), §10 (decision rights), §11 (escalation).

objective: >
  Split the two entity-dual metric_catalogue rows (finishing_efficiency, duels_won_pct — entity
  "team and player", blank base_relation/numerator_expr/denominator_expr) into per-entity rows with
  explicit, resolvable formulas, closing the one coverage gap in assert_metric_catalogue_expr_resolvable
  (it skips blank-base rows). CPO-approved option (iii): ship everything resolvable now; park player
  finishing_efficiency as a blank-base deferred row for follow-up (b) (player goals_penalty leg).

refs: >
  #530(a). CPO sign-off this chat (2026-06-29): option (iii) + player rows null
  direction/interpretation/importance_tier per the v1.x player convention. Plan approved
  (whimsical-swinging-mccarthy.md). Follows #600 (the integrity guards this fills).

scope_paths:
  - dbt_project/seeds/metric_catalogue.csv
  - dbt_project/seeds/schema.yml
  - .claude/active_work.md
  - .claude/task/**

# No impact_map: no raw writer, dbt model, or consumption path in scope. metric_catalogue.csv is a
# seed (configuration), schema.yml is its doc/test config. No model SQL changes; no warehouse migration.

decisions_taken: >
  Rests on the CPO's in-chat sign-off of the exact per-entity rows + option (iii) sequencing + the
  player-row null convention. Formulas are pure math per the standing formula-vs-availability ruling
  (no coalesce/countif/null-gate in any *_expr; "Null when…" stays in description prose only). Both
  metrics keep their existing label_i18n_key on both entity rows — no new i18n keys (out of scope).

decisions_reserved:
  - Player finishing_efficiency formula APPLICATION (sum(goals_total - goals_penalty)/sum(shots_on))
    waits on #530(b) adding the event-derived goals_penalty atom to int_legs__player_match — this row
    ships blank-base/deferred only. Do NOT add the player goals_penalty leg here (separate PR).
  - Player direction/interpretation classification stays deferred (v1.x player benchmark) — not in scope.

done_when:
  - metric_catalogue.csv: duels_won_pct → team (int_legs__team_from_players) + player
    (int_legs__player_match), both sum(duels_won)/sum(duels_total); finishing_efficiency → team
    (int_legs__team_match, sum(goals_for - goals_penalty - goals_own)/sum(shots_on_goal)) + player
    (blank base/exprs, deferred to (b)). The merged "team and player" rows are removed.
  - schema.yml prose updated: drop the "entity-dual split per entity" wording; fold
    finishing_efficiency into the deferred-player-rows list with goals_penalty/goals_open_play.
  - Offline: scratchpad python confirms every row has 14 fields + the 3 new resolvable rows tokenize
    clean against their model columns; `python scripts/check_layer_contract.py` green.
  - CI ci-data-build green (assert_metric_catalogue_expr_resolvable, assert_team_metric_meaning_complete,
    assert_metric_catalogue_unique_by_entity, base_relation accepted_values).
  - scope-auditor + analytics-engineer + football-analytics-expert PASS (>=2 risks each); review.md
    diff_sha256 binds the staged diff; CPO merges (never self-merge).

amendments: (none)
