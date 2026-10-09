# Rendered page evidence — the future match page

Two sources, no screenshot (the pane's screenshot tool fails in this environment):
- The dev server (`npm run dev`) in the Browser pane, measured by DOM script for sideways scroll and for elements
  past the edge.
- check_design_inventory.py with the committed block_standard.md, run against a scratch build holding only this
  page. The Match page entry expects the parts both match-page states show; every other row is measured where it
  appears.

The page is a gitignored copy of the real Bayern München vs Borussia Dortmund payload: fixture of 31 Oct, exported
once from prod, 129 MB read. It is served under a `-check` slug and was deleted after the check.

| Page | 375px | 700px | 1010px |
|---|---|---|---|
| /en/bundesliga/matches/…-check/ | document 375px wide; 0 elements of the page content past the edge; blocks Match preview, Head to head, Next matches | document 707px; page content 0 past the edge | document 995px; page content 0 past the edge |
| /de/…, /fi/… | design check 0 failures | design check 0 failures; Header row warning | design check 0 failures |

The design check reports 0 failures in 9 renders (3 widths, 3 languages). Its 3 warnings are the Header row at
700px (707, 731 and 709px against 700): the site header's controls, as on every page today.
