# Task contract — the phone check also sweeps Finnish at 320px, the local design check runs, and validate:ui runs locally in the CI image

objective: >
  Issue #311. A merge request's validate:ui also sweeps Finnish at 320px; the local design check no
  longer crashes in its colour parser on a developer machine; a script runs the whole validate:ui
  script list of .gitlab-ci.yml inside the CI image through Docker, and running it is the rule before
  every review round on a change under the design surfaces.

refs: "#311 (CPO, parts 1 and 2 approved in chat 2026-11-14, part 3 approved in chat 2026-11-15); #231 (the phone-fixes MR whose rounds this removes)"

scope_paths:
  - .claude/task/311-local-ci-check/
  - .gitlab-ci.yml
  - scripts/design_inventory.py
  - scripts/check_design_inventory.py
  - tests/test_design_inventory.py
  - tests/fixtures/design_inventory/baseline_quick_fi.json
  - scripts/validate_ui_docker.py
  - tests/test_validate_ui_docker.py
  - .claude/skills/validate-local/SKILL.md

protected_override: >
  .gitlab-ci.yml, scripts/design_inventory.py, scripts/check_design_inventory.py and
  tests/test_design_inventory.py: the Finnish 320px sweep in the merge-request run (part 1) and the
  colour-parser fix (part 2), approved in chat on 2026-11-14 as the body of issue #311; the new
  pin file baseline_quick_fi.json belongs to part 1.

impact_map: >
  writers: none; no dbt model, no export script, nothing under site_v2/src.
  downstream: the merge-request pipeline's validate:ui job gains one more design-check run (Finnish,
  320px) with its own pin file; main, manual and local runs are unchanged. design_inventory.py's
  colour parser is read by check_design_inventory.py only (parse_css_color is called from compare()
  and expected_color()); a colour the page does not carry becomes a reported finding where it
  crashed the run.
  layer_rules: not applicable; no computation.
  deploy_order: none; CI only.
  blast_radius: every merge request that touches the UI paths runs one more check, measured in the MR;
  a failing Finnish count now blocks the MR instead of main. The new script is read by no job.

decisions_taken: >
  The script reads the validate:ui job's image, before_script and script from .gitlab-ci.yml at run
  time, so no second copy of the steps exists. It runs them against a copy of the working tree
  inside the container (the repo is mounted read-only), in the merge-request scope. The Finnish run
  is its own script line with its own pin file, because one run takes one viewport list and one
  language list. Thresholds: no new recurring spend (the runner time of one more check is measured
  in the MR); one new local script, which part 3 of #311 approves.

decisions_reserved:
  - none: the three parts are the CPO's approved wording on #311.

approved_design:
  - none: no page output changes

done_when:
  - the new script runs green on this branch, its output is in the MR
  - the local design check completes on this Windows machine without the colour crash
  - the MR pipeline is green and the added job time is stated in the MR
  - the full pytest passes

amendments:
  - Part 3 also runs the design inventory in main's full scope (every width, en, de and fi, against baseline.json) as a second pass. Authority: the CPO's approval in chat on 15 Nov 2026 that a local run of the exact CI phone and screenshot check precedes every review; main's validate:ui is part of that check, so its full scope is included (relayed by the coordinating session). This MR does not edit baseline.json.
  - The new pin file baseline_quick_fi.json is covered by the same guards as baseline_quick.json (no pin rises above main's, its scope equals the CI line's, its page names and count keys are valid). Part 1 of #311 covers it.
