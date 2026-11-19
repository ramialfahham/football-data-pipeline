# Task contract — a club name in a row never runs past its space

objective: >
  Issue #231, follow-up to the merged !488: at 260px and 280px a result row of the match page's
  Recent matches block runs past its row when the opponent is a hyphen-joined name (for example
  "Weston-super-Mare", 142px, in a 118px space), because the build keeps a hyphen-joined word whole
  and the word is wider than the space the row leaves it. The shared part takes the name's own
  space: a hyphen-joined word stays whole on its line and breaks at its hyphens only where it is
  wider than the line. Pages whose names fit are unchanged.

refs: >
  #231 (fix approved in chat, 2026-10-23; the approved Result row rule: under the opponent come home
  or away / competition / date, whose facts wrap as whole words); !488 (merged, main 3dddb7af);
  the coordinator's request of 2026-11-19 (a follow-up under the approved result-row rule).

scope_paths:
  - .claude/task/231-result-row-fact-wrap/
  - site_v2/src/styles/system.css
  - docs/design/components.yml
  - docs/wireframes/block_standard.md
  - tests/test_phone_fixes_231.py
  - tests/fixtures/component_registry/baseline.json
  - tests/fixtures/design_inventory/baseline.json
  - tests/fixtures/design_inventory/baseline_quick.json
  - tests/fixtures/design_inventory/baseline_quick_fi.json
  - tests/fixtures/chart_screenshots/*

protected_override: >
  docs/design/components.yml: the Result row gains one part for its club name (class `cn`, measured on its
  `.club` box by `fits`, since the name inside it holds its own content) with the rule above, and
  the Name in whole words rule's selector no longer lists `.club .cn`, which the new part covers. No text style, colour, spacing or corner value
  is added. #231's fix approved in chat, 2026-10-23; visual details are the coordinator's under
  docs/design/design_standard.md, approved in chat, 2026-11-16.

impact_map: >
  writers: none; site_v2/src/styles/system.css only, and the component registry with its generated
  table. downstream: site_v2/dist only. The rule applies to every `.club .cn` (result, meeting and
  goal rows on match, Team and Player pages) and changes a line break only where a hyphen-joined
  word is wider than its line. guard: docs/design/components.yml is read by
  scripts/check_component_registry.py (which also writes the element table of
  docs/wireframes/block_standard.md), scripts/check_design_inventory.py and
  scripts/design_inventory.py, scripts/parts_page.py and site_v2/scripts/check-term-list.test.mjs; no
  measurement kind is added. layer_rules: not applicable; no computation. deploy_order: none;
  deploy:site-v2 is manual. blast_radius: the line break of a club name wider than its line, below
  700px; no text, link, number or block changes.

acceptance_criteria:
  - A club name in a result, meeting or goal row never runs past its space at 260, 280 and 320px, in EN, DE and FI.
  - A hyphen-joined word that fits its line stays whole; where it is wider than the line it breaks at its hyphens.
  - A row whose names fit keeps its form and its look.
  - The block standard states the rule, and the design check measures it.
  - No pin rises.

approved_design:
  - home: #127
  - competitions: #128
  - competition: #129
  - matches: #130
  - match: #132
  - teams: #133
  - team: #134
  - players: #135
  - player: #136

depends_on:
  - none: !488 is merged (main 3dddb7af)

shared_files:
  - site_v2/src/styles/system.css
  - docs/design/components.yml
  - tests/fixtures/component_registry/baseline.json
  - tests/fixtures/design_inventory/baseline.json
  - tests/fixtures/design_inventory/baseline_quick.json
  - tests/fixtures/design_inventory/baseline_quick_fi.json
  - tests/fixtures/chart_screenshots/*

decisions_taken: >
  The coordinator's request of 2026-11-19: the smallest fix in the shared part, applied sitewide,
  measured against the approved Recent matches design. Root cause: the opponent name, not the
  competition and date, is the part that runs past the row. wholeWords.mjs wraps "Weston-super-Mare"
  in `.nb` (white-space: nowrap), the name sits in `.club`, a flex item whose automatic minimum width
  is that whole word, so in the row's last form (`fit-two`) nothing is left to give. The fix is one
  rule in the stylesheet: the no-break span inside a club name is an inline-block (as wide as its
  line at most, by the shrink-to-fit rule) that wraps inside itself, so the word moves whole to the
  next line like any atomic inline and breaks at its hyphens only where it is wider than the line. No new
  mechanism, dependency or cost; the build's no-break pass is unchanged.

decisions_reserved:
  - none

done_when:
  - node --test site_v2/src/lib/fitBlocks.test.mjs site_v2/src/lib/wholeWords.test.mjs passes.
  - python scripts/check_component_registry.py passes; no pin rises.
  - A sample build with a hyphen-joined opponent injected shows no row wider than its box at 260, 280 and 320px in EN, DE and FI.
  - python scripts/ci_local.py --mr is green.
