# Task contract — a merge request that changes the site is checked against the full page baseline

objective: >
  Issue #326: a merge request that changes `site_v2/src/**` or `docs/design/components.yml` runs
  validate:ui's design-inventory sweep at every width and language against
  `tests/fixtures/design_inventory/baseline.json`, as main does, so a count that drifts shows in
  the MR instead of on main. `scripts/ci_local.py --mr` runs the same sweep for such a branch, and
  `scripts/merge_ready.py` says not ready while that sweep has a count off the baseline or did not
  run.

refs: >
  #326; !471 and !472 (main's red validate:ui, pipeline 3078457547).

scope_paths:
  - .claude/task/326-full-ui-on-site-mrs/
  - .gitlab-ci.yml
  - scripts/ci_local.py
  - scripts/merge_ready.py
  - tests/test_ci_local.py
  - tests/test_merge_ready.py
  - .claude/skills/validate-local/SKILL.md
  - docs/wireframes/block_standard.md
  - tests/test_design_inventory.py

protected_override: >
  The full validate:ui scope on merge requests that change the rendered surface: approved in chat,
  17 Nov 2026, recorded on #326 (note 4255024092) with the measured runner time.

impact_map: >
  writers: none; no table, model or page output changes.
  guard: validate:ui's rules gain one rule, first after the schedule rule: a merge_request_event
  whose changes hit `site_v2/src/**/*` or `docs/design/components.yml` sets UI_FULL_SCOPE=1. Both
  paths are inside `*ui_paths`, so build:site-v2 still fires on every pipeline validate:ui fires
  on. The two scoped script steps read the variable; main's push,
  web runs and every other MR run as today. build:site-v2 takes the same rules list by anchor, so
  the two jobs' rules stay equal (`tests/test_design_inventory.py` pins that); the variable is
  unused there.
  readers: scripts/ci_local.py loads .gitlab-ci.yml at run time (rules, variables, steps);
  scripts/merge_ready.py now reads the same rule through ci_local; tests/test_ci_local.py and
  tests/test_merge_ready.py load the real file.
  failure: if the variable never set, MRs keep the quick sweep (today's state) and the new tests
  fail; if it set too widely, an MR pays the full sweep (about 11 min more on ci-runner-01, no
  spend). Main's pipeline is unchanged.
  blast_radius: CI runtime of MRs touching the two paths; no data, no deploy.

approved_design:
  - none: no page output changes

depends_on:
  - none: works on main alone

shared_files:
  - none: no design, registry, font or chart baseline changes

decisions_taken: >
  The recurring runner time (about 11 min per site MR pipeline, no spend) is the CPO's approval
  on #326. The path rule lives once, in validate:ui's rules; ci_local applies a matching rule's
  `variables:` as GitLab does, and merge_ready reads the same rule. No new dependency.

decisions_reserved:
  - none: the scope, the paths and the cost are the approved issue text.

done_when:
  - python -m pytest tests/test_ci_local.py tests/test_merge_ready.py -q passes, with tests for the path rule, the scoped steps and the merge_ready refusal.
  - python scripts/ci_local.py --mr --plan on a branch that changes a site_v2/src file shows validate:ui with UI_FULL_SCOPE=1, and on this branch without it.
  - python scripts/ci_local.py --mr on a branch that changes a site_v2/src file runs the sweep at every width in en, de and fi against baseline.json.
  - python scripts/ci_local.py --mr is green on this branch; the MR pipeline is green.

amendments:
  - 2026-11-17: + tests/test_design_inventory.py — authority: the #326 approval above (its pin on
    validate:ui's scoped steps reads the changed step text); content: that pin's regex follows the
    UI_FULL_SCOPE condition. build:site-v2 shares validate:ui's rules by anchor.
