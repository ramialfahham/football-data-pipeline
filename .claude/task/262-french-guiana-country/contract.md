# Task contract — French Guiana keeps its country when the provider sends Guyana

objective: >
  Issue #262: the 13 Nov nightly failed unique_dim_team_team_country because the provider's CONCACAF
  Nations League delivery of 13 Nov gives French Guiana's national team (team 8118, "French Guyana")
  the country Guyana, which Guyana's own national team (5162) holds. Through 12 Nov it sent
  French-Guiana. One team_country_corrections row restores French Guiana.

refs: >
  #262; route ruled by the coordinating session on 2026-11-13 after the read-only trace of the
  failing row. The other 13 Nov failure (Copa del Rey fixture 1644363's cards) waits on the official
  match sheet and is not part of this task.

scope_paths:
  - dbt_project/seeds/team_country_corrections.csv
  - .claude/task/262-french-guiana-country/contract.md
  - .claude/task/262-french-guiana-country/review.md
  - .claude/task/262-french-guiana-country/review_input.patch

approved_design:
  - none: no page output changes; team 8118 keeps the country it showed until 12 Nov

decisions_taken: >
  Ruled by the coordinating session on 2026-11-13. Team 8118 is French Guiana: the provider's own
  /teams delivery said French-Guiana until 12 Nov, and Concacaf's 2026/27 Nations League groups page
  lists French Guiana and Guyana as two separate national teams. The row records the wrong provider
  value, Guyana, so assert_team_country_corrections_still_needed warns when the provider returns to
  French-Guiana. A seed row through the existing mechanism; no new mechanism, no recurring cost.

decisions_reserved:
  - The Copa del Rey cards of fixture 1644363, which need the official match sheet.

done_when:
  - dbt parse passes and the full pytest suite passes.
  - The MR's data build passes unique_dim_team_team_country, and its dim_team differs from prod only in team 8118's country.

amendments: (none)
