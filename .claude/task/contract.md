# Task contract — #165: the Data Scientist role brief

objective: >
  Write the Data Scientist role brief, the role that owns the prediction models, and move the
  "predictive" claim off the Football Analytics Expert; update the prediction lines in
  product_direction_threads.md and north_star.md, and add the role to the north star's Roles table.
  Docs only.

refs: >
  #165 (the build issue; its What exactly is the requirement); #164 (the predictions decisions issue
  the brief enforces); the plan approved in plan mode.

scope_paths:
  - docs/roles/data_scientist.md
  - docs/roles/football_analytics_expert.md
  - docs/product_direction_threads.md
  - docs/north_star.md
  - .claude/task/contract.md
  - .claude/task/review.md
  - .claude/task/review_input.patch

decisions_taken: >
  The CPO's rulings, recorded on #165 and approved in plan mode: the role is named "Data Scientist"
  (over ML Engineer and Predictive Modeller), because it spans exploration, modelling and the
  published analysis pages. The Football Analytics Expert stays, but without the claim to decide what
  is predictive, because predictiveness is now measured on unseen seasons; it keeps the football
  validity of displayed metrics. The Data Scientist specifies each input and its as-of-kickoff rule;
  the Analytics Engineer builds it in dbt under the layer rules and DQ tests; the model code belongs
  to the Data Scientist. No reviewer agent and no review routing for the Data Scientist yet: the
  north star's Roles row says "nothing — brief only, no agent". Builder's: the brief's wording within
  the plan's approved text, the file name data_scientist.md.

  THRESHOLD DECLARATIONS: NEW MECHANISM: none (a document; no agent, no routing row). RECURRING
  COST: none.

decisions_reserved:
  - A reviewer agent and a routing row for the Data Scientist: a separate governance step (#165 Not in scope).
  - docs/ui_design_brief.md ("no win probability"): changes when the prediction page is designed.
  - Every product decision on predictions (launch bar, cost, variables): #164, the CPO's.

done_when:
  - python -m pytest tests/ -q passes, including test_no_decision_history_in_docs.py,
    test_governance_doc_parity.py and test_no_dead_issue_refs.py.
  - python scripts/check_task_artifacts.py passes.
  - git diff --stat gitlab/main shows exactly the 4 docs plus the task artifacts.
  - The MR pipeline passes on GitLab.

amendments: (none)
