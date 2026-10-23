# Task contract — the shared Filter bar

objective: >
  The Competitions, Matches and Matches day pages show the approved Filter bar: each filter offers
  only the types and regions the page's rows carry and is absent with fewer than two real choices;
  a choice that would leave no row beside the other filter's choice is removed and comes back when
  it fits; the buttons show while each row of buttons fits on one line, otherwise a dropdown per
  filter in the Filter row's sunk box, side by side while each holds its longest choice and stacked
  full width below that, decided per block and language by the shared fit script; buttons and
  dropdowns hold the same choice; the open list is drawn in the site's design where the browser
  supports it. The block standard states the rules and the design check measures them.

refs: >
  #223, the shared Filter bar
  (https://gitlab.com/rami.al-fahham/football-data-pipeline/-/work_items/223), design approved in
  chat, 2026-10-20; #128 and #130, the approved designs of the pages that change; the fit rule
  approved in chat, 2026-10-22 and 2026-10-23. Plan approved in chat, 2026-10-23.

scope_paths:
  - site_v2/src/components/competitions/FilterRows.astro
  - site_v2/src/components/competitions/CompetitionIndexGrid.astro
  - site_v2/src/components/matches/MatchesDay.astro
  - site_v2/src/styles/system.css
  - site_v2/src/i18n/strings.ts
  - site_v2/src/lib/filterBar.mjs
  - site_v2/src/lib/filterBar.test.mjs
  - site_v2/src/lib/fitBlocks.mjs
  - docs/wireframes/block_standard.md
  - scripts/design_inventory.py
  - scripts/check_design_inventory.py
  - tests/test_design_inventory.py
  - tests/fixtures/design_inventory/green.html
  - tests/test_no_decision_history_in_docs.py
  - tests/test_no_decision_history_in_code.py
  - tests/test_sentence_length_in_docs.py
  - .claude/task/contract.md
  - .claude/task/review.md
  - .claude/task/review_input.patch
  - .claude/task/acceptance_evidence.md
  - .claude/task/rendered_page_evidence.md

impact_map: >
  writers: no data writer changes; the export and every payload are untouched.
  downstream: FilterRows.astro is rendered by CompetitionIndexGrid.astro (the Competitions page)
  and MatchesDay.astro (the Matches page and every Matches day page). The row-hiding rules in
  system.css (`#filter-…:checked ~ .categories …`) and the Competitions page's empty-category script
  read the same radios. fitBlocks.mjs is loaded on every page by Layout.astro; its new kinds act only
  where a Filter bar renders. The design check reads block_standard.md through design_inventory.py.
  layer_rules: presentation only; which rows a page is served and their order are unchanged; the
  bar selects among the page's own rows.
  deploy_order: none; deploy:site-v2 is manual and builds from the export.
  blast_radius: the filter rows of the Competitions, Matches and Matches day pages in EN, DE and FI;
  two new copy keys; one new shared script; two new fit kinds.

approved_design:
  - competitions: #128
  - matches: #130

acceptance_criteria:
  - "On the Competitions, Matches and Matches day pages in EN, DE and FI, each filter offers only the choices its rows carry, and a filter with fewer than two real choices is absent."
  - "Every combination the bar offers shows at least one row; a removed choice comes back once the other filter allows it."
  - "At 280, 320, 375, 430, 700, 768, 1010 and 1440px the bar shows buttons when they fit on one line and dropdowns otherwise, and no page scrolls sideways."
  - "Buttons and dropdowns always hold the same choice."
  - "The dropdowns' first choices read All types / Alle Arten / Kaikki tyypit and All regions / Alle Regionen / Kaikki alueet."
  - "The design check passes on every built page it lists."

decisions_taken: >
  Approved in chat, 2026-10-20: the Filter bar design and its copy (#223). Approved in chat,
  2026-10-22 and 2026-10-23: a block switches form only when its content no longer fits, decided
  per block and language by the shared fit script. Readings of the approved design: the dropdowns
  reuse the existing filterByType and filterByRegion names; without the script the buttons show and
  wrap, which still filters. No new dependency, no recurring cost.

decisions_reserved:
  - The Team page's competition filter and the Teams page's filter, built with #134 and #222.

done_when:
  - npm run build in site_v2 passes (prebuild tests, astro build, audit-seo, check-built-pages).
  - python scripts/check_design_inventory.py --dist site_v2/dist passes.
  - The full pytest suite and the offline gates pass.
  - Reviewers per review_routing.json pass.

amendments:
  - The code-history pin moves down one line, because the Filter bar retires the `.seg.wrap` comment
    that carried history; the pin only moves down, so this records the cleanup.
