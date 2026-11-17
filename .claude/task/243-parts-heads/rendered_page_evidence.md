# Rendered pages — before and after, every difference with its reason

"Before" is a checkout of main at a10ee51f served on port 4328; "after" is this branch served on
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

114 of 114 screenshots are identical, byte for byte.

Two readings were taken again, each for a cause outside the page:

- **Home, EN, 375px, after:** the dev server's error overlay, left from an earlier reload, covered
  the first page captured. It was taken again: identical.
- **Players, EN, 1280px, before:** the hidden filter dropdown carried `fit-two` in the first
  capture of main and not in a second one. The fit class of a hidden dropdown follows load timing,
  not the markup. It was taken again on main: identical to after.

## DOM, no pixel change

- **Whitespace between tags only** on every page: a part written inside a page's loop had no
  whitespace between its tags; written in its component, a line break between tags is one space.
  Every one sits between flex, grid or block items, where a space draws nothing.

## Links and text

Every `href` in the 271 files is the same before and after (14,868 links), and the visible text of
every captured page is the same.

## Forms the captured pages do not show

- **A competition group head without a competition page** showed its name alone on Home, Matches
  and a team's fixture groups, and its crest and name on a match page's header and next matches.
  It now shows its crest and name, the one form. No captured page has such a head: every
  competition on them has a page.
