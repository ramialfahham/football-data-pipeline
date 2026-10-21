# Task contract — one page width

objective: >
  The header, the content and the footer share one maximum width of 960px on every page whose
  design is approved; the pages keep their one column. The Team page and the Player page keep
  today's widths (content 680px, header and footer 1100px) until their own designs are approved.
  The design check measures the width.

refs: >
  #224, one page width (https://gitlab.com/rami.al-fahham/football-data-pipeline/-/work_items/224),
  design and build scope approved in chat, 2026-10-20; #127, #128, #129, #130 and #132, the
  approved designs of the pages that change. Plan approved in chat, 2026-10-20.

scope_paths:
  - site_v2/src/styles/system.css
  - site_v2/src/layouts/Layout.astro
  - site_v2/src/pages/[[]lang]/[[]teams]/[[]team].astro
  - site_v2/src/pages/[[]lang]/[[]players]/[[]player].astro
  - scripts/design_inventory.py
  - tests/test_design_inventory.py
  - docs/wireframes/block_standard.md
  - docs/wireframes/00_overview.md
  - docs/wireframes/08_browse.md
  - docs/wireframes/09_chrome.md
  - docs/wireframes/10_home.md
  - tests/test_no_decision_history_in_docs.py
  - tests/test_sentence_length_in_docs.py
  - .claude/task/contract.md
  - .claude/task/review.md
  - .claude/task/review_input.patch
  - .claude/task/acceptance_evidence.md
  - .claude/task/rendered_page_evidence.md

impact_map: >
  writers: no data writer changes; the export and every payload are untouched.
  downstream: .inner is the content column of every page (git grep 'class="inner'): Home,
  Competitions, a competition's overview, matchdays and rankings, the Matches page and the Matches
  day page (MatchesDay.astro), the match page, the Team page and the Player page. .header-in and
  .footer-in are rendered once each by SiteHeader.astro and SiteFooter.astro inside Layout.astro,
  which every page except the root redirect stub uses. .shell has no reader. The design check reads
  block_standard.md through design_inventory.py.
  layer_rules: presentation only; what each page is served and its order are unchanged.
  deploy_order: none; deploy:site-v2 is manual and builds from the export.
  blast_radius: the width of the content column, the header row and the footer on every approved
  page in EN, DE and FI; the Team and Player pages unchanged; one new Layout prop; one new measured
  property in the design check.

approved_design:
  - home: #127
  - competitions: #128
  - competition: #129
  - matches: #130
  - match: #132

acceptance_criteria:
  - "At 1440px, on every approved page in EN, DE and FI, the header, the content and the footer are 960px wide and share both edges."
  - "The Team page and the Player page measure as on main: content 680px, header and footer 1100px."
  - "At 375px every page measures as on main."
  - "No page scrolls sideways and the header fits, at 700, 800, 1010 and 1440px, in EN, DE and FI."
  - "The design check's Page width row passes on every built page it lists."

decisions_taken: >
  Approved in chat, 2026-10-20: one width of 960px for the header, the content and the footer; the
  Team and Player pages keep today's widths until their designs are approved. The unused .shell
  follows the one width. The two pages opt out through a Layout prop that sets a body class; no new
  dependency, no recurring cost.

decisions_reserved:
  - The Team page's width (#134) and the Player page's width (#136), each in its own design review.

done_when:
  - npm run build in site_v2 passes (prebuild tests, astro build, audit-seo, check-built-pages).
  - python scripts/check_design_inventory.py --dist site_v2/dist passes.
  - The full pytest suite and the offline gates pass.
  - Reviewers per review_routing.json pass.

amendments: (none)
