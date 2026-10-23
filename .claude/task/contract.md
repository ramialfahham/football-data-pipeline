# Task contract — pages hold on narrow screens

objective: >
  On every approved page, at every width from 280px, in EN, DE and FI, a team name never splits
  inside a word and never runs outside its space; a table row that no longer fits on one line
  takes two lines (rank, crest and name, then the numbers under their heads); a block of fact rows
  stacks only when its longest row no longer fits on one line; the site header fits. One shared
  script measures each block per language; without it a narrow block shows the two-line form.
  Wider screens are unchanged. The block standard states the rules; the design check measures
  whole words and that every built page's blocks carry the script's mark.

refs: >
  #231, pages break on narrow screens
  (https://gitlab.com/rami.al-fahham/football-data-pipeline/-/work_items/231), fix approved in
  chat, 2026-10-23; the fact-row rule approved in chat, 2026-10-22; #127, #128, #129, #130 and
  #132, the approved designs of the pages that change. Plan approved in chat, 2026-10-23.

scope_paths:
  - site_v2/src/styles/system.css
  - site_v2/src/layouts/Layout.astro
  - site_v2/src/lib/fitBlocks.mjs
  - site_v2/src/lib/fitBlocks.test.mjs
  - docs/wireframes/block_standard.md
  - scripts/design_inventory.py
  - scripts/check_design_inventory.py
  - tests/test_design_inventory.py
  - tests/fixtures/design_inventory/green.html
  - tests/test_no_decision_history_in_docs.py
  - tests/test_sentence_length_in_docs.py
  - .claude/task/contract.md
  - .claude/task/review.md
  - .claude/task/review_input.patch
  - .claude/task/acceptance_evidence.md
  - .claude/task/rendered_page_evidence.md

impact_map: >
  writers: no data writer changes; the export and every payload are untouched.
  downstream: `.ctab` is every table built on the standings grid: the competition page's league
  table and Deserved points table (DeservedTable.astro) and the Rankings boards (`.ctab.rkt`).
  `.frow` is the fact row (the competition page's Season pulse, the Team page). `.fxrow .side .nm`
  is the match row's team name (Home, Matches, the competition page). `.club .cn` is the club name
  in the match page's result rows. `.header-in` is the site header on every page (SiteHeader.astro
  inside Layout.astro). The script is loaded once by Layout.astro on every page. The design check
  reads block_standard.md through design_inventory.py.
  layer_rules: presentation only; what each page is served and its order are unchanged.
  deploy_order: none; deploy:site-v2 is manual and builds from the export.
  blast_radius: narrow screens on every approved page in EN, DE and FI; the header gap on every
  page at its narrowest; the Team and Player pages get the header and name rules only; one new
  shared script; one new measured property in the design check.

approved_design:
  - home: #127
  - competitions: #128
  - competition: #129
  - matches: #130
  - match: #132

acceptance_criteria:
  - "At 280, 320, 375, 430, 768 and 1010px, on every approved page in EN, DE and FI, no team name splits inside a word or runs outside its space."
  - "At the same widths, no approved page scrolls sideways, except the filter rows of the Competitions and Matches pages, which the Filter bar (#223) replaces."
  - "A table row shows rank, crest, name and every number; where they do not fit on one line, the numbers stand on a second line under their column heads."
  - "A block of fact rows is side by side when its longest row fits on one line, and stacked otherwise."
  - "At 1010px and 1440px every approved page measures as on main."
  - "The design check's whole-words property passes on every built page it lists."

decisions_taken: >
  Approved in chat, 2026-10-23: a name wraps only between words; a table row that does not fit
  takes two lines and drops nothing; one shared script decides each block's form per language;
  without the script a block narrower than 600px shows the two-line form. Approved in chat,
  2026-10-22: fact rows stack only when the block's longest row no longer fits. Approved in chat,
  2026-10-23, with the plan: the Team and Player pages, whose new designs are built in their own
  MRs, take only the header change. The built pages render no table, fact row, match row or club
  name in a match row; the header is shared by every page through Layout.astro. The Teams menu
  page has no built page yet. Approved in chat, 2026-10-23: the design check fails a built page
  whose table, fact-row block or header carries no fit-one or fit-two mark (the Fitted block row,
  measured as fit-marked); the check's test page carries the marks. No new dependency, no
  recurring cost.

decisions_reserved:
  - The filter rows' narrow form, built with the Filter bar (#223).
  - The Team page's and the Player page's narrow forms, each in its own build (#134, #136).

done_when:
  - npm run build in site_v2 passes (prebuild tests, astro build, audit-seo, check-built-pages).
  - python scripts/check_design_inventory.py --dist site_v2/dist passes.
  - The full pytest suite and the offline gates pass.
  - Reviewers per review_routing.json pass.

amendments:
  - Approved in chat, 2026-10-23: the design check's fixture of a correct built page carries the
    fit marks a built page now carries, so the check's own tests keep a passing page.
