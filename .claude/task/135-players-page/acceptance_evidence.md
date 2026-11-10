# Verification — the Players page and the nation pages

Read from the built site (`npm run build` in site_v2, the committed sample: 2,355 pages) and the dev
server on the same sample. The sample holds 2,154 of 18,518 players, so nation sizes are the
sample's; the full counts come from the warehouse: 2,971 rows shown with no position chosen, 5,214
in any view, 101 nations with a page (mart_player_index on prod data, read-only).

criteria_demonstrated:
  - **Players page:** `/en/players/`, `/de/spieler/` and `/fi/pelaajat/` build, titled "Football players", "Fußballspieler" and "Jalkapalloilijat", with the breadcrumb Home › Players, the heading Players, then the blocks World's best and Players by nation, in that order.
  - **World's best:** four lists, Forwards (Kylian Mbappé, K. Kvaratskhelia, O. Dembélé, Ferran Torres, …), Midfielders, Defenders and Goalkeepers (T. Courtois, M. Safonov, G. Kobel, David Raya, …), each in club order: Real Madrid, then Paris Saint-Germain, Bayern München, Arsenal. All 40 nominees of the 2026 seed show, with no fold; the seed test in dbt checks the set against the seed.
  - **Players by nation:** Spain shows its rows and "Show all 9", linking to `/en/players/spain/`, as does its heading. A nation whose rows all show has no link: no "Show all" under any of the sample's smaller groups.
  - **No nation recorded:** the last group reads "No nation recorded", shows its first 10 rows, and has no heading link, no "Show all" link and no page.
  - **Filters:** Goalkeepers leaves 116 rows over 21 nations, every one a goalkeeper, each nation with its goalkeepers' count ("3 players", "1 player", "5 players"), and only the Goalkeepers list of World's best. Africa leaves Morocco, Senegal, Cape Verde, Tunisia and Nigeria, and World's best keeps S. Mané, A. Hakimi, Y. Bounou, É. Mendy and Vózinha; the Forwards list hides, having none.
  - **Nation page:** 27 nation pages build per language in the sample. `/en/players/spain/`, `/de/spieler/spain/` and `/fi/pelaajat/spain/` show the breadcrumb Home › Players › Spain, the heading Spain, the position filter and every Spain row of the sample in the served order.
  - **No shared address:** `nationPages` throws on a nation slug that is a player page's slug or not letters and hyphens (playerIndex.test.mjs), the dbt test holds every nation_slug to letters and hyphens, and the SEO audit matches a player address only to a slug ending in its id and a nation address only to letters and hyphens; the build checked 2,356 pages with no address claimed twice.
  - **Links in:** the menu's Players item and the footer's link to `/en/players/`, and the Player page of Harry Kane (`/en/players/h-kane-184/`) has the breadcrumb Home › Players › Harry Edward Kane, its Players level a link to `/en/players/`.
  - **Widths:** at 280, 360, 375, 700 and 1010px, in EN, DE and FI, the Players page and Spain's page do not scroll sideways and no name, club line, group head, count or link is cut. The filters show as dropdowns at 280 to 375px and as buttons at 700 and 1010px. At 280px with a 15px scrollbar, the site header's icon buttons reach 277px on every page, the Teams page included; at 280px of content, as on a phone, nothing scrolls.
