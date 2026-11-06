# Task contract — list the Player page's approved design

objective: >
  Issue #259, its first line: `player: 136` enters docs/wireframes/approved_designs.yml, so the
  contract gate accepts the Player page's build contracts. The CPO's merge is the approval.

refs: >
  #259, plan approved in chat 2026-11-06. Design: #136.

scope_paths:
  - docs/wireframes/approved_designs.yml
  - .claude/task/contract.md
  - .claude/task/review.md
  - .claude/task/review_input.patch
  - .claude/task/acceptance_evidence.md
  - .claude/task/rendered_page_evidence.md

approved_design:
  - none: no page output changes

decisions_taken: >
  One line in the list of approved designs, approved with the plan on #259. No new mechanism, no
  recurring cost.

decisions_reserved:
  - none: this lists a design the CPO approved on #136 and changes nothing else

done_when:
  - docs/wireframes/approved_designs.yml holds `player: 136`.
  - pytest tests passes.

amendments: (none)
