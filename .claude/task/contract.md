# Task contract — player metric directions

objective: >
  Appearances, minutes per appearance and the share of team goals carry the direction the
  catalogue's own rule gives them (is more of it better, all else equal: yes), their
  interpretations stop calling them neither good nor bad, and the `direction` description no
  longer names a position-dependent share as neutral.

refs: >
  #136, the Player page review, where the catalogue's player metrics were listed (directions,
  interpretation texts and the description sentence approved in chat, 2026-11-01; this MR's plan
  approved in chat, 2026-11-01). The approved player metric labels ship with the page that first
  shows each metric and are recorded on #136.

scope_paths:
  - dbt_project/seeds/metric_catalogue.csv
  - dbt_project/seeds/schema.yml
  - docs/wireframes/11_team_squad.md
  - .claude/task/contract.md
  - .claude/task/review.md
  - .claude/task/review_input.patch
  - .claude/task/acceptance_evidence.md

impact_map: >
  `metric_catalogue.csv` changes `direction` and `interpretation` on three player rows.
  `direction` is read in SQL by mart_team_competition_benchmarks and mart_team_leaderboards,
  both limited to team rows, and by scripts/export_metric_definitions_json.py (only as
  lower_better) and the export's metric rows (team rows only); none of the three metrics is in
  the player benchmark set (int_player_competition_benchmark_metrics_long.sql), so no served value
  changes. `fetch_glossary` in scripts/export_site_data.py writes every catalogue row and column
  to `metrics.json`, so the three rows' `direction` and `interpretation` change in that file; the
  deploy's export list in .gitlab-ci.yml does not include `glossary`, and no page under site_v2/src
  reads it. `schema.yml` changes one column
  description of the catalogue seed.
  blast_radius: none rendered; three catalogue rows.

approved_design:
  - none: no page output changes; the diff touches two seed files and no site file

decisions_taken: >
  Approved in chat, 2026-11-01: appearances, minutes per appearance and contribution_player_pct
  become higher_better; their interpretations lose the closing 'not good or bad' sentence, the
  contribution share keeping its position caveat in brackets; the `direction` description's
  neutral example is a narrative gap only; the deserved points gap stays neutral; the player
  metric labels ship with the page that first shows each metric.

decisions_reserved:
  - "none: every decision of this task is approved, see decisions_taken"

acceptance_criteria:
  - "appearances, minutes_per_appearance and contribution_player_pct carry direction higher_better and an interpretation without the 'not good or bad' close; no other catalogue cell changes."
  - "The catalogue's direction description reads: neutral is reserved for a metric with genuinely no better/worse pole, such as a narrative gap."

amendments:
  - "Approved in chat, 2026-11-01: the Team Squad wireframe's minutes-per-appearance row drops '(neutral)', so it no longer restates a direction the catalogue owns."

done_when:
  - The offline gates, pytest, the site's node tests and dbt parse pass.
