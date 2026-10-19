# Task contract — the shared fold

objective: >
  The site's fold keeps its control between the shown and the revealed rows and reads "Show all
  {n}" when open. Make it one shared, scriptless fold whose control stays under the shown rows and
  reads "Show less" once open, on every page that renders it: Home, the Matches page and the
  Matches day page.

refs: >
  #221, the shared fold (https://gitlab.com/rami.al-fahham/football-data-pipeline/-/work_items/221);
  #127, Home's approved design; #130, the Matches page's approved design; #133, the Teams page's
  approved design, which names this fold. Mock and plan approved in chat, 2026-10-19.

scope_paths:
  - site_v2/src/components/ui/Fold.astro
  - site_v2/src/components/home/HeroFixtures.astro
  - site_v2/src/components/matches/MatchesDay.astro
  - site_v2/src/styles/system.css
  - site_v2/src/i18n/strings.ts
  - site_v2/src/specs/index.spec.json
  - site_v2/src/specs/matches/index.spec.json
  - site_v2/src/specs/matches/day.spec.json
  - docs/wireframes/block_standard.md
  - docs/wireframes/10_home.md
  - design-mocks/gen_home.py
  - design-mocks/gen_matches_hub.py
  - design-mocks/check_home.py
  - tests/test_no_decision_history_in_code.py
  - tests/test_no_decision_history_in_docs.py
  - tests/test_sentence_length_in_docs.py
  - .claude/task/contract.md
  - .claude/task/review.md
  - .claude/task/review_input.patch
  - .claude/task/acceptance_evidence.md
  - .claude/task/rendered_page_evidence.md

impact_map: >
  writers: no data writer changes; the export and every payload are untouched.
  downstream: the fold markup is rendered by HeroFixtures.astro (Home) and MatchesDay.astro (the
  Matches page and the Matches day page), its only two renderers (git grep fxmore). The new
  Fold.astro has these two importers. The .fxmore rules in system.css have no other reader; the
  mocks gen_home.py and gen_matches_hub.py inline system.css and emit the fold, so they move with
  it.
  layer_rules: presentation only; the rows, their count and their order are what the page is served.
  deploy_order: none; deploy:site-v2 is manual and builds from the export.
  blast_radius: the three locale Home pages, Matches pages and Matches day pages; the fold's markup
  and its CSS; one new copy key in EN, DE and FI.

approved_design:
  - home: #127
  - matches: #130

acceptance_criteria:
  - "On Home, the Matches page and the Matches day page, a competition with more than three matches shows its first three, then 'Show all {n}' with the chevron pointing down; n is the competition's match count."
  - "Opened, the remaining matches follow the third directly in the same list, with the same divider between every two rows and no extra line or gap."
  - "Opened, the control sits under the last match and reads 'Show less' (DE 'Weniger anzeigen', FI 'Näytä vähemmän') with the chevron pointing up; clicking it closes the list."
  - "The fold needs no JavaScript, and every match row is in the page's HTML."
  - "The design check measures the Fold on Home, the Matches page and the Matches day page at 375, 700 and 1010 px."

decisions_taken: >
  Plan approved in chat, 2026-10-19: the copy EN "Show less", DE "Weniger anzeigen", FI "Näytä
  vähemmän" under the key homeShowLess; the fold is the site's existing scriptless checkbox toggle
  (the filters' and tabs' pattern), so a closed fold is not opened by the browser's find-in-page;
  the texts of the block standard's Fold row and of 10_home.md §5 are the ones in the approved plan.
  No new mechanism, no recurring cost.

decisions_reserved:
  - none: the Teams page renders this fold in its own build (#222).

done_when:
  - npm run build in site_v2 passes (prebuild tests, astro build, audit-seo, check-built-pages).
  - python scripts/check_design_inventory.py --dist site_v2/dist passes for Home, the Matches page and the Matches day page at 375, 700 and 1010px.
  - The full pytest suite and the offline gates pass.
  - Reviewers per review_routing.json pass.

amendments: (none)
