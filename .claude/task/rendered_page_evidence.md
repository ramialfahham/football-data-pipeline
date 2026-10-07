# Rendered page evidence — #177 part 2: metric names without sigils

Read from the dev server (`npm run dev`, the committed sample) in the Browser pane, per viewport, with geometry taken
from the rendered page: for every visible label element, whether its content overflows its box (scrollWidth >
clientWidth) and every mid-word line break (two non-space characters on different lines; a break after a hyphen is
allowed).

| Page | Element | 375px | 700px | 1010px |
|---|---|---|---|---|
| /de/mannschaften/1-fc-koln/ | hero tiles (3), name + "pro Spiel" | 0 overflow, 0 breaks | 0, 0 | 0, 0 |
| /de/mannschaften/1-fc-koln/ (Leistung) | Performance rows (16) | 0 overflow, 3 breaks (Schlüsselpässe, Defensivaktionen, Zu-Null-Spiele at its hyphen) | 0, 0 | 0, 0 |
| /fi/joukkueet/1-fc-koln/ | hero tiles (3) | 0, 0 | 0, 0 | 0, 0 |
| /fi/joukkueet/1-fc-koln/ (Suoritus) | Performance rows (16) | 0 overflow, 9 breaks | 0, 0 | 0, 0 |
| /de/bundesliga/statistiken/ | board titles (24), e.g. "Gewonnene Zweikämpfe in Prozent" | 0, 0 | — | — |
| /fi/bundesliga/tilastot/ | board titles (24) | 0, 0 | — | — |
| /de/bundesliga/spiele/2026-10-09-borussia-dortmund-vs-sv-werder-bremen/ | Form comparison rows (16), "Tore / pro Spiel" | 0, 0 | — | — |

The 375px Performance-row breaks are the ones `metrics_display.md` records as open (3 German, 9 Finnish, the
name column's width); the names in them only lost their sigil, and the second line sits below the name, so it adds
no break. Every other element fits at every width.
