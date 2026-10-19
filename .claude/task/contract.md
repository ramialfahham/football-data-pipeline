# Task contract — the Teams page enters the approved-designs list

objective: >
  The Teams page review on #133 closed with the design approved. The Teams page enters
  docs/wireframes/approved_designs.yml so the design gate lets its build (#222) change the page
  surface once this merges.

refs: >
  #133, the Teams page's design (https://gitlab.com/rami.al-fahham/football-data-pipeline/-/work_items/133);
  the build is #222. Approved in chat, 2026-10-19.

scope_paths:
  - docs/wireframes/approved_designs.yml
  - .claude/task/contract.md
  - .claude/task/review.md
  - .claude/task/review_input.patch
  - .claude/task/acceptance_evidence.md
  - .claude/task/rendered_page_evidence.md

decisions_taken: >
  Approved in chat, 2026-10-19: the Teams page review is closed and the page enters the list as
  "teams: 133".

decisions_reserved:
  - none: the CPO approved the Teams page design on #133, and this task only records it in the list.

done_when:
  - The full pytest suite passes.
  - Reviewers per review_routing.json pass.

amendments: (none)
