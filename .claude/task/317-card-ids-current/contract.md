# Task contract — nightly green: card corrections keyed to the provider's current player ids

objective: >
  Issue 317: make the prod nightly green again by re-keying 8 corrected cards in
  fixture_card_corrections.csv to the player ids the provider now files on those matches' sheets,
  and deleting the fixture_result_corrections.csv row for fixture 1647990, which the provider now
  carries as the official 1-1.

refs: >
  Issue 317. Requested by the coordinating session; go-live gate issue 290.

scope_paths:
  - dbt_project/seeds/fixture_card_corrections.csv
  - dbt_project/seeds/fixture_result_corrections.csv
  - .claude/task/317-card-ids-current/contract.md
  - .claude/task/317-card-ids-current/review.md
  - .claude/task/317-card-ids-current/review_input.patch

approved_design:
  - none: no page output changes

decisions_taken: >
  Seed upkeep only, under the cleaning rule that a provider value failing its check is withheld and
  only checks of our own seeds stop the build. Each new id is proven from base_apif__lineups by
  fixture, team and player name. No new mechanism, no spend beyond read-only queries.

decisions_reserved:
  - none: nothing else changes.

done_when:
  - Evidence per row (fixture, team, old id, new id, name on today's sheet) is in the MR.
  - grep of every seed for the 7 old ids finds only the row for fixture 1506949, which is still on its sheet.
  - Full pytest, dbt parse and sqlfluff lint are green.
  - data:build:mr shows both assert_card_corrections_applied and assert_result_corrections_applied passing.

amendments:
  - + dbt_project/seeds/fixture_card_corrections.csv gains the 12 card rows of fixture 1495763 (SJK-FC Lahti, VL, 2026-08-21), already in scope_paths. Authority: the approved Cards line of cleaning_rules.md (a match whose stat lines and card events disagree takes its cards from sourced research) and the coordinating session's instruction. The official page was unreachable, so source_kind is match_reports with two sites. No new mechanism, no spend. done_when: assert_card_corrections_applied and assert_player_match_cleaning_answer_key pass in data:build:mr, and no other match changes.
