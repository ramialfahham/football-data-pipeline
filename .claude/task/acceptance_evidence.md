# Verification — player metric directions

criteria_demonstrated:
  - `metric_catalogue.csv`: appearances, minutes_per_appearance and contribution_player_pct read `higher_better`; their interpretations end without "not good or bad" (contribution keeps "(position-dependent: a defender's share is naturally low)"). A cell-by-cell comparison with main shows no other cell changed.
  - `seeds/schema.yml`, the `direction` description: "`neutral` is reserved for a metric with genuinely no better/worse pole, such as a narrative gap."
  - No served value changes: `direction` is read in SQL only by the two team marts (team rows), by `export_metric_definitions_json.py` only as `lower_better`, and by the export's metric rows (team rows); none of the three metrics is in the player benchmark set. The glossary export (`metrics.json`, every catalogue row) carries the three rows' new `direction` and `interpretation`; the deploy does not export it and no page reads it.
  - `docs/wireframes/11_team_squad.md` no longer states a direction for minutes per appearance.

dbt parse passes. pytest: 1,619 passed, 2 skipped. The site's node tests: 152 pass. The fast offline
gates pass: layer contract, registry sync, competition type seed, UI metric labels, copy gate,
description hygiene.
