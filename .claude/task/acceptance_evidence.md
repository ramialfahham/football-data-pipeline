# Acceptance evidence — #166 part 3: the next match page

Read from `astro build` of the committed sample (2,538 pages; audit-seo and check-built-pages OK), from a build of
main from the same sample, and from a build that adds the real Dortmund vs Bremen payload (a gitignored copy,
deleted after). A script checks every built match page (1,884; 1,887 with the real one); the dev-server check is
in rendered_page_evidence.md.

criteria_demonstrated:
  - THE BREADCRUMB. On all 1,884 match pages the trail has five levels, Home › Competitions › {competition} ›
    Matchdays (Rounds for a cup) › {home} vs {away}. The script checks the fourth level against the competition
    index's type in every language. The last level is a span with aria-current="page". The
    BreadcrumbList JSON-LD lists the same five names in the same order, and an item carries a URL exactly where
    the trail has a link. A level links only to a built page: the SEO audit's dead-link check passes on 2,539 pages.
  - ONE H1 AND THE KICK-OFF LINE. Every match page has exactly one H1, the page title (two meetings of the same
    clubs differ by date). Every kick-off line carries the time with "UTC"; the real page reads "Matchday 5 · Fri,
    9 Oct 2026 · 18:30 UTC · Signal Iduna Park". The committed sample payloads predate round_order, so their
    domestic pages show the provider's round name, as the criterion's "otherwise" gives. No standing chip appears
    without its rank.
  - NOTHING THE DESIGN DROPPED. No match page carries the sentence, the window switch, points, the Explore chips
    or the "Sample data" line. NarrativeSlot.astro and LinksFooter.astro are deleted.
  - ONE FORM WINDOW, IN THE PAGE'S LANGUAGE. The export's form_block picks the block the warehouse flags with
    is_form_window; a test covers both flags and neither. Pills read W/D/L, S/U/N and V/T/H, the H/A letters H/A,
    H/A and K/V. No metric name on any match page carries Ø or %.
  - RECENT MATCHES AND HEAD TO HEAD. Each side shows at most 5 result rows, and no row shows a competition code.
    Head to head shows the served intro or "No meetings on record.", at most 5 meetings, every date with its
    year, no totals and no bar. The real page's intro reads "Borussia Dortmund won 3 of the last 5 meetings, and
    2 were drawn.", the home side first in each meeting.
  - PLAYERS TO WATCH. At most 5 players per side, in the served top_player_rank order. The real page shows
    Guirassy (2 goals, 2 assists) first for Dortmund and Grüll (2 goals, 3 assists) first for Bremen. A
    goalkeeper's row shows saves only: no mart serves the shots faced its percentage needs. A fetch-level test
    holds round_order, the team slugs, each side's flagged form block and the players' window_type.
  - LAYOUT AT 375, 700 AND 1010PX. In EN, DE and FI nothing in the match page's content passes the edge; the
    teams stack under 700px. At 700px only the site header's controls pass the edge, as on every page.
    check_design_inventory.py reports 0 failures in 165 renders on the sample build, and 0 in 9 on the real page.
  - NO OTHER PAGE CHANGES. All 655 pages that are not match pages show the same text as main's build.
  - REAL DATA IN THREE LANGUAGES. The real payload renders every block in EN, DE and FI. Examples: "Spieltag 5",
    "Kierros 5", the FI intro "Borussia Dortmund voitti 5 edellisestä kohtaamisesta 3, ja 2 päättyi tasan."
