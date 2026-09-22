# Acceptance evidence — the menu item reads Statistics

Read from `site_v2/dist` built by `npm run build` on the committed sample (1,195 pages;
`audit-seo: 1195 built page(s) checked. OK.`), with a scratchpad script that strips Astro's
`<!-- -->` splits, takes each page's `nav.mainnav` and its footer, and reads the last menu item's
text and link state. Exit codes read bare.

criteria_demonstrated:
  - EVERY BUILT PAGE SHOWS THE RULED WORD IN ITS OWN LANGUAGE, AND NO PAGE SHOWS THIS MORNING'S.
    Swept all 1,195 pages under `dist`; 1,194 carry the header nav (the 1,195th is the root
    redirect stub, which has no chrome). The last menu item reads `Statistics` on 398 pages,
    `Statistiken` on 398 and `Tilastot` on 398. Pages still showing `Leaderboards`,
    `Bestenlisten` or `Kärkilistat` in the nav: **0**; in the footer link row: **0**.
    `grep -rn "navLeaderboards"` over `site_v2/`, `docs/`, `design-mocks/`, `scripts/`, `tests/`
    returns nothing outside a stale `__pycache__` blob.
  - THE ITEM IS STILL DEAD TEXT. Of the 1,194 pages with a nav, the last item renders without an
    `href` on **1,194**. No page gained a link, so nothing points at the hub #139 has not built
    (`audit-seo: 1195 built page(s) checked. OK.`). Measured in Chromium at 375/1280 px in three
    locales: `SPAN`, `href` null, 13px, 70 px EN / 79 px DE / 61 px FI, and the nav never
    overflows (`scrollWidth == clientWidth` on every render). The footer row reads
    `… Players · Statistics · About` and its DE and FI equivalents.
  - "LEADERBOARDS" SURVIVES ONLY WHERE IT NAMES THE HUB, NOT THE MENU ITEM. After the sweep, the
    word remains at exactly four sites, each about the page or the work rather than the label:
    `site_architecture.md:247` (the `leaderboards/{league_code}/{metric_id}.json` export payload
    row), `north_star.md:115` (the GitLab milestone list; milestone 7 is "7 · Leaderboards"),
    `10_home.md:9,13,1002` (the #139 page, and the ruling's own history) and
    `gen_navmap.py:155` ("Leaderboards for this competition", the competition page's boards).
  - THE GATES ARE GREEN. `check_copy_gate.py` → `COPY GATE ok: 654 strings across 3 locales`,
    exit 0. `cd site_v2 && npm test` → 99 pass, 0 fail. `check_design_inventory.py --dist
    site_v2/dist` → `19 pages · 2 viewports · 2 languages · 76 renders · 0 failures · 0
    warnings`, exit 0. `ruff check design-mocks/gen_navmap.py` clean.

⚠ Unchanged and pre-existing, as recorded on !217: `design-mocks/gen_navmap.py` aborts on its own
assertion that the nav emits no anchors, false since the Competitions index shipped. The
generator is a diagram no check runs; this branch's edit to it (the key rename) is verified
directly — `menu_items()` returns the six keys ending `('navStatistics', 'Statistics')` and every
key resolves to a `MENU_NOTES` entry.
