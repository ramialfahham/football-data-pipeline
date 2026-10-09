# Acceptance evidence — the footer repeats the menu, and the menu marks the page's section

Read from `astro build` of the committed sample (2,538 locale pages; audit-seo and check-built-pages OK) and from a
build of main from the same sample. A script parses every built page in both; the dev-server check covers the look.

criteria_demonstrated:
  - THE FOOTER ROW. On all 2,538 pages the footer reads the six menu items in the menu's order, then About and
    Imprint (pending). EN: Competitions · Matches · Teams · Players · Standings · Statistics · About · Imprint
    (pending); DE: Wettbewerbe · Spiele · … · Impressum (in Vorbereitung); FI: Kilpailut · Ottelut · … ·
    Vastuutiedot (tulossa). On every page each footer item is a link exactly when the menu's item is:
    Competitions and Matches are links, the rest spans.
  - THE MARKED SECTION. On every page but the three Home pages exactly one item carries aria-current="true" and
    class `on`, in the menu and in the drawer, at the section's place. Pages by section: Competitions 2,037,
    Matches 174, Teams 108, Players 216; Home marks none. No footer item is marked.
  - THE LOOK. On a match page at 1010px the marked "Competitions" is ink at weight 700 with the inset 2px ink
    line; "Matches" stays muted at 600 with no line. At 375px the drawer's marked item is ink at 700, the others
    600, and the page does not scroll sideways.
  - NO OTHER TEXT. With the footer left out, every page's text equals main's build, and both builds hold the
    same pages.
  - GATES. npm test 117 pass; check_copy_gate, check_page_css, and check_design_inventory (0 failures in 165
    renders) pass; pytest tests/ 1490 passed, 2 skipped.
