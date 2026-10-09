# Acceptance evidence — the future match page

Read from `astro build` of the sample payloads (2,539 pages; audit-seo and check-built-pages OK), from a build of
main from the same payloads, and from a build that adds one real future fixture: Bayern München vs Borussia
Dortmund, 31 Oct, Bundesliga matchday 8. That payload was exported for this check (129 MB read), kept as a
gitignored copy and deleted after. A script reads the built pages; the dev server covers the widths.

criteria_demonstrated:
  - THE FUTURE PAGE. The real payload says is_next_round false. In EN, DE and FI its blocks are Head to head,
    then Next matches, under the breadcrumb and the header. No standing chip shows, though the warehouse serves a
    rank for both teams. There are no form pills, Recent matches rows or player rows. The H2H intro reads "Bayern
    München won 2 and Borussia Dortmund 1 of the last 5 meetings, and 2 were drawn."
  - NEXT MATCHES. One Bundesliga group head links to the competition page. Two date headings follow: "Fri, 9 Oct
    2026" and "Sat, 10 Oct 2026" (DE "Fr., 9. Okt. 2026", FI "pe 9.10.2026"). Each heads one match row: Borussia
    Dortmund vs SV Werder Bremen 18:30 UTC, and FC Augsburg vs Bayern München 13:30 UTC. Each row shows both
    crests and links to that match's page; both pages are built. This is the approved render's content. An
    export test holds that a team whose next match is this one adds none.
  - NEXT-MATCH PAGES UNCHANGED. Every page of the build, 2,539, shows the same text as main's build, and both
    builds hold the same pages. The sample payloads carry no is_next_round, so they render as the next match.
  - WIDTHS. At 375 and 1010px the page does not scroll sideways, and nothing in its content passes the edge. At
    700px only the site header passes the edge, by 7px, as on every page. check_design_inventory.py on the real
    page reports 0 failures in 9 renders (3 widths, 3 languages), with the committed block_standard.md. On the sample
    build it reports 0 failures in 165 renders.
  - GATES. npm test 117 pass; check_copy_gate, check_page_css pass; pytest tests/ 1490 passed, 2 skipped.
  - COST. The nightly export's two changed queries read 3.5 MB more (fixtures 19.83 to 19.89 MB, next matches
    16.83 to 20.22 MB), dry-run on prod: about 0.1 GB a month.
