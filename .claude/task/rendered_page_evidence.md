# Rendered page evidence — Compared with last season on the Team page

Method: this branch's dev server (`npm run dev` in `site_v2`, the committed sample data) in the Browser pane.
Each page loads in a same-origin iframe at the listed width with no border. The Performance tab is checked,
then the metric switch is set off and on in turn. The geometry is read with `getBoundingClientRect` and
`getComputedStyle`. The gap is measured as the design check measures `gap(next)`: from the group heading's
bottom to the top of the table's first line of text. The box gap is from the heading's bottom to the table's top.

Page: Bayern München, the Team page, Performance tab. The switch-off view shows 6 metric groups and the
switch-on view shows 8. All 18 runs (280, 320, 360, 375, 700 and 1010px, in EN, DE and FI) give the same values:

| Measure | Switch off | Switch on |
|---|---|---|
| Groups / head rows inside their table | 6 / 6 | 8 / 8 |
| Gap, text / box | 26px / 26px in every group | 26px / 26px in every group |
| Stripes per group, 1 = tinted | `01 · 010 · 010 · 01 · 0 · 010` | `010 · 0101010 · 01010 · 010101 · 0101 · 01 · 01 · 0101` |
| Name cell | 14px, 600 | 14px, 600 |

- **Uneven head:** every group's head holds labels of different heights. At 700 and 1010px in FI, "Viime kausi" takes two lines beside "Tämä kausi" on one. The gap stays 26px, because the head aligns its labels at the top.
- **Before the fix:** on this machine, the same FI page at 700 and 1010px measured a 31.6px gap, with the labels centred.
- **Other pages:** Borussia Dortmund (EN) and Inter (FI) were measured the same way at all six widths. All four rules hold, and none of the pages scrolls sideways.
