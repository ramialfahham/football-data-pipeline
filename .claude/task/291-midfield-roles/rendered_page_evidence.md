# Rendered pages — the Player page with a midfield role, the Players index row, the Team squad

Tool: the in-app browser pane on a static `astro build` of this branch's `site_v2` (2,355 pages),
served over HTTP from the build folder, with three sample payloads given the role the branch's
warehouse gives them (Pavlović 328033 DM with his 14-player Bundesliga 2026/27 pool, Amiri 714 CM,
Olise 19617 AM). The pane emulates each width; every check is DOM geometry read in the page
(getBoundingClientRect and getClientRects of each element and of each "·" text node; scrollWidth
against clientWidth for clipping). No accessibility-tree read and no screenshot of this build was
taken. The page texts below (headers, intros, legends, index row, squad headings) were read from the
built HTML files.

Pages measured: `/en/players/a-pavlovic-328033/`, `/de/spieler/a-pavlovic-328033/`,
`/fi/pelaajat/a-pavlovic-328033/`, with the comparison switch set to all metrics.

Checked on every page at every width:
- column: every element of the page body inside the body column (the site's top bar is excluded;
  at 260px it is 17px wider than the screen today, without this change);
- clipping: no element with hidden overflow whose content is wider than its box;
- the header's position item: its line boxes inside the header text column, and the number of
  lines it takes;
- the separators: no "·" text node that starts a line of the header;
- the header's other items: none of its nowrap items (club, nation, age, height, season) splits over
  two lines; the position item, which opens the line, carries no nowrap class;
- the comparison: the number of rows, every peer dot inside its line, the value column aligned.

| width | language | body column | clipped | position item | "·" at a line start | rows / dots in their lines | values aligned |
|---|---|---|---|---|---|---|---|
| 260 | EN | inside | 0 | 1 line | 0 | 20 / 299 | yes |
| 260 | DE | inside | 0 | 2 lines | 0 | 20 / 299 | yes |
| 260 | FI | inside | 0 | 2 lines | 0 | 20 / 299 | yes |
| 280 | EN | inside | 0 | 1 line | 0 | 20 / 299 | yes |
| 280 | DE | inside | 0 | 1 line | 0 | 20 / 299 | yes |
| 280 | FI | inside | 0 | 2 lines | 0 | 20 / 299 | yes |
| 320 | EN · DE · FI | inside | 0 | 1 line | 0 | 20 / 299 | yes |
| 375 | EN · DE · FI | inside | 0 | 1 line | 0 | 20 / 299 | yes |

The same measurement also reads the number rule: values and medians of 10 or more still show one
decimal ("104.8", "52.5") on every page at every width. That is the live page today, before this
change, and belongs to the display_value work, not to this task.

Read from the built HTML:
- headers: Pavlović "Defensive midfielder" / "Defensiver Mittelfeldspieler" / "Puolustava
  keskikenttäpelaaja"; Amiri "Central midfielder" / "Zentraler Mittelfeldspieler" / "Keskikentän
  keskustan pelaaja"; Olise "Attacking midfielder" / "Offensiver Mittelfeldspieler" / "Hyökkäävä
  keskikenttäpelaaja";
- Pavlović intros (competition, club squad, last season, national squad), EN · DE · FI: none
  contains "Pavlović";
- legends: "Aleksandar Pavlović · Defensive midfielder" and "Other defensive midfielders" (DE
  "Andere defensive Mittelfeldspieler", FI "Muut puolustavat keskikenttäpelaajat"); FI squad legend
  "Muut Bayern München -pelaajat";
- Players page (EN): Olise's row reads "M. Olise" over "Attacking midfielder · Bayern München"; the
  position filter offers All positions, Forwards, Midfielders, Defenders, Goalkeepers;
- Team page Bayern München (EN): squad headings Goalkeepers, Defenders, Midfielders, Forwards; no
  role label on the page.
