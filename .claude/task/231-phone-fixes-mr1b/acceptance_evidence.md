# Verification — phone fixes, the rules approved on #231 (MR 1b)

Read from the built site (`npm run build` in site_v2, sample data) at 260 to 768px in EN, DE and FI,
in the CI image `mcr.microsoft.com/playwright/python:v1.63.0-noble`, on 29 pages (home, competitions,
a competition, its matches and statistics, a match, the Matches day page, teams, a team, players, a
player, in all three languages).

criteria_demonstrated:
  - **Tap areas:** before the change the tap audit found 2,000+ links and buttons under 44px (competition heading links 548 at 38px, board rows 384 at 42px, footer links 336 at 19px, team rows 207 at 40px, table-column links 171 at 16px, menu links 87 at 34px, header icon buttons 84 at 36px, the day picker arrows at 34px). `tests/test_phone_built_pages_231.py::test_every_link_and_button_has_a_44px_tap_area` finds 0 at 260, 280, 320, 375 and 768px; the header icon buttons shrink to no less than 34px only where three 44px buttons do not fit beside the name.
  - **Day picker:** the title carries the long and the short date; the short form is the one shown without the script, and fitBlocks marks the picker fit-one where the long date fits.
  - **Square rows:** `a.fxrow, a.ctab-row, a.frow, a.lrow, a.brow, a.comp-row` have no border radius and no negative side margin; the built test finds 0 rows with either at five widths.
  - **Separator dots:** the build step turns every middle dot between items into one no-break unit with its space; the built test (`test_no_separator_dot_starts_or_ends_a_line`) finds 0 dots that start or end a line at 260-768px in EN, DE and FI; before the player-row dot fix it found 35 ends of line in the match page lineups.
  - **"Goals 25:6":** the competition row on the Team page keeps the space (static test).
  - **Header:** no page scrolls sideways at 280-768px, and the header fits at 280 and 300px. At 260-270px it overflows by up to 15px; closing that needs a new width rule, which the pinned design checks refuse (see the contract).
  - **Explainer:** `teamPerfIntro` no longer carries the team's name in EN, DE and FI.
  - **1010px and wider:** the design inventory run at 1010px in EN and DE passes against its pins, and the built test measures the tap areas, dots and rows at 768px; what changes at 1010px is the 44px rows and links and the lowercase DE and FI explainer; the two 1010px strip chart pins moved with the 44px rows and were renewed from the CI image.
  - **Pins:** no pin is raised. `check_page_css.py`, `check_component_registry.py` and the design inventory (merge-request scope, 280 and 1010px, EN and DE) pass in the CI image; the only remaining lines are the container's own (the read-only mount stops the home generator, and the base for the pin-rise tests is not reachable). The chart screenshot check shows 0 differences over 18 screenshots after the renewal of the eight pins from the CI image's own output.
