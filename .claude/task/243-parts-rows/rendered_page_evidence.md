# Rendered pages — before and after, every difference with its reason

"Before" is a checkout of main at e6f7f6fb served on port 4328; "after" is this branch served on
port 4327. Both carry the same local data, national teams included. A Playwright capture per page
read the server's HTML, then at 375px and 1280px loaded the page, let it fit its blocks, checked
each tab's radio in turn, and saved the rendered DOM and a full-page screenshot.

Pages, each in EN, DE and FI: Home, Matches, Competitions, Teams, Players, the Bundesliga overview,
its matches and its stats page, `/teams/bayern-munchen/` and `/teams/germany/` (three tabs each),
the played match Hoffenheim against Dortmund, the upcoming match Leverkusen against Freiburg (recent
form, players to watch, head to head) and `/players/h-kane-184/` (two tabs). 256 files: 39 server
HTML, 108 rendered DOMs, 108 screenshots plus one index.

The DOM comparison sorts each tag's attributes and drops the dev server's own toolbar script.

## Pixels

102 of 108 screenshots are identical, byte for byte. Six differ, all on the Player page at 1280px
(EN, DE and FI, both tabs), in the Recent matches rows:

- **HOME or AWAY after the opponent's name takes one space more.** The Team and match pages wrote
  the result row with a space before HOME or AWAY, the Player page without one, so the one result
  row component takes one of the two. It takes the Team page's: three pages (club, national team,
  match) against one, and the form the club and national team pages were reviewed in. At 375px
  HOME or AWAY sits on the second line, so nothing moves there.

## DOM, no pixel change

- **Whitespace between tags only** (Bayern, Germany, Home, Teams, Players, the Bundesliga overview
  and stats page): a row written inside a list's loop had no whitespace between its tags; written
  in its component, a line break between tags is one space. Every one of these sits between block,
  flex or grid items, where a space draws nothing.
- **Competitions:** a competition's region text loses the spaces around it (`" Europe "` becomes
  `"Europe"`); the region is a block of its own, so leading and trailing spaces draw nothing.
- **Player page:** each Recent matches row carries `data-fixture`, as every other result row
  already did. Nothing reads the attribute.
- **Upcoming match, Players to watch:** the position line is the player row's one form,
  `ps facts-line` holding a span, as on the line-up, the Squad and the Players page.
- **Upcoming match, Head to head:** the meeting row's separator between the two clubs keeps its
  text and loses surrounding whitespace.
- **Played match, line-up:** the minutes take the player row's one form, `pstat facts-line`, as
  on Players to watch.
- **Team page, Squad, a player without a photo:** the initials sit in a span inside the photo
  circle, as on every other player row; the circle is a grid that centres its one item either way.
  No squad row without a photo appears on the captured tabs.

## Links

Every `href` in the 256 files is the same before and after. A table row that leads nowhere is now
a plain row instead of a link without an address; on the local data that is 0 rows (every standings
and deserved-points row has a team page, and the match leaders' rows were already plain rows).
