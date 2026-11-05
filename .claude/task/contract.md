# Task contract — merge requests run a quick design check, main runs the full one

objective: >
  Issue #252: on merge requests validate:ui runs the design check at two widths (280 and 1010 px)
  in English and German over every built page and every mock, compared with its own pinned counts;
  main, web runs and the local default keep the full 6 widths x 3 languages and the full baseline.
  Cuts the check from about 40 minutes to about 10, so a failing pin shows in minutes, not after a
  40-minute run.

refs: >
  #252, approved in chat 2026-11-05 (quick check on merge requests, full check on main).

scope_paths:
  - scripts/check_design_inventory.py
  - tests/test_design_inventory.py
  - tests/fixtures/design_inventory/baseline_quick.json
  - docs/wireframes/block_standard.md
  - .gitlab-ci.yml
  - .claude/task/contract.md
  - .claude/task/review.md
  - .claude/task/review_input.patch
  - .claude/task/acceptance_evidence.md
  - .claude/task/rendered_page_evidence.md

protected_override: >
  Approved in chat, 2026-11-05: the quick design check on merge requests. Edits
  .gitlab-ci.yml (validate:ui passes the quick scope and baseline on merge_request_event) and
  scripts/check_design_inventory.py (a baseline names the widths and languages it pins, and a run
  that matches them is compared), tests/test_design_inventory.py and the new pin file under
  tests/fixtures/design_inventory/.

impact_map: >
  readers: validate:ui in .gitlab-ci.yml runs check_design_inventory.py; the validate-local skill
  runs it with no flag; tests/test_design_inventory.py drives it as a subprocess and calls
  compare_rendered and compare_coverage. `grep -rl check_design_inventory` (excluding .claude/task)
  returns 22 files: the check, its test and .gitlab-ci.yml; tests/test_governance_doc_parity.py,
  tests/test_governance_hooks.py, tests/test_address_words.py; site_v2/src/lib/addressWords.mjs;
  design-mocks/README.md; scripts/design_inventory.py, check_component_registry.py,
  check_chart_screenshots.py; requirements-ui.txt; docs/working_agreement.md,
  docs/wireframes/block_standard.md, docs/wireframes/00_overview.md,
  docs/roles/platform_reliability.md, docs/north_star.md; the validate-local skill;
  .claude/hooks/task_contract_gate.py, .claude/review_routing.json, .claude/agents/cto-reviewer.md
  and platform-reviewer.md. They name the script in text or as a protected path; none imports
  its main().
  fires_on: a merge request pipeline passes --viewports 280,1010 --langs en,de --baseline
  tests/fixtures/design_inventory/baseline_quick.json. main, web and local runs pass none, so they
  read baseline.json, whose scope is the default, and run exactly as today; a test pins that the
  flags sit only inside the merge_request_event branch.
  on_failure: a run whose widths and languages differ from its baseline's scope is still a
  narrower run: compared with nothing, element misses fail as before. The quick baseline is
  measured on linux, so off linux its rendered counts are not compared. The quick pins cannot
  rise above main's copy of the file (a test, as for baseline.json), and the file's scope must
  match the flags in .gitlab-ci.yml (a test).
  stops_being_enforced_if_wrong: a defect visible only at a width or language the quick scope
  does not render (320, 360, 375, 700 px, Finnish) passes the merge request and fails on main's
  full run, which still compares every pin. A merge request that moves a rendered count must move
  both pin files, and baseline.json is measured only by main's or a manual run, so a wrong full
  pin shows after the merge, not before it.
  deploy_order: none; no data, no deploy, no new dependency, no recurring cost. build:site-v2 is
  unchanged.
  blast_radius: validate:ui duration and what a merge request pipeline can catch; no page output
  changes.

approved_design:
  - none: no page output changes

decisions_taken: >
  The quick scope is the narrowest and the widest width in English and German; English because
  the mocks exist only in English and Finnish, German because it is the longest text. A merge
  request that renders less than main is the approved trade, approved in chat 2026-11-05. The
  baseline file names its own scope (a second pin file) so the compare logic stays one code path.
  No new dependency, no recurring cost (the job gets shorter).

decisions_reserved:
  - none: the width and language choice is stated and changeable in one line of .gitlab-ci.yml.

done_when:
  - python -m pytest tests/test_design_inventory.py -q is green.
  - A local run with --viewports 280,1010 --langs en,de --baseline baseline_quick.json prints that rendered counts are not compared off linux, and a run with the default scope still compares.
  - The merge request pipeline's validate:ui time is quoted in the MR, with the quick pins taken from a linux run's counts.json.

amendments: (none)
