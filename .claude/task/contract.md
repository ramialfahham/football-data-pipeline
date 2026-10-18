# Task contract — Home enters the approved-designs list

objective: >
  The Home recheck on #127 closed with the design approved. Home enters
  docs/wireframes/approved_designs.yml so the design gate lets its build (#219) change the page
  once this merges.

refs: >
  #127, Home's design (https://gitlab.com/rami.al-fahham/football-data-pipeline/-/work_items/127);
  the build is #219. Approved in chat, 2026-10-18.

scope_paths:
  - docs/wireframes/approved_designs.yml
  - tests/test_governance_hooks.py
  - .claude/task/contract.md
  - .claude/task/review.md
  - .claude/task/review_input.patch
  - .claude/task/acceptance_evidence.md
  - .claude/task/rendered_page_evidence.md

decisions_taken: >
  Approved in chat, 2026-10-18: the Home recheck is closed and Home enters the list as
  "home: 127". The shipped-list test stops pinning the exact entries, which would need a test edit
  for every approval, and instead checks that every entry line of the shipped file parses.

decisions_reserved:
  - none: the CPO approved the Home design on #127, and this task only records it in the list.

done_when:
  - The full pytest suite passes.
  - Reviewers per review_routing.json pass.

amendments: (none)
