# Task contract — #530(b): fix the player catalogue-integrity gap (finishing_efficiency + duels_won_pct)

> Written on a CLEAN tree (branch fix/530b-player-catalogue-integrity off main @ ee4eb98).
> dbt MODEL + CATALOGUE change (NOT doc-only). Fixes the two player benchmark metrics whose
> metric_catalogue rows are incomplete, surfaced while spec'ing the Player Stats screen (#391).
> See docs/working_agreement.md §2 (contract), §10 (decision rights). Plan mode + ExitPlanMode required.

objective: >
  The player competition benchmark (mart_player_competition_benchmarks, #559) ranks 18 metrics, but two
  have incomplete metric_catalogue (entity=player) rows: (1) `finishing_efficiency` — numerator_expr,
  denominator_expr, base_relation, direction ALL blank (its VALUE is computed in
  int_player_season_position__metrics via an events-derived penalty component, but the catalogue — the
  SSoT — doesn't define it, because penalty goals is not an atom on the player leg); (2) `duels_won_pct` —
  fully defined (num `duels_won`, denom `duels_total`) but `direction` blank. CPO ruled both
  `higher_better` (2026-07-02). Fix = make the catalogue rows complete + resolvable, single-sourcing the
  penalty atom. This is the tracked #530(b) follow-up.

refs: >
  Season formula (CPO Option A, int_player_season_position__metrics.sql:152-159): finishing_efficiency =
  (goals − goals_penalty) / shots_on_goal (capped to [0,1] at the model; the cap is availability handling,
  NOT part of the formula — per [[feedback-metric-formula-vs-availability]]). goals_penalty is event-derived
  (fct_fixture_event: event_type='Goal' and event_detail='Penalty') — today via a local events CTE in the
  season model. Team analog already catalogued: finishing_efficiency (entity=team) base=int_legs__team_match,
  num=sum(goals_for − goals_penalty − goals_own), denom=sum(shots_on_goal), direction=higher_better.
  int_legs__player_match = materialized TABLE (no incremental full-refresh concern), grain (fixture_sk,
  player_sk), has goals_total + shots_on but NOT goals_penalty.

impact_map: >
  CHANGED: (1) int_legs__player_match — ADD an event-derived `goals_penalty` column (additive; the leg is
  "the shared foundation every player metric aggregates over", so the atom belongs here). (2)
  metric_catalogue.csv — fill finishing_efficiency (player): base_relation=int_legs__player_match,
  num=sum(goals_total − goals_penalty), denom=sum(shots_on), direction=higher_better, lower_is_better=false;
  set duels_won_pct (player) direction=higher_better (+ lower_is_better=false). (3) dbt_project/seeds/schema.yml
  — the seed's own governing doc lists finishing_efficiency among "the deferred player rows pending
  int_legs__player_match exposing the penalty atom"; drop finishing_efficiency from that enumeration (now
  filled) + correct the phrasing (the atom now exists); goals_penalty/goals_open_play stay listed (still
  blank). NO int_legs.yml change — it documents only keys + enum columns; leg raw-count atoms (goals_total,
  shots_on, the team leg's own goals_penalty) carry NO per-column entry, so a goals_penalty entry/test would
  break convention (and a non-negativity test on a coalesced countif is trivially always true). NOT CHANGED:
  int_player_season_position__metrics (Option Y — it keeps its own identical penalty derivation; repointing
  it to the leg is a bigger/riskier refactor, deferred).
  UPSTREAM: fct_fixture_event, fct_fixture_player_stats (read-only). DOWNSTREAM of the leg: additive column,
  backward-compatible for all consumers (int_player_season_position__metrics, int_player_competition_benchmarks,
  momentum). CI guards: assert_metric_catalogue_expr_resolvable will now CHECK the finishing row (was skipped
  while base blank) → the new exprs must resolve against the leg; assert_no_uncatalogued_season_metric
  unaffected (finishing_efficiency already an output column + catalogued). Verified by ci-data-build (dbt
  build + DQ) — dbt CLI broken locally. No export/site/live-MVP change.

scope_paths:
  - dbt_project/models/4_intermediate/shared/int_legs__player_match.sql
  - dbt_project/seeds/metric_catalogue.csv
  - dbt_project/seeds/schema.yml
  - .claude/task/**

decisions_taken: >
  Complete the two player catalogue rows to match the already-computed reality + the CPO direction ruling
  (both higher_better). Add the penalty atom to int_legs__player_match (additive column) so the catalogue's
  leg-based finishing formula resolves — mirroring the team finishing row. The season model is LEFT
  UNCHANGED (Option Y): finishing value is unchanged; the season model's own penalty derivation stays (a
  pre-existing duplication, flagged as a follow-up, not consolidated here — scope discipline). numerator/
  denominator exprs are the PURE formula (no cap/coalesce — the [0,1] cap stays model-side availability
  handling). No new metric invented; no export/UI change; the Player Stats wireframe (parked) resumes after.

decisions_reserved:  # §10
  - The finishing_efficiency player NUMERATOR semantics (goals − penalty goals, "open-play", Option A) are
    ALREADY CPO-ruled + computed; this only mirrors them into the catalogue. If football-analytics review
    finds the mirror misstates the formula, escalate — do not re-derive.
  - Whether to also fill the other #530(b) deferred rows (goals_open_play etc.) — OUT of scope; only the two
    benchmark-blocking metrics here.

done_when:
  - metric_catalogue finishing_efficiency (player) + duels_won_pct (player) rows complete + resolvable;
    goals_penalty on int_legs__player_match; season model single-sourced (finishing value unchanged).
  - scope-auditor + analytics-engineer + football-analytics(-expert) PASS (>=2 risks each); ci-data-build
    green (resolvability guard + DQ); review.md diff_sha256 binds; CPO merges.

amendments:
  - 2026-07-02 (plan-back, pre-code): dropped int_player_season_position__metrics from scope — Option Y
    (leave the season model; add the atom to the leg only). Adjusted impact_map + decisions_taken. Season
    model single-sourcing repoint deferred as a flagged follow-up.
  - 2026-07-02 (mid-implement): dropped int_legs__player_match.yml from scope — int_legs.yml documents only
    keys + enums, not leg raw-count atoms, so goals_penalty gets no per-column entry (matches goals_total /
    shots_on / the team leg's goals_penalty). No yml change.
  - 2026-07-02 (review round 1, analytics-engineer FAIL): added dbt_project/seeds/schema.yml to scope — the
    seed's own governing doc still listed finishing_efficiency as a deferred/blank row; completing the CSV
    row without updating schema.yml left the catalogue SSoT internally inconsistent. Drop finishing_efficiency
    from the deferred enumeration; goals_penalty/goals_open_play stay (still blank).
