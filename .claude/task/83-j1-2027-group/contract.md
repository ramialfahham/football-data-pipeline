# Task contract — J1 2027 joins the international group

objective: >
  Issue #83 follow-up: competition_season_map sets J1 2027's competition_group to international,
  applying the season map's group rule (a split-year league outside Europe). One seed cell.

refs: >
  #83. The value approved in chat, 2026-11-09.

scope_paths:
  - dbt_project/seeds/competition_season_map.csv
  - .claude/task/83-j1-2027-group/contract.md
  - .claude/task/83-j1-2027-group/review.md
  - .claude/task/83-j1-2027-group/review_input.patch

approved_design:
  - none: no page output changes

decisions_taken: >
  J1 2027's competition_group is international, approved in chat, 2026-11-09. J1 is not in the
  elite group, so the home page's Top players and Top teams boards do not change. No new
  mechanism, no recurring cost.

decisions_reserved:
  - none: the one value is approved and nothing else changes.

done_when:
  - dbt parse succeeds from the repo root.
  - python -m pytest tests/test_registry_seed_projection.py -q is green.
  - The offline gates in FAST_GATES pass.
  - CI's data:build:mr is green, and dim_competition_season, mart_leaderboards and mart_team_leaderboards differ from prod only in J1 2027's competition_group.

amendments: (none)
