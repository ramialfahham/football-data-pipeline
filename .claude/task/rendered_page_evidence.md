# Rendered page evidence — `feat/144-competitions-hub-approved-design` (#144, the Competitions hub built to #128)

Read from the RUNNING page (Astro dev server, `preview_start` name `v2`) and the production build
(`npm run build`), on the committed `competition_index.json` (48 rows, the whole mart). Structure
is the DOM and the emitted HTML, driven through real `change` events; every value names what it
was read from.

## 1. `/en/competitions/` — the rows are links

`a.comp-row[href]` → **48**; first three: `/en/belgian-pro-league/`, `/en/ligue-1/`,
`/en/serie-a/`. `.comp-name` computed `display: block` (the row's children became spans inside
the anchor). A `a.comp-row:hover` rule is present in the loaded stylesheet.

## 2. The filter state, through the real controls

Radios as rendered (`name:id=value`, `*` = checked): entity `all=""*`, `club="club"`,
`national="national"`; region `all=""*`, `uefa="UEFA"`, `conmebol="CONMEBOL"`,
`concacaf="CONCACAF"`, `caf="CAF"`, `afc="AFC"`, `ofc="OFC"`, `fifa="FIFA"`.

Group visibility after checking a radio and dispatching `change`:

| Filters | Shown | Hidden |
|---|---|---|
| National teams | Continental championships, World Cup, National team qualifiers | the other 5 |
| Africa | Continental club cups, Continental championships, National team qualifiers | the other 5 |
| Clubs + Africa | Continental club cups | the other 7 |
| Clubs + Oceania | none | all 8 (no OFC club competition is onboarded) |
| All + All | all 8 | none |

## 3. The background-load case (the defect of 2026-09-14)

`/de/competitions/` opened in a new tab that was never fronted: `document.visibilityState`
→ `"hidden"`; `.comp-category[hidden]` → `[false, false, false, false, false, false, false,
false]`; 48 links; headings "Nationale Ligen", "Kontinentale Vereinspokale", "Nationale Pokale".
Before this branch the same load hid all eight groups (`hidden: [true ×8]`, `visibleRows: 0`).

## 4. Production build

`npm run build`: 306 pages, `audit-seo: 307 built page(s) checked. OK.`
`dist/en/competitions/index.html`: 48 `<a class="comp-row"`, 0 occurrences of `offsetParent`;
`dist/fi/competitions/index.html`: 48 distinct `/fi/{slug}/` hrefs.

## 5. The six new labels

Not visible on any page today (no competition of those kinds is onboarded); present in
`strings.ts` in EN/DE/FI and held by the copy gate's check 5 (`21 seed label keys resolvable in
every locale`).
