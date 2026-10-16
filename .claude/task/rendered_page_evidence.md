# Rendered page evidence — the played match page

New markup, CSS and copy on the match page; markup only (a `data-fixture` attribute and a link
when the match's page is built) on the match rows of other pages. Read from the built output of
`npm run build` in site_v2 with the committed samples plus seven played payloads, through the
Browser pane: the accessibility tree and page text (`get_page_text`), and computed styles and
geometry read by script on the rendered page. Screenshots do not work in this pane.

- Every played state renders its blocks in the approved order (EN read in full; DE and FI by the
  build's audit, which found every description and title localised in all 2,560 pages):
  full time (Hoffenheim–Dortmund), extra time (Halle–Schalke), penalties (Viktoria Köln–Nürnberg),
  played then awarded (Union Berlin–Bochum), abandoned then awarded (Nantes–Toulouse), not played
  (Tours–Lorient), no player stats (Wingate–Bedford).
- 1010px (Hoffenheim–Dortmund): `.vs.score` 40px regular ink, the winner's number bold; the goal
  row's second line 14px ink-2; the column heads 13px bold muted, both Substitutes heads 14px
  below the last starter, the two teams' sheet rows level (top offset 0px).
- 375px (same page, mobile emulation): `.vs` hidden, each team's `.sg` shown at 24px and in the
  accessibility tree; the Line-ups columns stacked; no horizontal scroll
  (`scrollWidth` = viewport width).
- Empty states read as approved: Union Berlin–Bochum's Match stats shows "The teams' numbers are
  not recorded for this match." (its served numbers outside the Goals group are all empty);
  Wingate–Bedford's four goals without a scorer name show "–" in the name.
- The design check (`scripts/check_design_inventory.py --dist site_v2/dist`, Playwright, as CI's
  validate:ui runs it): 24 pages × 3 viewports (375, 700, 1010px) × the published languages, 174
  renders, 0 failures, 30 warnings, every one the header row at 700px that main carries; the new
  Played match page row measures Match header winner, Goal row meta, Comparison element and
  Column head.
- Every other page: its visible text is identical to main's build on all 2,539 pages main builds;
  429 links are added, none removed.
