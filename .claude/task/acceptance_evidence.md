# Acceptance evidence — #41, the Top teams block

Read from BUILT output (`site_v2/dist`, the dev server at 375px and 1280px, and the committed
`site_v2/src/data/landing.json`), not from source.

⛔ **THIS FILE WAS REWRITTEN WHOLESALE, NOT AMENDED.** Its previous version measured the FIRST
version of this branch — the one built without reading #41 — and every headline number in it was
false by the time it was read: `250 built page(s)` (now 307), "the rows do not link" and "0 anchors"
(now 28 hrefs per locale, 7 per board), board titles quoted with the Ø sigil (now expanded), and a
closing section calling the links "deliberately absent (#41)" when #41 is the document that requires
them. That is the accumulate-instead-of-replace failure this repo has recorded nine times, so the
remedy applied here is the one the record prescribes: pull EVERY number out and re-derive it, rather
than sweep for the ones I remember changing.

criteria_demonstrated:
  - ONE ROW PER LEAGUE, ALL SEVEN, DECIDED BY THE WAREHOUSE. The committed `landing.json` carries
    4 team boards x 7 rows = 28 rows, and the export filters `league_leader_order = 1` — a column
    `mart_team_leaderboards` has served since `!167`, confirmed live in prod before any code was
    written.
  - THE INTRO SENTENCE NAMES THE LEAGUES ON THE BOARDS. Rendered in all three locales; the league
    list is read from the payload rows rather than restated, so it cannot drift when #101 changes
    the pool nightly.
  - ⭐ THE LEAGUE NAMES ARE THE WAREHOUSE'S, NOT THE REGISTRY'S. The intro read
    "... Eredivisie, 1. Fußball-Bundesliga, Premier League" until the CPO caught it on the page; the
    export was building its competition dict from `docs/competition_registry.yml`, which is INPUT.
    Now `Bundesliga`, in all three locales. Swept across the whole registry — **37 identical,
    11 DIFFERENT** — and fixed on BOTH surfaces that display a competition name, not only the one
    that was looked at: `competitions.json` gains the same 11 corrections and 0 slug changes, which
    is what `TeamHeader.astro` renders on the BL1 team pages this branch builds. Zero registry-only
    names survive anywhere in the 307 built pages. Detail and mutation results: §3b of
    `rendered_page_evidence.md`.
  - THE EXPORT IS DETERMINISTIC AND COMPARES NOTHING. `--entities landing` run twice against live
    BigQuery, outputs compared with `cmp`: IDENTICAL, and identical again after the name overlay was
    refactored into one shared helper. The query is `order by t.board_leader_order` — one served
    column. The shaper groups, preserves and caps. Mutation-tested: putting a value sort into the
    shaper turns `test_top_teams_does_not_reorder_what_it_is_given` RED. That test feeds rows in an
    order no sort would produce, so it cannot pass by luck.
  - ⭐ THE MIXED FORMAT IS RIGHT, READ FROM THE BUILT HTML rather than from the catalogue. This is
    the one thing that differs from the player block, whose four boards are all integers:
        goals_per_match           1 decimal   4.3, 3.6, 3.6, 3.5
        shots_on_goal_per_match   1 decimal   9.0, 9.0, 8.7, 8.5
        passes_per_match          0 decimals  767, 746, 701, 647
        duels_per_match           0 decimals  121, 119, 111, 109
    A component that picked a formatter would have rendered one pair wrong. The format travels per
    board from `metric_catalogue.csv`, and `test_top_teams_carries_the_catalogue_format_per_board`
    asserts the boards do not collapse to a single shared format.
  - EVERY BOARD TITLE IS LOCALISED, NON-EMPTY, AND SPELLS THE RATE OUT — #41's rule, per locale:
        EN  Goals per match / Shots on goal per match / Passes per match / Duels per match
        DE  Tore pro Spiel / Torschüsse pro Spiel / Pässe pro Spiel / Zweikämpfe pro Spiel
        FI  Maalit ottelua kohden / Maalilaukaukset ottelua kohden / Syötöt ottelua kohden /
            Kaksinkamppailut ottelua kohden
    Blank-title count is 0 in each locale and the **Ø sigil count on the home page is 0 in each
    locale**. The expansion derives from the LOCALISED label, so a Finnish board is not titled in
    English. No metric label was authored: all four already existed in the catalogue and in
    `strings.ts`, and "per match"/"pro Spiel"/"ottelua kohden" already ship in
    `heroVerdictUnder`/`heroCaption`. A metric ROW elsewhere keeps the sigil, which
    `metrics_display.md` locks — and that heading-vs-row boundary is now recorded IN
    `metrics_display.md`, not only in #41.
    ⛔ THE CODE BEHIND THOSE TITLES WAS REWRITTEN AFTER A REVIEW FAIL, though the titles did not
    change. `boardTitle()` classified the metric from its id (`endsWith("_per_match")`); it now
    takes `(lang, labelKey)` and branches on nothing, and the premise that this block's four boards
    are per-match rates is asserted against the catalogue's `denominator_expr` in
    `test_the_team_board_set_is_all_per_match_rates`. See §2 of `rendered_page_evidence.md`.
  - EVERY ROW LINKS OUT AND EVERY LINK RESOLVES. `audit-seo: 307 built page(s) checked. OK.` with
    the page-count driver showing `/[lang]/teams/[team] -> 60` — the 20 distinct teams the boards
    link to x 3 locales, up from 3. Measured on the built page: **28 team hrefs per locale**, 7 on
    each of the four boards (against 0 in the first version of this branch), matching the 28 player
    hrefs the Top players block already emitted. Check 8 passing is what proves the 20 committed
    payloads are exactly the right ones. NO NEW ROUTE: `[lang]/teams/[team].astro` already existed.
  - GEOMETRY HOLDS AT BOTH WIDTHS, AND ACROSS BOTH BLOCKS. At 375x812 every one of the eight boards
    has a minimum row height of 55.8px against the 44px floor, `.ent` resolves to a single computed
    display value per board (so a board stacks as a whole, never row-by-row), and the value column's
    right edge is 359 on ALL EIGHT — the two blocks line up with each other, not just internally.
    At 1280x900: minimum 44.0px, one-line variant, right edge 945 on all eight, no name truncated.
    The rows are anchors now, so the focus ring was re-measured on a team board rather than carried
    over: outline-offset -2px, 0px reach beyond the border box, no divider crossed. No console
    errors.
  - THE OFFLINE GATE SET IS GREEN, re-run after the name fix:
        pytest tests/test_export_landing.py     27 passed
        pytest tests/test_export_site_data.py   45 passed (72 together)
        npm test                                83 passed
        ruff check scripts tests                All checks passed
        check_copy_gate.py                      exit 0, 474 strings across 3 locales
                                                (405 chrome + 69 metric labels)

## What was reused rather than rebuilt

`system.css`'s board rules were written for both blocks — its own comment says "the Home page's Top
players (#40) and, when it lands, Top teams (#41)" — so this branch adds no CSS at all. The value
column lining up at the same offset across both blocks at both widths is the evidence that the
shared pattern actually holds rather than merely being intended. The `a.brow:focus-visible`
rule #40 shipped covers the new anchors, which is what "no new CSS" has to mean if it is true.

## What is NOT demonstrated here

- No screenshot: the Browser pane's `screenshot` action fails in this environment, so every visual
  claim is a measured number or emitted text.
- No dark/light toggle. The block introduces no new colour token — it reuses the same board classes
  as Top players, which the theme already swaps. That is reasoning, not a measurement, and is
  labelled as such.
- The crests are not fetched. #41 records that the block inherits #36 (crests hotlinked from
  `media.api-sports.io`, a go-live blocker with a licence question). This block neither adds to that
  problem nor solves it.
