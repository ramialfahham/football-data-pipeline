# Rendered pages — before and after

"Before" is main at c1084493, "after" this branch, both served by the dev server from the committed
sample. A Playwright sweep loaded every page with a tab bar: the Bundesliga overview, matches and
stats pages, all 34 Team pages and all 72 Player pages, in EN, DE and FI, at 280, 320, 375 and
1010px. For each it recorded every tab bar's tab widths, whether a label is cut, and the
sideways scroll. At 375 and 1010px it also took a full-page screenshot with images hidden, the
visible text and the links.

## Tab widths

- 1,308 tab bars measured. At 320, 375 and 1010px every bar's tabs are equal to within 1px (981
  of 981 bars).
- At 280px, 217 of 327 bars are equal. In the other 110, one label needs more than its share and
  takes it: EN "Performance" (34 bars), DE "Nationalmannschaft" (39), FI "Yleiskatsaus" (37).
- 0 labels cut, 0 pages scroll sideways.

## Pixels, text and links

- 654 screenshots: the same visible text and the same links on every page.
- 456 screenshots change, all inside the tab bar's band. The bars with equal tabs before (a single
  tab, or labels of one length) do not change.
- One screenshot (`/de/spieler/j-kimmich-502/` at 1010px) differed outside its tab bar in the
  first sweep. Two fresh renders of the branch match the first "after" capture byte for byte, and
  a fresh render with the old rule differs from it only in rows 215–241, inside the tab bar
  (198–243). The first "before" capture of that page was a bad render.
