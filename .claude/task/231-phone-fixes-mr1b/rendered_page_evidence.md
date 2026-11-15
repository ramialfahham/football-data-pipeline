# Rendered pages — phone widths

Tool: headless Chromium in the CI image, driven by Playwright against `site_v2/dist` (a static
server), the viewport set to 260, 280, 320, 375 and 768px, read through each page's DOM and computed
geometry. No screenshots of the pages were read; the chart screenshot pins are the check's own
output.

observed:
  - **Home, Competitions, Teams, Players, Matches and a team, a player and a match page, in EN, DE and FI:** every link and button measures 44px high, except the header icon buttons on the narrowest phones (34px wide floor); no page scrolls sideways at 280px and wider.
  - **Match page lineups, 260-375px:** the stat line "1 Tor · 1 Vorlage" wraps with the dot at the start of the second item or hidden, never at the end of a line.
