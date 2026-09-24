# Acceptance evidence — #158, page addresses follow the reader's language

Every item read from `site_v2/dist` built by `npm run build` on the committed sample (1330 pages),
from the dev server (`preview_start` v2), or from a command's exit code read bare. HJK and Jamal
Musiala are not in the committed sample, so the same shapes are shown on Borussia Dortmund and
P. Schick, which are.

criteria_demonstrated:
  - EVERY ADDRESS USES ITS LANGUAGE'S WORD. dist holds `/de/wettbewerbe/`, `/fi/kilpailut/`,
    `/en/competitions/`, `/de/bundesliga/spiele/`, `/de/bundesliga/statistiken/`,
    `/fi/bundesliga/ottelut/`, `/fi/bundesliga/tilastot/`, and 36 pages each under
    `/de/mannschaften/`, `/fi/joukkueet/`, `/en/teams/`, 72 each under `/de/spieler/`,
    `/fi/pelaajat/`, `/en/players/`; a scan of all 1330 built paths finds 0 at an old shape
    (`/fixtures/`, `/rankings/`, or an English word under /de/ or /fi/). Dev server: 200 for
    `/de/mannschaften/borussia-dortmund/` (h1 "Borussia Dortmund"), `/fi/joukkueet/borussia-dortmund/`,
    `/de/spieler/p-schick-794/` (h1 "P. Schick"), `/fi/pelaajat/p-schick-794/`,
    `/de/bundesliga/spiele/2026-10-09-borussia-dortmund-vs-sv-werder-bremen/`; 404 for `/de/teams/x/`.
  - THE TWO TABS MOVED, THEIR NAMES DID NOT. Built `/de/bundesliga/index.html` tab bar:
    `Übersicht` (on), `<a href="/de/bundesliga/spiele/">Spieltage</a>`,
    `<a href="/de/bundesliga/statistiken/">Ranglisten</a>`; EN `/en/bundesliga/matches/` and
    `/en/bundesliga/stats/` and FI `/fi/bundesliga/ottelut/` and `/fi/bundesliga/tilastot/` are
    emitted; `/en/bundesliga/fixtures/` returns 404 on the dev server; no i18n string changed.
  - EVERY HREFLANG PAIR POINTS BOTH WAYS AT A REAL PAGE. A script over the built HTML: 1330 pages,
    3987 reciprocal hreflang pairs (1329 localised pages x 3 languages), 0 problems (each page's own
    language names itself, each target is emitted, each target names the page back). audit-seo now
    checks the same on every build: "1330 built page(s) checked. OK."; with `alternatePaths`
    reverted to the prefix swap it went RED with 4728 violations ("hreflang "en" points at
    /en/bundesliga/spiele/..., which the build did not emit", "... a different page than ...").
  - THE BUILD FAILS ON A SLUG THAT EQUALS A WORD. With the German matches word set to `bundesliga`
    the build stopped in the competition hub's getStaticPaths: "competition slug equals an address
    word: bundesliga = matches (de)", nonzero exit; `tests/test_address_words.py::
    test_no_registry_slug_equals_an_address_word` went RED on the same mutation (the registry's
    slugs against the table); reverted, both green.
  - THE SEARCH CHECKS MATCH ACROSS LANGUAGES THROUGH THE WORD LIST AND PASS. `npm run build` exit 0:
    node tests "pass 111, fail 0"; "check-page-specs: 8 page(s) validated against their specs. OK.";
    "audit-seo: 1330 built page(s) checked. OK." (the page-count driver lists
    `/[lang]/[competition]/[matches]` -> 3, `/[lang]/[competition]/[stats]` -> 3, `/[lang]/[teams]/[team]`
    -> 108); "check-built-pages: 849 match page(s) = 283 payload(s) x 3 ...; 3 fixtures page(s) and 3
    rankings page(s) checked. OK."; with its Matchdays shape set back to `/fixtures/` it went RED:
    "a payload carries fixtures but no Matchdays page matched FIXTURES_PAGE". `python
    scripts/check_design_inventory.py --dist site_v2/dist` exit 0: "21 pages · 3 viewports · 3
    languages (pages per language: en 21, de 7, fi 21) · 147 renders · 0 failures · 21 warnings",
    the German and Finnish built pages opened at their own words.
