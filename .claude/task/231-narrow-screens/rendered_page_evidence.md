# Rendered pages — #231

- **Instrument:** Playwright Chromium (the validate:ui browser) on two static builds of the committed sample, served locally: main a54adfbf and this branch. Geometry, line boxes and computed style are read in the page after its fonts load and the fit script has run. Each page is loaded once, then resized; every tab is opened at every width.
- **Pages:** every built page in EN, DE and FI, 786 per language. That covers Home, Competitions, competition Overview / Matchdays / Rankings, Matches and its day pages, every match page (537 upcoming, 11 played), Teams and every Team page, Players, every Player page and the nation pages.
- **Widths:** 280, 320, 375, 768 and 1010px.
- **Defects found after:** 0 name splits, overflows, overlaps or cut-off text, and 0 rows off their rule, on every page type at every width, with the site's scripts and without them (280–768px). The Deserved points table shows its narrow heads (approved in chat, 2026-11-19) where a head word does not fit its column: the fit script chooses them, the cells keep 4px on the left instead of 8px, and 54px hold "Deserved" (51.7px) and "Verdiente" (52.1px); the page does not scroll.
- **The narrow Deserved points heads, one-page check (Bundesliga overview, EN/DE/FI, 280, 300 and 375px, geometry read in the page):**
  - 280 and 300px: the table shows its narrow heads and 4px head padding, a 54px or 55px room. EN reads "Shots on target margin per match" and "Points minus deserved points"; DE "Differenz der Schüsse aufs Tor pro Spiel" and "Punkte minus verdiente Punkte"; FI "Vetoero maalia kohti ottelua kohden" and "Pisteet miinus ansaitut pisteet"; "Deserved points", "Verdiente Punkte" and "Ansaitut pisteet" unchanged.
  - No word is wider than its room, no head cell scrolls, and the page does not scroll sideways (0px) at either width.
  - 375px: `heads-full`, the full heads with the 8px padding in a 66px room, 0 words over, 0px page scroll.
- **1010px:** the only layout differences from main are match pages' Recent matches lists that broke at 1010px on main; they now take their two-line form.
- **Spot checks by hand, reading geometry:**
  - The meeting rows on the Borussia Mönchengladbach v TSG 1899 Hoffenheim page at 280 and 375px: the list is fit-two; home, away and meta each on their own lines, the score beside the names, the dash hidden.
  - The same list at 1010px: fit-one, each row on one line with the dash shown.
  - The header names on that page: 15px at 280px, 20px at 375px and 30px at 1010px, each team's box holding its content (scrollWidth equals clientWidth).
