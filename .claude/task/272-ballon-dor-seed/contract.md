# Task contract — Ballon d'Or and Yashin Trophy results seed

objective: >
  Issue #272, first part. A researched seed of the Ballon d'Or nominees and the Yashin Trophy
  nominees for the editions 2016–2026, each row with its final placing and its published source,
  and a test that fails the build when a row resolves to no player in `base_apif__players`.

refs: >
  #272. History window 2016–2026 set on the issue (approved in chat, 2026-11-09). Plan for this MR
  approved by the coordinating session, 2026-11-09.

scope_paths:
  - .claude/task/272-ballon-dor-seed/
  - dbt_project/seeds/player_award_results.csv
  - dbt_project/seeds/schema.yml

approved_design:
  - none: no page output changes; the diff touches no site_v2/src/ file, no export script and no model

decisions_taken: >
  The seed is one row per award, edition and nominee. `placing` is the published final rank; tied
  players share it; it is empty where no source publishes it. Every row carries the publisher's URL
  (`source_url`) and one major outlet's URL that confirms it (`check_url`). The Yashin Trophy rows
  start in 2019, its first edition. No model reads the seed in this MR; the Player page line and
  its mart are the issue's second part, built after the Player page design approves the line.
  NEW MECHANISM: none (a seed with column tests, as the other correction seeds). RECURRING COST:
  none (no provider call, no new run).

decisions_reserved:
  - How the Player page shows the results (placement, tabs, rows, EN/DE/FI texts) is decided on the
    Player page design (#136) before the second part is built.

done_when:
  - Every edition 2016, 2017, 2018, 2019, 2021, 2022, 2023, 2024, 2025, 2026 has its Ballon d'Or rows;
    every edition from 2019 has its Yashin Trophy rows.
  - The seed's tests pass against the warehouse, the relationships test with every row matched.
  - `scripts/check_description_hygiene.py`, `dbt parse` and the `validate-local` offline gates pass.
  - The site export diffed against main shows no change.
  - The MR's CI is green.

amendments: (none)
