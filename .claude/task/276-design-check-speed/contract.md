# Task contract — the design check spends less CPU per render

objective: >
  Issue #276. Main's validate:ui hit the 1 h job limit twice on 2026-11-09. On ci-runner-01's
  cores the design check is CPU-bound, so this cuts the CPU each render costs, with identical
  findings, counts and output.

refs: >
  #276. Measurements: the issue's exploration detail and the MR head.

scope_paths:
  - scripts/check_design_inventory.py
  - tests/test_design_inventory.py
  - .claude/task/276-design-check-speed/

protected_override: >
  Approved in chat, 2026-11-09: the CPO typed the go in this task's session for
  scripts/check_design_inventory.py, then for tests/test_design_inventory.py so its fake browser
  returns the measurement as a JSON string.

impact_map: >
  scripts/check_design_inventory.py: run by validate:ui in .gitlab-ci.yml (quick scope on a merge
  request, full scope on main and web runs) and by the validate-local skill. Imported by
  scripts/check_chart_screenshots.py (serve only), tests/test_address_words.py and
  tests/test_design_inventory.py (`grep -rn "check_design_inventory" scripts tests .claude/hooks`).
  What changes: the measuring and gap-counting scripts return a JSON string that Python decodes;
  each match carries only the fields an assertion of its element reads; the mouse is not moved to
  the point it already holds. What depends on it: every count compared with baseline.json and
  baseline_quick.json, every failure line, counts.json and failures.json. If wrong, a count or a
  failure moves and the check goes red on main, or a gap hides. The proof is a full run of the
  old and new check over one CI-built site, diffed byte for byte (stdout, counts.json,
  failures.json); CI then compares both baselines. serve() is unchanged, so chart screenshots
  are unaffected.
  tests/test_design_inventory.py: one fake browser's evaluate returns its canned measurement
  through json.dumps; the assertions are unchanged.

approved_design:
  - none: no page output changes; the diff touches no site_v2/src/ file or export script

decisions_taken: >
  Coverage, scope, pins and the job's timeout are unchanged: every page, tab, width and language
  as before. Ruled out on measurement: reusing one load across widths (measures a resized page,
  saves 15 ms of ~198), more workers (the runner is CPU-bound), Chromium flags (no gain), and
  blocking crest images (slower). No new mechanism, no new dependency, no recurring cost.

decisions_reserved:
  - A larger CI runner (more vCPUs) is a recurring cost and the CPO's call; this task does not
    change the runner.

done_when:
  - A full local run of the old and new check over main's CI-built site (2 workers) gives
    byte-identical stdout, counts.json and failures.json.
  - python -m pytest tests/test_design_inventory.py tests/test_address_words.py passes.
  - The offline gates pass.
  - CI's validate:ui passes on the MR (quick baseline) and on a full-scope run (full baseline),
    with the design-check step's time reported against the before figures.

amendments: (none)
