# Task contract — the Team page enters the approved-designs list

objective: >
  The Team page review on #134 closed with the design approved. The Team page enters
  docs/wireframes/approved_designs.yml so the design gate lets its build change the page surface
  once this merges.

refs: >
  #134, the Team page's design (https://gitlab.com/rami.al-fahham/football-data-pipeline/-/work_items/134),
  drawn in the mock in the private snippet 6069923. Approved in chat, 2026-10-22 and 2026-10-28.

scope_paths:
  - docs/wireframes/approved_designs.yml
  - docs/wireframes/00_overview.md
  - .claude/task/contract.md
  - .claude/task/review.md
  - .claude/task/review_input.patch
  - .claude/task/acceptance_evidence.md
  - .claude/task/rendered_page_evidence.md

approved_design:
  - none: no page output changes

decisions_taken: >
  Approved in chat, 2026-10-28: the Team page review is closed and the page enters the list as
  "team: 134"; the screen inventory's row 02 in 00_overview.md points at #134 as the authority for
  the page, in the approved text with its dates, its tab list and its closing clause left out and
  the issue as a link. As #134 records, the Squad sub-screen (11_team_squad.md) is the Overview's
  last block and the Stats sub-screen (14_team_stats.md) is the Performance tab.

decisions_reserved:
  - none: the CPO approved the Team page design on #134, and this task only records it in the list.

done_when:
  - The full pytest suite passes.
  - Reviewers per review_routing.json pass.

amendments:
  - "2026-10-28: + docs/wireframes/00_overview.md — authority: the CPO's approval in chat, 2026-10-28, of the row text; content: row 02 of the screen inventory names #134 as the authority for the Team page."
  - "2026-10-28: the shortened row 02 text as committed and the decisions_taken line on the Squad and Stats sub-screens — authority: the CPO's approval in chat, 2026-10-28, of both texts as shown to him; content: unchanged from the round-3 diff."
