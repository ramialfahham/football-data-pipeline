# Rendered page evidence — the chart theme and its checks

Read on the committed sample build (`npm run build` in `site_v2`, 2,272 pages), served from
`site_v2/dist` on a local port and opened in headless Chromium.

## Scatter plot, 1. FC Köln Team page (EN)

| Width | Form | Team dot | Other dot | Tick text | Axis |
|---|---|---|---|---|---|
| 280 | narrow | 10px | 6px | 11px | 1px |
| 479 | narrow | 10px | 6px | 11px | 1px |
| 480 | narrow | 10px | 6px | 11px | 1px |
| 700 | wide | 10px | 6px | 11px | 1px |
| 1010 | wide | 10px | 6px | 11px | 1px |

The difference label "-1.4", after a fresh load and a click on the Performance tab, at 375px:
[134, 1037, 155, 1053], the team's dot [156, 1024, 166, 1034], the name [169, 1020, 221, 1036];
it meets nothing.

## Difference label on every Team page, reader flow

102 pages (34 teams, EN, DE, FI) × 12 widths (280, 320, 360, 375, 414, 479, 480, 560, 700, 768,
900, 1010) = 1,224 measurements with an overlap: main 957, this branch before the tab-click fix
921, after 0.

## Comparison element, Hoffenheim against Dortmund (EN, FI; 375 and 1010px, all identical)

| Part | Measured |
|---|---|
| Values | 15px 700; better rgb(59,176,114), other rgb(241,243,247) |
| Metric names | 14px rgb(241,243,247), centred, 0px off |
| "per match" | 11px rgb(139,144,153) |
| Bar | 5px; better side rgb(59,176,114), other rgb(241,243,247); lengths 100/61, 100/67 |
| Group heading | 17px 700, 26px to the first row |
| Team names | 12px 400 rgb(193,198,206), at the left and right edges |

The design check on the played match page: 0 failures over 18 renders (EN, DE, FI × 280, 320, 360,
375, 700, 1010px); unnamed classes 50 → 38; the sideways-scroll count 2 equals main's build on
the same machine.

## Last-season table

Untouched: `git diff gitlab/main -- site_v2/src/components/team/TeamLastSeason.astro` is empty; on
the built Köln page ▲ rgb(59,176,114), ▼ rgb(181,59,59), – rgb(139,144,153) (dark) and
rgb(10,110,58), rgb(178,59,59), rgb(119,119,110) (light), equal to main.
