# Rendered pages — the Players page and the nation pages

Tool: the in-app browser on the Astro dev server (`preview_start v2`), committed sample data. Each
page loads in a same-origin iframe of the stated width and is measured with DOM geometry read in
the page (getBoundingClientRect, scrollWidth against clientWidth). Phone widths (280, 360, 375) are
measured at that content width (iframe width plus its 15px scrollbar, as a phone has none); 700 and
1010 at the window width, so the content is 15px narrower when the page scrolls vertically.

Pages: `/en/players/`, `/de/spieler/`, `/fi/pelaajat/` (Players page) and `/en/players/spain/`,
`/de/spieler/spain/`, `/fi/pelaajat/spain/` (nation page).

Checked on every page at every width:
- sideways scroll: the document's scrollWidth against its clientWidth;
- cut text: scrollWidth against clientWidth of every visible player name and position · club line,
  group name and count, "Show all" label, breadcrumb level, heading and filter button;
- the filter form: the buttons or the dropdowns shown;
- on the Players page: every "Show all" link's left and right edges against its grid's, and, with
  Midfielders chosen, that each shown nation shows one count, the Midfielders one;
- the JSON-LD ItemList count.

| width | page, EN · DE · FI | sideways scroll | cut text | filters | Show all links span the grid row | Midfielders: one count per nation | ItemList |
|---|---|---|---|---|---|---|---|
| 280 | Players page | none | 0 | dropdowns | 27 of 27 | yes, 22 nations | 714 |
| 280 | Spain | none | 0 | dropdown | none on the page | — | 9 |
| 360 | Players page | none | 0 | dropdowns | 27 of 27 | yes, 22 nations | 714 |
| 360 | Spain | none | 0 | dropdown | none on the page | — | 9 |
| 375 | Players page | none | 0 | dropdowns | 27 of 27 | yes, 22 nations | 714 |
| 375 | Spain | none | 0 | dropdown | none on the page | — | 9 |
| 700 | Players page | none | 0 | buttons | 27 of 27 | yes, 22 nations | 714 |
| 700 | Spain | none | 0 | buttons | none on the page | — | 9 |
| 1010 | Players page | none | 0 | buttons | 27 of 27 | yes, 22 nations | 714 |
| 1010 | Spain | none | 0 | buttons | none on the page | — | 9 |

Each row holds for all three languages; no language differed in any column.

Group heads at 280px: on all 29 nation heads of each language, the nation's name sits on one line
with its count beside it (tops within 4px). The longest heads in the sample are "No nation
recorded", "Keine Nationalität erfasst" and "Ei kansallisuutta". Written into a head on the German
page, the longest nation name in the full data, "Saint Vincent and the Grenadines", with "1.237
Spieler", wraps to three lines beside the count; nothing is cut and the page does not scroll.

A nation the filters empty hides, read on `/en/players/` with the nation groups as div elements:
with Goalkeepers chosen, 21 of the 29 nations show and 8 hide, and no shown nation is left without
a row; with Africa chosen, 5 nations show, all of them African. Both hold in the button form
(1010px) and in the dropdown form (280px of content), where the choice is made in the select.

The ItemList count is the players the Players page lists: the rows shown in any view and the World's
best nominees (714 in the sample); on a nation page, its players (9 for Spain in the sample).
