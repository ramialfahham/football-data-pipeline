# Task contract — the match page's Show all metrics switch and team names

objective: >
  The played match's Match stats and the upcoming match's Form comparison show the key team
  metrics by default; a "Show all metrics" switch at the top right shows every metric in its
  place, the order never changing, and a group heading with no key row is hidden while it is off.
  The team names over the comparison read 14px, semi-bold, ink. The switch enters the block
  standard.

refs: >
  #132 (the match page; the switch and the names approved in chat, 2026-10-22, note 4069141243);
  #134 (the switch's copy in EN, DE and FI, approved in chat, 2026-10-22, note 4069024967).

scope_paths:
  - site_v2/src/components/ui/MetricSwitch.astro
  - site_v2/src/components/fixture/MetricComparison.astro
  - site_v2/src/components/fixture/MetricRow.astro
  - site_v2/src/components/fixture/MatchStats.astro
  - site_v2/src/components/fixture/FormSegment.astro
  - site_v2/src/lib/comparisonGroups.ts
  - site_v2/src/styles/system.css
  - site_v2/src/i18n/strings.ts
  - docs/wireframes/block_standard.md
  - .claude/task/contract.md
  - .claude/task/review.md
  - .claude/task/review_input.patch
  - .claude/task/acceptance_evidence.md
  - .claude/task/rendered_page_evidence.md

impact_map: >
  writers: none; the export, the warehouse and the served data are unchanged (is_key_metric is
  already served in metric_rows.json). downstream: the match page's Match stats and Form
  comparison blocks; the new switch component and its CSS are read by nothing else yet.
  layer_rules: display only, no metric fact computed. deploy_order: none; deploy:site-v2 is
  manual. blast_radius: two blocks of the match page, and the `.mp .formhead .h` rule, which only
  those two blocks use.

approved_design:
  - match: #132

acceptance_criteria:
  - "With the switch off, Match stats and Form comparison show only the rows whose is_key_metric is true, and a group heading with no key row is hidden; with it on, every shown row stands in catalogue order."
  - "The switch reads Show all metrics / Alle Kennzahlen anzeigen / Näytä kaikki tunnusluvut, sits at the top right of the comparison, is off by default, neutral grey when on, needs no script and is announced as a switch."
  - "The team names over the comparison are 14px, weight 600, ink."
  - "block_standard.md lists the Metric switch and the Comparison team name, and the Played match page expects both."

decisions_taken: >
  Approved in chat, 2026-10-22: the switch on Match stats and Form comparison, the key metrics by
  default, every metric in its place when on, a heading without key rows hidden while off, top
  right, neutral grey when on; the team names 14px semi-bold ink; the copy in three languages.
  The block standard rows approved with the plan, 2026-10-25. Readings: the switch appears only
  when the block shows both a key row and another row; the rows behind it carry the class
  `nonkey`. No new dependency and no recurring cost.

decisions_reserved: []

done_when:
  - The offline gates, check_page_css.py and the full pytest suite pass.
  - The dev server shows both states on a played and an upcoming match in EN, DE and FI.
  - check_design_inventory.py passes on a local build of the match pages.
  - Reviewers per review_routing.json pass.

amendments: []
