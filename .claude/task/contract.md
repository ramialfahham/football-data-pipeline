# Task contract — own season mapping: every club competition edition in one season

objective: >
  Issue #257: a reviewed seed places every club competition edition in a season and feeds
  dim_competition_season, and the Player page windows read it, so "This season" and "Last season"
  no longer depend on provider labels or dates.

refs: >
  #257, approved in chat 2026-11-05. Follows #256.

scope_paths:
  - dbt_project/seeds/competition_season_map.csv
  - dbt_project/seeds/schema.yml
  - dbt_project/models/3_core/dim_competition_season.sql
  - dbt_project/models/3_core/core.yml
  - dbt_project/models/4_intermediate/shared/int_competition_season__club_windows.sql
  - dbt_project/models/4_intermediate/shared/int_player_page.yml
  - dbt_project/tests/assert_season_map_covers_club_editions.sql
  - dbt_project/tests/assert_season_map_places_known_editions.sql
  - .claude/task/contract.md
  - .claude/task/review.md
  - .claude/task/review_input.patch
  - .claude/task/acceptance_evidence.md
  - .claude/task/rendered_page_evidence.md

impact_map: >
  writers: dbt only; no ingestion change. dim_competition_season gains columns from the new seed.
  lineage: `dbt ls --resource-type model --select int_competition_season__club_windows+` returns
  4_intermediate.shared.int_competition_season__club_windows,
  4_intermediate.shared.int_player__page_profile,
  4_intermediate.shared.int_player_page__window_seasons,
  4_intermediate.shared.int_player_squad_window__metrics,
  4_intermediate.shared.int_player_window__metrics,
  5_marts.shared.mart_player_competition_benchmarks, 5_marts.shared.mart_player_profile,
  5_marts.shared.mart_player_squad_benchmarks, 5_marts.shared.mart_player_window_metrics.
  dim_competition_season readers (dim_player_team_season_mapping,
  dim_team_competition_season_mapping, fct_standings, mart_roster and the marts above) select named
  columns, so the added columns reach none of them.
  consumption: the export does not read the two new marts yet; no page shows these windows.
  ci_layer_rules: scripts/check_layer_contract.py, scripts/check_description_hygiene.py,
  scripts/check_relationships_coverage.py.
  deploy_order: one merge; the nightly dbt build loads the seed and rebuilds. No backfill.
  blast_radius: the this_season and last_season members change for calendar-year leagues and for
  split-year leagues with a calendar-year continental cup, and so the numbers in
  mart_player_window_metrics, mart_player_squad_benchmarks and page_tab in
  mart_player_competition_benchmarks. featured_team_sk can change with them. Kane's last season
  stays as the answer key holds it. season_label does not change.

approved_design:
  - none: no page output changes

decisions_taken: >
  The definition of season and previous season, the split-year and calendar-year columns, and the
  Club World Cup 2025 at the end of 2024/25: approved in chat 2026-11-05, recorded on #257.
  Winter Club World Cup editions belong to the season they were played in, approved in chat
  2026-11-05. J1 2027's previous season is J1 2026 and J1 2027 is the first split-year J1 season: both
  follow the approved definition, the same league's season before it, approved in chat 2026-11-05.
  Seed and column names follow the warehouse's patterns and go to the CPO in the MR head.

decisions_reserved:
  - season_label corrections for J1 2027, the CONCACAF Champions Cup and the AFC Champions League 2016 to 2021.

acceptance_criteria:
  - Every club competition edition belongs to a season by our own reviewed mapping, not by provider labels or dates.
  - An edition stays whole in one season. The Super Cup and qualifiers open the new season.
  - Each edition carries its split-year season and its calendar-year season, and each season its kind and previous season.
  - dim_competition_season serves the mapping.
  - A player's this season and last season read the mapping. KuPS's UEFA 2025 is no longer in Veikkausliiga 2026, and Liga MX's CONCACAF Champions Cup 2026 is in Liga MX 2025/26.
  - A test fails when a club edition with fixtures has no mapping row.

done_when:
  - dbt parse succeeds from the repo root.
  - python -m pytest tests -q is green.
  - The offline gates in FAST_GATES pass.
  - CI's data:build:mr is green.

amendments: (none)
