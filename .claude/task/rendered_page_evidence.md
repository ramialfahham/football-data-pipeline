# Rendered page evidence — `feat/151-rankings-tab` (#151)

What changes on a rendered page: a new page, the Rankings tab at `/{lang}/{slug}/rankings/` (header ·
tab bar · Team rankings · Player rankings, the boards as `.ctab.rkt` single-value tables under
`.rkgroup` headings); the Overview's blocks (Next matches gone, the two deserved boards replaced by
the `.ctab.dpt` deserved points table, the six fact rows inert); the Rankings tab of the bar now a
link on every competition page with a board. Every element is one the block standard already
rules; no element, class or CSS rule is added (`.ctab.dp` is removed).

## How it was observed

Headless Chromium (Playwright, the engine `check_design_inventory.py` uses) over the sample build
served over HTTP from `site_v2/dist`, at **375** and **700** px, in EN, DE and FI, on three pages
each: `bundesliga/rankings/` (measured first at `/stats/`, then again after his rename — identical readings), `bundesliga/` (the Overview) and Home. For every page: the document's
`scrollWidth` against the viewport; the tab bar's `scrollWidth` vs `clientWidth` and each tab's
left, width and font size; every block name's text and font size; every metric group heading's
text, font size and bottom border; every board name's box and overflow; the notes; the first
ordered-by numbers' size, weight and colour; the player rows' sub-line; the deserved table's head.
Screenshots (`<page>@<viewport>.png`) and `rendered.json` are in the session scratchpad under
`renders/`. The measured check itself: `20 pages · 2 viewports · 2 languages · 80 renders · 0
failures · 0 warnings`.

## What was observed

**375 px, page scrollWidth 375 on all nine pages (no sideways scroll).** The tab bar fits in
every locale: `scrollWidth 343 = clientWidth 343`, three tabs sharing the row at 13px (the
container query under 430px), e.g. FI `Yleiskatsaus 119 · Kierrokset 108 · Rankingit 108`, DE
`Übersicht 112 · Spieltage 111 · Rankings 112`, EN `Overview 109 · Matchdays 117 · Rankings 109`.
No board name overflows its box in any locale (the longest, FI `Maalilaukaukset vastaan ottelua
kohden`, wraps inside the head cell).

| element | measured | rule |
|---|---|---|
| block name `.sechead .eyebrow` | 13px on every page (Team rankings · Player rankings; Table · Deserved points table · The season in numbers; Home's three) | 13px |
| metric group heading `.rkgroup > .gh .nm` | 17px, border-bottom 0px, 13 per Rankings page (6 team groups, 7 player groups) | 17px bold, no line |
| ordered-by number `.ctab .n.pts` | 15px / 700 / rgb(59,176,114) on the boards (3.5, 3.0, 2.8) and on the Overview's Pts and Deserved | bold 15px accent |
| board sub-line `.ctab.rkt .tm .ent .sub` | 12px, the club under the player's name | 12px muted |
| note `.bnote` | 0 per page, in all three locales; the ascending boards read "Goals against per match  0.5" and "Shots on goal against per match  2.0" | no board states a direction |
| deserved head `.ctab.dpt .ctab-head .h` | `# · · Balance · Deserved · Pts · Diff` (DE `Bilanz · Verdient · Pkt. · Diff.`, FI `Tase · Ansaitut · P · Ero`) | the ruled columns |
| fact rows | `a.frow` 0, `div.frow` 6 on every Overview | inert until #140 |

**700 px:** the tab bar fits (624 = 624, 14px tabs); every block name, group heading and board
name measures as above. Page scrollWidth is 700 on the EN pages and **707 (FI) / 728 (DE)** on the
Rankings page, the Overview and Home alike — the site header's search control (`div.header-actions`),
which this branch does not touch; the same pre-existing overflow the #152 evidence recorded on
the team and fixture pages and Home, still not this MR's. The measured check does not measure page
scrollWidth, so it passes; the fact is stated here rather than hidden.
