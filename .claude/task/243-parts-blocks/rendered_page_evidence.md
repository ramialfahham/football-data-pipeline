# Rendered pages — before and after, every difference with its reason

"Before" is a checkout of main at 6b80c12e served on port 4328; "after" is this branch served on
port 4327. Both carry the same local data, national teams included. A Playwright capture per page
read the server's HTML, then at 375px and 1280px loaded the page, let it fit its blocks, checked
each tab's radio in turn, and saved the rendered DOM and a full-page screenshot. The DOM
comparison sorts each tag's attributes and drops the dev server's own toolbar script.

Pages, each in EN, DE and FI: Home, Matches, Competitions, Teams, Players, the Bundesliga overview,
its matches and its stats page, `/teams/bayern-munchen/` and `/teams/germany/` (three tabs each),
the played match Hoffenheim against Dortmund, the upcoming match Leverkusen against Freiburg, the
nation page `/players/spain/` and `/players/h-kane-184/` (two tabs). 271 files: 42 server HTML,
114 rendered DOMs, 114 screenshots plus one index.

## Pixels

111 of 114 screenshots are identical, byte for byte. The three others are the nation page at
1280px (EN, DE and FI). Two captures of main itself differ there in the same rows: the player
photos load lazily and a full-page screenshot catches them part-way. The rendered DOM of those
three readings is identical before and after.

## DOM, no pixel change

- **The filter script's tag moved** on the Competitions, Matches, Players, nation and Player
  pages: the filter bar's script is now emitted by the filter bar component, so its `<script
  type="module">` tag sits at a different place in the page. A module script runs after the page
  is parsed wherever its tag stands, and the page loads it once.
- No other difference: the explainers, filter radios, buttons and dropdowns render the same
  markup as before.

## A case the captured pages do not show

- **A player whose first comparison has no metric group:** the Player page's comparison chooser
  checked the radio of comparison 1, which is then absent, so no comparison was chosen. The filter
  bar checks its first choice, so the first comparison that has groups is chosen. No captured
  player page has such a comparison.

## Links, text and filters

Every `href` in the 271 files is the same before and after (14,868 links), and the visible text of
every captured page is the same, so every filter offers the same choices in the same order.
