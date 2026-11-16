# Task contract — main's full design check finishes in under 30 min

objective: >
  Issue #316. Main's validate:ui runs 41–60 min on ci-runner-01 and holds one of its two job slots
  that long. Measure where the time goes, then remove the largest costs the measurement shows
  until the job is projected under 30 min, checking exactly what it checks today.

refs: >
  #316. The breakdown is posted on the issue; the before/after is in the MR head.

scope_paths:
  - scripts/check_design_inventory.py
  - tests/test_design_inventory.py
  - scripts/check_chart_screenshots.py
  - tests/test_check_chart_screenshots.py
  - tests/test_phone_built_pages_231.py
  - .claude/task/316-sweep-speed/

protected_override: >
  Approved in chat, 2026-11-16: the CPO typed the go in this task's session for
  scripts/check_design_inventory.py and tests/test_design_inventory.py.

impact_map: >
  scripts/check_design_inventory.py: run by validate:ui in .gitlab-ci.yml (quick scope on a merge
  request, full scope on main and web runs) and by the validate-local skill. Imported by
  scripts/check_chart_screenshots.py (serve only), tests/test_address_words.py and
  tests/test_design_inventory.py (`grep -rn "check_design_inventory" scripts tests .claude/hooks`).
  What depends on it: every count compared with baseline.json, baseline_quick.json and
  baseline_quick_fi.json, every failure line, counts.json and failures.json. If wrong, a count or a
  failure moves and the check goes red on main, or a gap hides. The proof is a run of the old and
  new check over one CI-built site in the CI image, diffed byte for byte (stdout, counts.json,
  failures.json); CI then compares the baselines.
  scripts/check_chart_screenshots.py: run by validate:ui after the design check; its pins are
  tests/fixtures/chart_screenshots/*. If wrong, a colour or label finding or a screenshot
  difference moves. Same proof: old and new output identical over one CI-built site.
  layer_rules, deploy_order: not applicable, no model, seed or export changes.
  blast_radius: CI time only; the pages, widths, languages, rules and baseline counts are unchanged.

depends_on: none; the change builds on main alone.

shared_files: none; no design baseline or chart pin is regenerated, since the counts stay as they are.

approved_design:
  - none: no page output changes; the diff touches no site_v2/src/ file or export script

decisions_taken: >
  What is checked stays as it is: the same pages, tabs, widths, languages, rules and baseline
  counts. No runner, timeout, schedule or MR-scope change. No new dependency, no recurring cost.

decisions_reserved:
  - A larger CI runner or more runners is a recurring cost and the CPO's call; out of scope here.
  - Removing `timeout: 2h` from validate:ui is a follow-up once three main runs confirm the time.

done_when:
  - The breakdown of where the time goes is posted on #316.
  - A run of the old and new check over main's CI-built site, in the CI image, gives identical
    stdout, counts.json and failures.json.
  - python -m pytest tests/ -q is green and the offline gates pass.
  - The MR pipeline is green, and the MR head reports the measured before and after.

amendments: (none)
