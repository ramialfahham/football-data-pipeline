# Task contract — #243 step 1: the registry check sees every visual value

objective: >
  Part of #243 (step 1 only). scripts/check_component_registry.py reads only some of the
  properties of site_v2/src/styles/system.css, so a one-off corner, border, box size, shadow or
  background passes the build. Make it exhaustive: a `corners` set in docs/design/components.yml
  holding exactly today's radii, every border-radius value outside it counted under "stylesheet
  values", every other declaration either governed by a set or on an explicit non-visual list in
  the check, and anything else counted as "unchecked property" and pinned so the count only falls.
  A `<style>` block or `style=` attribute in any site_v2/src/**/*.astro file fails (pinned at 0).
  No value in system.css or any page changes; no set shrinks (that is #230).

refs: "#243 (its reopen note and its corners note); order of #243: 1 this check, 2 #230, 3 parts sheet, 4 pages"

scope_paths:
  - scripts/check_component_registry.py
  - tests/test_check_component_registry.py
  - tests/fixtures/component_registry/baseline.json
  - docs/design/components.yml
  - .claude/task/243-registry-check-coverage/contract.md
  - .claude/task/243-registry-check-coverage/review.md
  - .claude/task/243-registry-check-coverage/review_input.patch

protected_override: >
  docs/design/components.yml gains one set, `corners`, holding the radii system.css already uses.
  The order of #243 (check first, then #230) was agreed with the CPO and handed to this task by
  the coordinating session, 2026-11-16; the MR head declares the locked file and the CPO's merge
  is the approval.

impact_map: >
  writers: only a hand edit of docs/design/components.yml; sync_dbt_vars.py and the exports do
  not touch it.
  readers: scripts/check_component_registry.py (load(), counts()); scripts/check_design_inventory.py
  and scripts/design_inventory.py read components and parts, not sets (`grep -n "sets" ` on both
  to be confirmed in the task); docs/wireframes/block_standard.md is generated from components
  and parts only, so a new set leaves its table byte-identical.
  fails_if_wrong: load() rejects an unknown set key, so `corners` is added to SETS together with
  the registry key; a wrong value list makes the check count a radius nobody uses (visible in
  the pinned count), never a build break on its own.
  failure_mode: the CI job `check_component_registry` fails the MR on a count off its pin, in both
  directions; no runtime or site output depends on it.
  blast_radius: none on the site — system.css and every page are untouched, verified by an empty
  `git diff` on site_v2/.

depends_on:
  - none: no open MR changes the registry check, the registry or system.css for this step
shared_files:
  - tests/fixtures/component_registry/baseline.json

decisions_taken: >
  Engineering calls of the check (which properties are non-visual, how a radius is tokenised) are
  the coordinator's brief. No new mechanism and no recurring cost: one more count in an existing
  CI check.

decisions_reserved:
  - "none: the corners set holds only what system.css already uses; which corners the site keeps is #230"

done_when:
  - "python scripts/check_component_registry.py exits 0 with the new counts pinned"
  - "pytest tests/test_check_component_registry.py passes, including a new radius, a new unchecked property and an inline style each failing"
  - "python scripts/ci_local.py --mr is green and the full pytest passes"
  - "git diff main -- site_v2/ is empty"

amendments: (none)
