# Acceptance evidence — #160 part 2, the Matches page and its day pages

Read from `site_v2/dist` built by `npm run build` on the committed sample (exported 2026-09-25 from
prod after the nightly built mart_match_days: 58 days, 32 competitions, 628 fixture payloads),
from the dev server, and from exit codes read bare.

criteria_demonstrated:
  - THE MENU LINKS THE PAGE AT EACH LANGUAGE'S WORD. Every page's header: `Spiele→/de/spiele/`,
    `Matches→/en/matches/`, `Ottelut→/fi/ottelut/` (SiteHeader). dist holds `en/matches/index.html`,
    `de/spiele/index.html`, `fi/ottelut/index.html`; hreflang of `/de/spiele/` names `/en/matches/`
    and `/fi/ottelut/`, audit-seo checks every pair both ways: 2539 pages OK. Built to #130: the
    breadcrumb Home › Matches and the h1, the two filter rows, the day switcher, one Schedule block.
  - EVERY DAY IN REACH HAS A PAGE; THE ARROWS SKIP EMPTY DAYS. 57 dated pages per language beside the
    opening day, 58 days = mart_match_days' days (2026-08-20 to 2027-01-11); 342 day arrows across the
    three languages, 0 pointing at a missing page (audit-seo check 8 and a script over dist); no day
    page without a match row; the first day has no previous arrow and the last no next; the day
    before the opening day links to `/en/matches/` itself.
  - THREE MATCHES, THEN "SHOW ALL {n}"; SCORE WHEN PLAYED, KICK-OFF WHEN NOT. 2026-08-20: UEFA
    Conference League shows 3 rows then "Show all 24"; the opening day folds CNL and UNL; past days
    render `.fxrow.played` rows with the score ("Feyenoord 5 FC Utrecht 0") and no link, future
    rows the kick-off and "UTC" and link to their match page.
  - THE THREE ELEMENTS ARE IN THE INVENTORY AND MEASURED IN EN, DE, FI. block_standard.md gains Page
    heading (`.crumb + h1`), Filter row (`.seg`), Filter button (`.seg .seg-btn`) and Fold
    (`.fxmore > summary`), and the Pages rows "Matches page" and "Matches day page". `python
    scripts/check_design_inventory.py --dist site_v2/dist` → `23 pages · 3 viewports · 3 languages ·
    165 renders · 0 failures · 27 warnings` (all the known 700px header row). RED with the built
    page's fold removed and its heading at 22px: "Page heading ... expected font-size=30px ·
    measured 22px", "Fold · expected on this page · measured 0 matches".
  - OWN TITLE AND DESCRIPTION PER PAGE AND LANGUAGE; THE SEARCH PHRASE ON THE MATCHES PAGE.
    `/de/spiele/`: "Fußball heute: alle Spiele, Freitag, 25. September"; EN "Football today: all
    matches, Friday 25 September"; FI "Jalkapallo tänään: kaikki ottelut, perjantai 25. syyskuuta";
    a day page: "Football on Saturday 26 September: all matches". audit-seo's uniqueness per locale
    and across locales passes on 2539 pages; the wording is on the MR head.
  - HEADING TO THE COMPETITION PAGE, ROW TO THE MATCH PAGE. `.gh a.cnm` hrefs are the competition
    pages (`/de/nations-league/`); unplayed rows are `a.fxrow` to `/de/nations-league/spiele/2026-
    09-24-andorra-vs-malta/`-shaped pages the build emits (check-built-pages: 1884 match pages =
    628 payloads x 3; audit-seo: no dead link). Filters on the dev server: Clubs hides both
    national-team groups; National teams + CONCACAF leaves CONCACAF Nations League only.
