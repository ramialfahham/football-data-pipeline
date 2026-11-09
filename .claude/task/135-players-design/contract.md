# Task contract — the Players hub enters the approved-designs list

objective: >
  The Players hub review on #135 closed with the design approved. The Players hub enters
  docs/wireframes/approved_designs.yml so the design gate lets its build change the page
  surface once this merges.

refs: >
  #135, the Players hub's design (https://gitlab.com/rami.al-fahham/football-data-pipeline/-/work_items/135).
  Approved in chat, 2026-11-09.

scope_paths:
  - .claude/task/135-players-design/
  - docs/wireframes/approved_designs.yml

decisions_taken: >
  Approved in chat, 2026-11-09: the Players hub review is closed and the page enters the list as
  "players: 135".

decisions_reserved:
  - none: the CPO approved the Players hub design on #135, and this task only records it in the list.

done_when:
  - The full pytest suite passes.
  - Reviewers per review_routing.json pass.

amendments: (none)
