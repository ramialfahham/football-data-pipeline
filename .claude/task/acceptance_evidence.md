# Acceptance evidence — #155, one title per match page

Read from `site_v2/dist` built by `npm run build` on the committed sample, and from a full-scale
build carrying every upcoming fixture of the 2026-09-25 export (4,808 payloads: the 4,525 exported
beyond the tracked 283, copied in and removed afterwards), built with the deploy job's 8 GB heap.

criteria_demonstrated:
  - NO TWO MATCH PAGES OF ONE LOCALE SHARE A TITLE. Full scale: `audit-seo: 14905 built page(s)
    checked. OK.`, check 5 included; the pairs the issue names now differ, e.g.
    `/en/bundesliga/matches/2026-10-09-borussia-dortmund-vs-sv-werder-bremen/` is "Borussia Dortmund
    vs SV Werder Bremen, 9 Oct" and its DFB-Pokal meeting's page carries "27 Oct". With `{date}`
    removed from the EN title the same full-scale build fails with 11 "title is not unique within
    "en"" violations (DFB-Pokal vs Bundesliga pairings among them); restored, 0.
  - THE WORDING IS THE CPO'S AND THE DATE TELLS THE MEETINGS APART. The CPO chose "Date replaces
    Preview" in chat over "Date after Preview": EN `{home} vs {away}, {date}`, DE `{home} - {away},
    {date}`, FI `{home}–{away}, {date}`; the date is the served kick-off, formatted by
    formatShortDate (UTC). The competition stays out (measured: 1,672 titles over the 660px hard cap
    with it). Built titles: "Borussia Dortmund vs SV Werder Bremen, 9 Oct" / "Borussia Dortmund -
    SV Werder Bremen, 9. Okt." / "Borussia Dortmund–SV Werder Bremen, 9.10."; measured worst over
    all 14,385 upcoming titles 535px, inside the 600px budget, and the budget guard test passes.
  - AUDIT CLEAN ON A BUILD WITH EVERY UNPLAYED MATCH. `check-built-pages: 14424 match page(s) =
    4808 payload(s) x 3`; `audit-seo: 14905 built page(s) checked. OK.`; exit 0. Committed sample:
    node tests 111 pass, audit-seo 1330 pages OK, check-built-pages 849 OK; pytest 1325 passed;
    check_copy_gate OK.
