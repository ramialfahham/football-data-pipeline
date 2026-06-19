# Review — feat/leaderboard-metrics — 2026-06-19

> PR 2a of the split leaderboards build: 3 player-season COUNT composite metrics
> (scorer_points, defensive_actions, cards_total) computed in int_player_season__metrics + 3
> metric_catalogue rows. The count-board sort keys for mart_leaderboards (PR 2b). Round 2 of the
> cycle: round-1 football-analytics FAIL (cards_total second-yellow double-count undisclosed +
> window-label mismatch) resolved — CPO chose to keep cards_yellow + cards_red and DISCLOSE the
> behavior (option a), and the descriptions were made window-agnostic. Required reviewers for the
> staged paths (dbt_project/** + metric_catalogue.csv + always): scope-auditor + analytics-engineer
> + football-analytics-expert-reviewer — all PASS.

diff_sha256: f4363c00e16ed4aacce27b67820c487c7f3b978fe37f9582bf638a371816adeb

## scope-auditor
VERDICT: PASS
risks_checked:
- Uncatalogued-metric drift: the 3 composites are pure sums of existing catalogued atoms; the drift guard assert_no_uncatalogued_season_metric (CI-verified) requires each int-model metric column to be catalogued, and the 3 new catalogue rows (entity=player) register them. No uncatalogued creep.
- Shipped-number stability: mart_player_profile + mart_player_season select named columns (not *) from the int model, so the 3 added columns are invisible to them — no shipped number moves. The round-2 change is description-only.
- Scope containment: every edit is within scope_paths (int model SQL + metric_catalogue.csv + contract); no mart / export / consolidation work from PR 2b, no rate-board / floor work (deferred #506), leaked in.

## analytics-engineer-reviewer
VERDICT: PASS
risks_checked:
- BigQuery composite correctness: scorer_points / defensive_actions / cards_total reference columns of the aggregated CTE (goals, assists, tackles_total, tackles_interceptions, tackles_blocks, cards_yellow, cards_red — all present), not same-SELECT lateral aliases; no lateral-alias error.
- Drift guard + seed schema: the 3 columns normalize to themselves (no _season suffix, not goals_saves) and match the new catalogue rows (entity=player); rows pass the seed accepted_values (entity/format/metric_group) and assert_metric_catalogue_unique_by_entity (no collision with team defensive_actions_per_match).
- CSV integrity (round 2): the cards_total description now contains a comma and is double-quoted (RFC 4180) — the row still parses as 11 fields for the dbt seed loader; no field-count break; no structural change vs round 1.

## football-analytics-expert-reviewer
VERDICT: PASS
risks_checked:
- cards_total second-yellow double-count: the description now discloses that a second yellow is recorded by the provider as yellow=2 + red=1, so a two-yellow dismissal scores 3 ("total cards shown"); accurate (data: 1,867 fact rows at yellow=2/red=1) and sufficient for a reader to interpret the number. lower_is_better=false is a recorded CPO-reserved call, not a FAIL basis.
- Window-label mismatch: all 3 new descriptions are window-agnostic (no window claim), consistent with the seed's documented design ("Window-agnostic: metric IDs carry no window suffix"); the round-1 mismatch is gone.
- Formula correctness: scorer_points = goals + assists (standard goal contributions, no overlap), defensive_actions = T+I+B (mirrors the team metric, independently tracked components), cards_total = yellow + red (transparent) — all transparent count sums, no black-box index.

## escalations
- question: cards_total = cards_yellow + cards_red counts a second-yellow sending-off as 3 cards (the provider records it yellow=2, red=1; 1,867 fact rows). Keep yellow+red and declare it, rank the board by cards_yellow only, or use a disciplinary-points scheme?
  CPO ANSWER: option (a) — keep cards_total = cards_yellow + cards_red (semantics = "total cards shown") and disclose the second-yellow behavior in the description. (CPO, 2026-06-19, in-thread.)
