# Task contract — the two-width pins measured again on main

objective: >
  A merge request that changes the checks and not the site renders two widths against its own
  pins. Main fails two of them: the committed sample was regenerated and these pins were not
  measured with it. Set the Match page "scroll" pins to what main renders.

refs: >
  #362 (the header build; its design-checks part cannot pass until main's two-width pins hold).
  #36 (the crest change whose commit ba3e4762 regenerated the committed sample).

scope_paths:
  - .claude/task/362-quick-pins/
  - tests/test_design_inventory.py
  - tests/fixtures/design_inventory/baseline_quick.json
  - tests/fixtures/design_inventory/baseline_quick_fi.json

protected_override: >
  tests/test_design_inventory.py: one named exemption from the rule that a two-width pin never
  rises above main's, for the Finnish Match page "scroll" count going from 89 to 97, and for
  nothing else (approved in chat, 27 Nov 2026). A test fails any other file, page, count or
  number.

impact_map: >
  tests/test_design_inventory.py runs in test:python and in validate:ui. The two pin files are
  read by validate:ui's two-width sweep on a merge request that does not change the rendered
  site, and by this test file; scripts/ci_local.py runs the same job. No hook and no pipeline
  file changes. The exemption matches one pin file and one rise line that carries both main's
  count and the new one, so once main holds 97 it matches no comparison. If it were wider, a new
  gap could be pinned instead of fixed. The full pins in baseline.json stay as they are: main's
  full sweep is 0 off. Nothing reads the warehouse and nothing deploys.

approved_design:
  - none: no page output changes

depends_on:
  - none: no merge request is open

shared_files:
  - tests/fixtures/design_inventory/baseline_quick.json
  - tests/fixtures/design_inventory/baseline_quick_fi.json

decisions_taken: >
  Both pins are set once to main's measured values, English and German 943 to 896, Finnish 89 to
  97, the Finnish rise included (approved in chat, 27 Nov 2026). Cause: the crest change
  regenerated the committed sample, which now holds more match pages whose competition has a long
  name; at 320px more Finnish breadcrumb trails slide, as the approved breadcrumb does. No layout,
  style or label changed. No new mechanism, no dependency and no recurring cost.

decisions_reserved:
  - none: questions go to the coordinating session.

done_when:
  - python scripts/ci_local.py --mr is green.

amendments: (none)
