# Rendered page evidence — the Team page

Checked on the v2 dev server (`npm run dev`, the branch's committed samples) in the Browser pane,
with the viewport emulated at 280px, 375px and 1100px wide, each page loaded fresh at its width.
Tools: computed styles, element geometry and visibility read with the pane's script tool, and the
page text. No screenshot: the pane's screenshot does not work on this machine, so every observation
below is a measured value.

## Bayern München (`/en/teams/bayern-munchen/`)

| Check | 280px | 375px | 1100px |
|---|---|---|---|
| Sideways overflow (`scrollWidth > clientWidth`) | none | none | none |
| Competition row, `@container (max-width: 340px)`: `.tc-right` / `.tc-rank2` display | none / block (narrow form) | block / none | block / none |
| Squad grid columns (`.sqgrid`) | 1 | 1 (343px) | 2 (440px each) |
| Strip plot list width; strip on the row's second line (`grid-row-start`) | 248px; 2 | 343px; 2 | 904px; auto (one line) |
| Scatter plot: `.dp-wide` / `.dp-narrow` display | none / block | none / block | block / none |
| Scatter marks: team dot / other club dot, rendered width | 10px / 6px | 10px / 6px | 10px / 6px |
| League strips shown, switch off / on | 14 / 33 | 14 / 33 | 14 / 33 |
| Season table rows shown, switch off / on | 14 / 33 | 14 / 33 | 14 / 33 |
| Metric groups hidden with the switch off (no key row) | 2 | 2 | 2 |
| First season table's stripes, off / on (s = tinted) | `s-` / `s-s` | `s-` / `s-s` | `s-` / `s-s` |

- Clean sheets reads "Clean sheets · percentage 29%, 5th" in the league strip and "29% / 57% ▼" in
  the season table: the share, `clean_sheets_pct`.
- Matches tab filter: All, Bundesliga, DFB-Pokal, UEFA Champions League. With DFB-Pokal chosen, only
  the Results section shows (2 rows); the Upcoming section, which holds no DFB-Pokal match, is
  hidden with its heading.

## Manchester United (`/{locale}/{teams word}/manchester-united-fc/`)

- No sideways overflow on any of the three tabs in EN at 375px, nor in DE and FI at 280px.
- The tab bar fits in one row at 280px in DE and FI.
- Filter UEFA Champions League: 1 upcoming group and 3 result rows remain.
