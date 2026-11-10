# Task contract — the Statistics page enters the approved-designs list

objective: >
  The Statistics review on #139 (with the leaderboard page on #140) closed with the design approved. The
  Statistics page enters docs/wireframes/approved_designs.yml so the design gate lets its build change the page
  surface once this merges, and the design chain's screen inventory points at the issues.

refs: >
  #139, the Statistics page's design (https://gitlab.com/rami.al-fahham/football-data-pipeline/-/work_items/139);
  #140, the leaderboard page. Approved in chat, 2026-11-10.

scope_paths:
  - .claude/task/139-statistics-design/
  - docs/wireframes/approved_designs.yml
  - docs/wireframes/00_overview.md

decisions_taken: >
  Approved in chat, 2026-11-10: the Statistics review is closed and the page enters the list as "statistics: 139";
  the leaderboard page is part of the same design (recorded on #139, noted on #140).

decisions_reserved:
  - none: the CPO approved the Statistics and leaderboard design on #139 and #140, and this task only records it in the list and the screen inventory.

done_when:
  - The full pytest suite passes.
  - Reviewers per review_routing.json pass.

amendments: (none)
