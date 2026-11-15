# Task contract — phone fixes, the rules approved on the issue (#231 audit, MR 1b)

objective: >
  The remaining phone breaks that a rule approved on #231 settles: every link and button has a
  44px tap area; the matchday picker takes the short date where the full date does not fit; a
  linked row has square edges; a separator dot never ends or starts a line; a Team page competition
  row keeps its space in "Goals 25:6"; the header fits at 260-270px; explainers on the Team page
  never name the page's own team.

refs: >
  #231 (narrow-screen rules; the comments of 2026-11-12 on tap targets, the day picker date and
  separators); go-live issue #290 (gate item 1). MR 1 (!439) is merged. Left out, still the CPO's:
  the sitewide tab bar, scrollbar-gutter, country-name localisation, the competition-row note line
  (#250 MR 2).

scope_paths:
  - .claude/task/231-phone-fixes-mr1b/
  - site_v2/src/styles/system.css
  - site_v2/src/layouts/Layout.astro
  - site_v2/src/lib/wholeWords.mjs
  - site_v2/src/lib/wholeWords.test.mjs
  - site_v2/src/lib/dotEdges.mjs
  - site_v2/src/lib/dotEdges.test.mjs
  - site_v2/src/lib/fitBlocks.mjs
  - site_v2/src/lib/fitBlocks.test.mjs
  - site_v2/src/lib/format.ts
  - site_v2/src/i18n/strings.ts
  - site_v2/src/components/matches/MatchesDay.astro
  - site_v2/src/components/team/TeamCompetitions.astro
  - site_v2/src/components/fixture/PlayerRow.astro
  - site_v2/src/components/player/PlayerHeader.astro
  - site_v2/src/components/teams/TeamIndex.astro
  - site_v2/src/pages/[[]lang]/[[]teams]/[[]team].astro
  - docs/wireframes/block_standard.md
  - tests/test_phone_fixes_231.py
  - tests/test_phone_built_pages_231.py
  - tests/test_check_chart_screenshots.py
  - tests/fixtures/design_inventory/baseline.json
  - tests/fixtures/design_inventory/baseline_quick.json
  - tests/fixtures/chart_screenshots/

impact_map: >
  writers: none; page templates, one build-step module (wholeWords.mjs, runs in middleware.ts over
  every page's body text), one client script, the stylesheet, three label strings and the block
  standard. No dbt model, no export script.
  downstream: site_v2/dist only. wholeWords.mjs rewrites every middle dot between items in a page's
  body text into a span; the text a reader copies is unchanged.
  layer_rules: not applicable; consumption layer, no computation added.
  deploy_order: none; deploy:site-v2 is manual.
  blast_radius: every page's middle dots (markup only), the tap area of every link and button
  (layout under stacked links), linked rows (square edges, no side overhang), the day picker's
  title, the Team page competition row, the header at 260-270px, one explainer string in EN, DE
  and FI. Counts before and after are in the MR. Chart pins and the design-inventory pins change
  only by lowering, or by renewal from the CI image's own output.

acceptance_criteria:
  - On the built site at 280-768px in EN, DE and FI every link and button measures at least 44px in height and width, or is a link inside running text. The header's three icon buttons are 44px high and 44px wide where they fit beside the name; where they do not, they shrink to no less than 34px wide, the width the registry gives the search button.
  - On day pages, where the full date does not fit on one line, the picker title shows the short date; where it fits it shows the full date.
  - No linked row (fixture row, table row, list row) has rounded corners or sticks out past its block's edge.
  - At 280-768px in EN, DE and FI no middle-dot separator is the first or the last thing on a line; it is hidden when its item starts a line.
  - The Team page competition row reads "Goals 25:6", with a space.
  - The site header does not scroll sideways at 280-300px. At 260-270px it still does by up to 15px: the room comes only from a new width rule, and the design checks pin the widths the stylesheet names, so a new one needs the CPO.
  - No explainer on the Team page names the page's own team, in EN, DE and FI.
  - At 1010px and wider no page changes except the picker and tap areas where they now differ by the rules above.
  - The sweep shows no new break class against the gitlab/main baseline; no pin baseline is raised.

approved_design:
  - competitions: #128
  - competition: #129
  - matches: #130
  - match: #132
  - statistics: #139
  - teams: #133
  - team: #134
  - players: #135
  - player: #136

decisions_taken: >
  Each change applies a rule the CPO approved on #231: tap targets (comment of 2026-11-12, every
  link and button at least 44px, sitewide, the text and look unchanged, closely stacked links gain
  the spacing they need); the day picker date (2026-11-12); separators (2026-11-12, a dot never
  ends or starts a line, it travels with the item after it and disappears when that item moves to
  its own line); explainers (#230, 2026-11-12, an explainer never names the page's own team or
  player). Square linked rows, the "Goals 25:6" space and the header padding at 300px are defects
  against rules already written (the linked-row note in the stylesheet; the fact-row standard).
  The separator rule is built once, in the build-step text pass and one client script, not in
  forty templates. Items the CPO has not ruled are left out (see refs). The short-date form is
  built from the language's own weekday and day.month pattern ("SU 18.10."), since the code has no
  Home form to reuse.

decisions_reserved:
  - none: the rules are approved on the issue; questions go to the coordinating session.

done_when:
  - The built site passes the new built-page test at 280-768px EN, DE, FI for tap areas, dots, row corners and header overflow.
  - validate:ui's script list runs green in the CI image (design inventory, chart screenshots, registry, i18n, font coverage).
  - The full pytest, the site's node tests and the offline gates pass.

amendments: []
