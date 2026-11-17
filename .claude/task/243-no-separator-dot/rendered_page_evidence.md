# Rendered pages — 375px and 1280px, EN, DE, FI

Tool: the Browser pane against this branch's dev server, the viewport set by an iframe at 375px and 1280px, read through each page's DOM and text. Screenshots of the team page, the played match page and the player page were read at 375px.

observed:
  - **Home, Matches, the Bundesliga overview, the Bayern München team page, a played match page and a player page, in EN, DE and FI, at 375px and 1280px:** 0 "·" in the rendered text, no horizontal overflow, no fact line or unit wider than its box.
  - **Team page at 375px:** the header facts sit on two lines with a 12px gap and whole units; each competition row shows the name over a muted round note, the W/D/L chips on the left and "Goals 25:6" with "Points 17" at the right; a recent-match row shows home or away, the competition and the date as units under the opponent.
  - **Long substitution unit in a player row (no committed fixture has one):** the squad rows of the German Bayern München page, given a second fact "eingewechselt 73′ für Kingsley Coman-Longname" (about 280px) under a first fact, at 375, 560, 600 and 700px: the page is as wide as the viewport at each width, and the long unit takes its own line.
  - **A unit wider than the line:** in the shared line style a unit has `max-width: 100%` and `min-width: 0` with no nowrap, so a short unit wraps whole and a unit wider than the line takes its own line and breaks between words. Measured at 260, 280, 320, 375 and 1280px in EN, DE and FI: the Benfica, Elversberg and Sevilla team pages and the result row given "WC Qualification Intercontinental Playoffs" show no sideways scroll at 280px and wider, no unit cut off, and the short date unit stays on one line. At 260px every measured page is 271px wide, as before the change (the header's known 260-270px case).
  - **All 34 team pages at 375px:** no page scrolls sideways and no fact unit sticks out past the viewport.
  - **Played match at 375px:** the kick-off facts sit on two lines as whole units; a goal row shows "23′, Assist: F. Passlack" under the scorer.
