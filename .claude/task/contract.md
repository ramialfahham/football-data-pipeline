# Task contract — feat: metric direction + interpretation semantics (benchmark precursor, PR-a)

> PR-a of the team competition-benchmark build (CPO-directed 2026-06-19). The semantic precursor:
> give every TEAM metric a `direction` (higher_better / lower_better / neutral) and a short
> `interpretation`, so the data carries meaning — orienting the benchmark and powering future
> auto-narrative. Catalogue-only; no models, no benchmark mart (that is PR-b). Precursor pattern
> (like #507 → #508).

objective: >
  Add two columns to metric_catalogue.csv — `direction` (enum: higher_better / lower_better / neutral)
  and `interpretation` (short meaning string) — and populate them for ALL team metrics per the
  CPO-agreed classification. `direction` is the richer successor to the binary `lower_is_better` (which
  is RETAINED for now; full migration + player rows are v1.x). Drop NO rows. Player-metric direction +
  interpretation are deferred to the player benchmark (v1.x), so player rows leave the two new fields
  empty.

refs: team competition-benchmark design (this conversation); deserved-vs-actual (content_architecture §6); metrics_display.md (team display contract); PR-b = the benchmark mart.

scope_paths:
  - dbt_project/seeds/metric_catalogue.csv
  - dbt_project/seeds/schema.yml
  - .claude/task/contract.md
  - .claude/task/review.md

decisions_taken: >
  CPO-directed (2026-06-19): benchmark team-first; classify ALL team metrics with direction +
  interpretation (decouples "what we have" from "what we show"). The agreed team classification:
  higher_better = goals_per_match, clean_sheets, shots_per_match, shot_accuracy, danger_zone_ratio,
  shots_on_target_per_match, finishing_efficiency, duels_won_pct, pass_accuracy, key_passes_per_match,
  save_ratio, shot_share, points_capture, points_won; lower_better =
  goals_against_per_match, league_rank; neutral = duels_per_match, defensive_actions_per_match,
  tackles_per_match, interceptions_per_match, blocks_per_match, passes_per_match, corner_kicks_per_match,
  corners_conceded_per_match. The corners pair was RECLASSIFIED to neutral (overrides the old
  lower_is_better=true on corners_conceded — weak signal). interpretations per the agreed meanings
  (defensive_actions reworded: "deep block OR aggressive press"). `direction` supersedes
  `lower_is_better` where they differ (corners). dribbles_success_pct,team is NOT classified here (its
  two new fields stay empty) — it is a PLAYER metric ruled dropped team-side (2026-06-11) with no
  conventional team meaning; slated for full retirement (catalogue row + the leftover
  mart_momentum__team computation) in #510. Corrected from an earlier mis-call to keep it. No deletion in PR-a.

decisions_reserved:
  - Player-metric direction + interpretation = v1.x (the player benchmark) — player rows' two new fields
    stay empty here; do NOT mechanically guess them.
  - Team dribbles_success_pct full retirement (catalogue row + the leftover mart_momentum__team
    computation/test) = #510, done AFTERWARDS. Leave its row + two new fields untouched here.
  - Retiring `lower_is_better` entirely = a v1.x cleanup once all rows are on `direction` and consumers
    migrate. Keep it now.
  - The benchmark mart (`mart_competition_benchmarks__team`) + the 4 season-model metric additions
    (clean_sheets rate + tackles/interceptions/blocks per match) = PR-b. Nothing here.
  - If a catalogue consumer reads `lower_is_better` positionally and a new column would break it, STOP —
    but the export uses csv.DictReader (reads by name), so new columns are safe.

done_when:
  - metric_catalogue.csv has `direction` + `interpretation` columns; every STAYING team row populated
    (direction ∈ {higher_better, lower_better, neutral}; interpretation non-empty); dribbles_success_pct,team
    + all player rows' two new fields empty; NO row deleted; `lower_is_better` retained.
  - seeds/schema.yml documents both new columns; `direction` accepted_values [higher_better, lower_better,
    neutral] (null allowed for the not-yet-classified player rows); seed still loads.
  - `dbt parse` clean; the metric_catalogue seed tests (incl. assert_metric_catalogue_unique_by_entity)
    still pass; no CSV field-count break (quote any interpretation containing a comma).
  - reviewers: scope-auditor + analytics-engineer-reviewer + football-analytics-expert-reviewer PASS.

amendments: (none)
