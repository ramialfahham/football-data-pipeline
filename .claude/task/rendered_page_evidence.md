# Rendered page evidence — a table that opens with the name, in its narrow form

Method: the dev server (`npm run dev` in `site_v2`, the committed sample data) in the Browser pane. Each page
loads in a same-origin iframe at the listed width with no border. The Performance tab is checked, and a resize
event lets `fitBlocks.mjs` mark each table. For every visible row of a table whose rows open with the name
cell, it records the table's mark (fit-one, fit-two) and the name cell's left edge against its row's, read with
`getBoundingClientRect`.

Page: Bayern München, the Team page, Performance tab. The tables are Compared with last season (`yoyt`) and
the deserved points table (`dpm`).

| Run | Main, before | This branch |
|---|---|---|
| DE 280 | fit-two names 79px from the row's left | all 18 names at 0px: 4 dpm fit-one, 8 yoyt fit-one, 6 yoyt fit-two |
| FI 280 | fit-two names 79px from the row's left | all 18 names at 0px: 4 dpm fit-one, 5 yoyt fit-one, 9 yoyt fit-two |
| FI 320 | (not measured) | all names at 0px: 2 yoyt rows fit-two |
| EN 280–1010, DE 320–1010, FI 360–1010 | fit-one | every table fit-one, all names at 0px |

- **Main, before:** on main at 280px in DE, two fit-two tables placed the name in grid column 2, at the first number column; FI had three.
- **This branch:** every name starts in column 1 at all 18 width-and-language runs.
- **The deserved points table** is fit-one at every width, so it does not change.
- **Rank tables:** the Bundesliga page at 280px in DE has 36 visible rows, all opening with the rank. Their names stay in column 2, unchanged.
