# Task contract — feat: player-season composite metrics (leaderboards precursor, PR 2a)

> PR 2a of the split leaderboards build (CPO-directed 2026-06-19). The metric precursor — like
> #499→#501: define the 3 count-composite metrics the upcoming `mart_leaderboards` (PR 2b) ranks
> by, in the canonical single source + the catalogue, FIRST. Purely additive — nothing consumes
> them yet, no shipped number changes.

objective: >
  Add 3 player-season COUNT composite metrics — scorer_points (goals + assists), defensive_actions
  (tackles + interceptions + blocks), cards_total (cards_yellow + cards_red) — computed once in the
  canonical int_player_season__metrics (the metric-layer single source) and registered in
  metric_catalogue. These are the new sort keys for the 9-count-board mart_leaderboards (PR 2b).
  All three are sums of existing catalogued atoms already aggregated in the model.

refs: leaderboards v1 design (this conversation); docs/metric_layer.md; deferred rate boards = #506; PR 2b = the mart + consolidation.

scope_paths:
  - dbt_project/models/4_intermediate/domestic_league/team_season/int_player_season__metrics.sql
  - dbt_project/seeds/metric_catalogue.csv
  - .claude/task/contract.md
  - .claude/task/review.md

decisions_taken: >
  CPO-directed (2026-06-19): leaderboards v1 = 9 COUNT boards; rate boards + finishing_efficiency +
  the floor DEFERRED (#506); composites computed in the int model "like the other metrics"; full
  consolidation is PR 2b. The 3 composites: scorer_points = goals + assists (group goals);
  defensive_actions = tackles_total + tackles_interceptions + tackles_blocks (group defending);
  cards_total = cards_yellow + cards_red (group discipline). format integer. Reuse the existing
  playerMetrics.* label keys (scorerPoints.label / defensiveActions.label / cards.label); i18n
  resolution in site/i18n is deferred until surfaced — the established convention (the #501 catalogue
  metrics also carry not-yet-resolved keys). No int yml column docs/tests added: the model documents
  only keys + ratio ranges, its many count atoms (goals, assists, tackles…) are undocumented there by
  pattern, and the catalogue is the metric glossary (metric_layer.md).

decisions_reserved:
  - mart_leaderboards + full consolidation (retire mart_top_scorers / mart_player_season, drop
    mart_player_profile's 3 rank columns, repoint both export paths) is PR 2b — NOTHING from it here.
  - finishing_efficiency + the 5 rate boards + the qualification floor are deferred (#506) — not here.
  - cards_total lower_is_better is set to false to match the existing cards_yellow / cards_red rows;
    if football-analytics wants true (cards are a negative), that is their call — record it.
  - If football-analytics disputes any composite's definition / numerator / group / label, record it.

done_when:
  - int_player_season__metrics computes scorer_points, defensive_actions, cards_total in the final
    select; `dbt parse` clean; sqlfluff lint passes on the model.
  - metric_catalogue.csv has the 3 rows (entity=player, format integer, groups goals/defending/discipline),
    each an 11-field row matching the seed schema.
  - The drift guard assert_no_uncatalogued_season_metric still passes (the 3 new int columns are now
    catalogued) — verified in ci-data-build (it queries the warehouse; not runnable offline).
  - mart_player_profile / mart_player_season are UNCHANGED (they select named columns, not *), so no
    shipped number moves.
  - reviewers: scope-auditor + analytics-engineer + football-analytics-expert-reviewer PASS
    (>=2 named risks each); no FAIL; no ESCALATE.

amendments: (none)
