# Task contract — equal tab widths on every tab bar

objective: >
  Issue #254: every tab bar on the site, Competition, Team and Player pages, gives its tabs equal
  widths; a label that needs more than its share takes it and is not cut off. The tab bar's
  rule in the component registry carries #254's approved text. Part of the Team page design
  approved on #250, built on its own because the one tab bar rule changes every page with tabs.

refs: >
  #254 (rule text approved in chat, 2026-11-05), #250 note 4170153960 ("Tabs are equal width
  (#254)"), #243 (one tab bar part, ui/TabBand.astro).

scope_paths:
  - .claude/task/254-equal-tab-widths/
  - site_v2/src/styles/system.css
  - docs/design/components.yml
  - docs/wireframes/block_standard.md
  - tests/fixtures/component_registry/baseline.json
  - tests/fixtures/design_inventory/baseline.json
  - tests/fixtures/design_inventory/baseline_quick.json
  - tests/fixtures/design_inventory/baseline_quick_fi.json
  - tests/fixtures/chart_screenshots/*

protected_override: >
  docs/design/components.yml: the tab bar's `bar` rule becomes #254's approved text, "the tabs
  share the row equally and fit in one row at 375px in EN, DE and FI, no sideways scrolling; a
  label that needs more than its share takes it"; no other part, text style, value or
  measurement changes. #254's rule text approved in chat, 5 Nov 2026; the Team page design
  approved in chat, 6 Nov 2026 (#250).

impact_map: >
  writers: none; one declaration in site_v2/src/styles/system.css (`.comp-tabs .tab` flex from
  `1 1 auto` to `1 1 0`, min-width left at its default `auto`) and the tab bar's rule text in the
  component registry with its generated table.
  downstream: site_v2/dist only: every page with a tab bar (the competition pages, every Team page,
  every Player page). leaf: consumption layer, no computation.
  guard: docs/design/components.yml is read by scripts/check_component_registry.py,
  scripts/check_design_inventory.py, scripts/design_inventory.py, scripts/parts_page.py and
  site_v2/scripts/check-term-list.test.mjs. The rule text changes; the class, selector and
  measurement (`fits`) do not, so what the design check measures does not change.
  layer_rules: not applicable; no computation.
  deploy_order: none; deploy:site-v2 is manual.
  blast_radius: the width of each tab on every tab bar; no text, link or block changes.

acceptance_criteria:
  - Every tab bar on the site gives its tabs equal widths: Competition, Team and Player pages.
  - Where a label needs more than its share, it takes it and is not cut off.
  - The registry's Tab bar rule reads: "the tabs share the row equally and fit in one row at 375px in EN, DE and FI, no sideways scrolling; a label that needs more than its share takes it" (approved in chat, 2026-11-05).
  - The registry lists the Player page under the Tab bar's `used-on`.

approved_design:
  - competition: #129
  - team: #134
  - player: #136

depends_on:
  - none: !481 is merged (main c1084493)

shared_files:
  - site_v2/src/styles/system.css
  - docs/design/components.yml

decisions_taken: >
  The tabs keep their 4px side padding and their default min-width, so a label longer than its
  share widens its own tab and the others narrow, as #254 measured. No new mechanism, dependency
  or cost.

decisions_reserved:
  - none: the rule text is #254's approved text.

done_when:
  - Every page with a tab bar of the committed sample, EN/DE/FI, at 280, 320, 375 and 1010px: tabs of equal width unless a label needs more, no label cut off, no sideways scroll; before and after differ only in tab widths.
  - python scripts/check_component_registry.py passes; pins do not rise.
  - python scripts/ci_local.py --mr is green.

amendments: (none)
