# Rendered page evidence — the component registry and the Inter font

Method: the committed sample build (`npm run build` in `site_v2`, 2,272 pages) of this branch and of main
at d76335a3, both served from `dist` on a local port and opened in headless Chromium (Python Playwright) on
one Windows machine, at 280, 320, 360, 375, 700 and 1010px in EN, DE and FI. Both builds hold the same
2,272 pages. Main's font here is Segoe UI; CI's Linux pins were measured in another font, so "Main's pin"
below is the committed number and "Main, here" is main measured on this machine. Inter is the same file on
both systems, so this branch's numbers predict CI's; `baseline.json` takes CI's measurement.

## Inter beside today's font

The Bayer 04 Leverkusen Team page (Performance tab) and the Hoffenheim against Dortmund match page, at 375
and 1010px, rendered in today's font and in Inter side by side, went to the coordinating session before the
font was built.

## Rows past their box, every match page and Team page (1,746 pages)

`.resrow` and `.plrow` rows whose content is wider than the row.

| Width | Main, here | This branch |
|---|---|---|
| 280 | 320 | 0 |
| 320 | 0 | 0 |
| 360 | 0 | 0 |
| 375 | 0 | 0 |
| 700 | 0 | 0 |
| 1010 | 0 | 0 |

## Counts by page and width, main here to this branch

| Page | 280 | 320 | 360 | 375 | 700 | 1010 |
|---|---|---|---|---|---|---|
| Match page scroll | 1256 → 1397 | 372 → 437 | 71 → 220 | 21 → 132 | 0 | 0 |
| Match page split | 100 → 132 | 30 → 40 | 5 → 23 | 6 → 5 | 5 → 13 | 5 → 10 |
| Match page overflow | 9 → 9 | 0 → 3 | 0 | 0 | 0 | 0 |
| Match page overlap | 0 | 0 | 0 | 0 | 0 | 2 → 0 |
| Team page split | 21 → 21 | 9 → 15 | 3 → 5 | 0 → 3 | 3 → 3 | 0 |
| Home split | 0 → 9 | 1 → 0 | 2 → 2 | 0 → 2 | 0 | 0 |
| Competition overview split | 6 → 8 | 3 → 5 | 2 → 2 | 2 → 2 | 2 → 2 | 2 → 2 |
| Competitions index overflow | 15 → 18 | 6 → 9 | 3 → 3 | 3 → 3 | 3 → 3 | 3 → 6 |

By language, main here to this branch:

| Page | DE | EN | FI |
|---|---|---|---|
| Match page scroll | 702 → 856 | 716 → 879 | 302 → 451 |
| Match page split | 63 → 81 | 31 → 62 | 57 → 80 |
| Match page overflow | 3 → 4 | 3 → 4 | 3 → 4 |
| Team page split | 12 → 15 | 12 → 15 | 12 → 17 |
| Home split | 0 → 3 | 0 → 3 | 3 → 7 |
| Competition overview split | 6 → 7 | 7 → 10 | 4 → 4 |
| Competitions index overflow | 11 → 14 | 11 → 14 | 11 → 14 |

## Against main's pins

| Page | Count | Main's pin | This branch |
|---|---|---|---|
| Team page | overflow | 570 | 3 |
| Home | overflow | 227 | 0 |
| Competition matchdays | overflow | 15 | 0 |
| Match page | overlap | 2 | 0 |
| Match page | List row misses | 53 | 0 |
| Match page | Player row misses | 29 | 0 |
| Match page | Result row misses | 24 | 0 |
| Team page | Name in whole words misses | 3 | 3 |
| Match page | scroll | 1,174 | 2,186 |
| Match page | split | 148 | 223 |
| Match page | overflow | 9 | 12 |
| Played match page | scroll | 1 | 2 |
| Team page | split | 32 | 47 |
| Home | split | 4 | 13 |
| Competition overview | split | 19 | 21 |
| Teams page | split | 1 | 3 |
| Competitions index | overflow | 24 | 42 |

The last nine are the listed exception, approved in chat, 2026-11-04, each a limit that was already there
reached by wider letters: the breadcrumb scrolling sideways as designed, a hyphenated word breaking at its
hyphen, a competition name reaching its ellipsis, a long stadium name at 320px.

## Kick-off column

`.fxrow.fit-one:has(.topmatch)` on the built Team, Home, Matches and Competition matchdays pages at six
widths in EN, DE and FI: no kick-off misses `one-line` or `fits`.

The mocks were not measured here: five mock generators fail on this machine, so the mock counts come from
this MR's first `validate:ui` run.
