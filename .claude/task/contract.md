# Task contract — remove the Inter allowance from the rising-pin test

objective: >
  Remove INTER_RISES, its helper _unlisted and the test of that helper from
  tests/test_design_inventory.py, so test_no_pin_rises_above_mains again refuses every pin above
  main's. main's baseline.json holds the Inter counts, so the allowance has nothing left to allow.

refs: >
  #243. The head of !378, merged 2026-11-04, names this removal as the follow-up MR.

scope_paths:
  - tests/test_design_inventory.py
  - .claude/task/contract.md
  - .claude/task/review.md
  - .claude/task/review_input.patch

protected_override: >
  Approved by the CPO's merge of !378 on 2026-11-04, whose head states that the next MR removes
  INTER_RISES. Edits tests/test_design_inventory.py only, and only by deletion, plus one call that
  stops going through the deleted helper.

impact_map: >
  readers: `grep -rIln "INTER_RISES\|_unlisted\|test_only_a_listed_rise"` returns
  tests/test_design_inventory.py and .claude/task/acceptance_evidence.md. The second is the #243
  task's evidence record; no gate reads it unless a diff touches site_v2/src. Inside the test file
  only test_no_pin_rises_above_mains and test_only_a_listed_rise_on_mains_old_value_is_allowed
  call _unlisted. No script imports either name.
  fires_on: validate:ui runs `python -m pytest tests/test_design_inventory.py -q`, and test:python
  runs it through `pytest tests/ -v`. The file is in .ui_paths, so this MR's pipeline runs the
  quick validate:ui.
  evidence_main_needs_no_allowance: pipeline 3032797643 on 0e048d28, job 17778131723, is main's
  last full validate:ui: 387 pages, 6 viewports, 3 languages, 13830 renders, 0 failures, success.
  `git diff --stat 0e048d28 gitlab/main` over tests/fixtures/design_inventory/,
  tests/test_design_inventory.py and scripts/check_design_inventory.py is empty, and later main
  pipelines skipped validate:ui because they changed no ui path. All nine pins on main sit above
  the listed value (2184/1174, 223/148, 12/9, 2/1, 47/32, 13/4, 21/19, 3/1, 42/24). _unlisted
  excused a rise only from a main value equal to the listed one, so it excuses nothing today.
  on_failure: a pin above main's fails test_no_pin_rises_above_mains with its message, as it did
  before !378. This removal cannot turn a green run red, because no rise exists between this
  branch and main.
  stops_being_enforced_if_wrong: nothing; the change tightens the ratchet. Deleting the helper's
  test loses no coverage of di.rises, which test_a_pin_may_not_rise_above_mains_and_a_new_entry_starts_at_zero
  covers.
  deploy_order: none; no data, no deploy, no new dependency, no recurring cost.
  blast_radius: one test file. No pin, baseline file, script or page output changes.

approved_design:
  - none: no page output changes

decisions_taken: >
  Removal only, as !378's head stated. No new mechanism, no new dependency, no recurring cost. The
  coverage guard in test_no_pin_rises_above_mains stays: it serves a different purpose. The record
  in .claude/task/acceptance_evidence.md stays: it belongs to the #243 task.

decisions_reserved:
  - none: the removal was named in !378's head, and no pin, page or rule changes.

done_when:
  - grep for INTER_RISES and _unlisted in tests/test_design_inventory.py returns nothing.
  - python -m pytest tests/test_design_inventory.py -q is green.
  - The MR pipeline, quick validate:ui included, is green.

amendments: (none)
