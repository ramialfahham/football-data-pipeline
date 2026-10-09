# Rendered page evidence — #166 part 3: the next match page

Read from the dev server (`npm run dev`) in the Browser pane: page text, accessibility text and DOM geometry
measured by script. No screenshot: the pane's screenshot tool fails in this environment, so layout was measured
instead. The page is a gitignored copy of the real Borussia Dortmund vs SV Werder Bremen payload (fixture of 9 Oct,
exported once from prod, 125 MB read), served under a `-check` slug and deleted after the check.

| Page | 375px | 700px | 1010px |
|---|---|---|---|
| /en/bundesliga/matches/…-check/ | no sideways scroll; teams in 1 column; 15 of 15 result rows on two lines (list 343px); trail shows Competitions › Bundesliga › Matchdays, opened at its end | page content 0 elements past the edge; teams in 3 columns; lists side by side (297px), their 10 rows on two lines, the 5 meetings on one line | no sideways scroll; teams in 3 columns |
| /de/bundesliga/spiele/…-check/ | content 0 past the edge; teams in 1 column | content 0 past the edge; teams in 3 columns | no sideways scroll |
| /fi/bundesliga/ottelut/…-check/ | content 0 past the edge; teams in 1 column | content 0 past the edge; teams in 3 columns | no sideways scroll |

At 700px the document is 704px (EN), 729px (DE) and 707px (FI) wide. The one element past the edge is the site
header's `.header-actions`, as on every page today; block_standard.md's Header row reports it as a warning.

Observed text (EN): the kick-off line "Matchday 5 · Fri, 9 Oct 2026 · 18:30 UTC · Signal Iduna Park"; standing
chips "#1 · 12 pts · GD +7" and "#8 · 7 pts · GD 0"; Form comparison intro, pills WWWWW and WDWLW, 35 rows in eight
groups; Recent matches with competition names (Bundesliga, UEFA Champions League, DFB-Pokal); Players to watch
"S. Guirassy, Forward, 2 goals · 2 assists" first, "M. Grüll, Midfield, 2 goals · 3 assists" first; Head to head
"Borussia Dortmund won 3 of the last 5 meetings, and 2 were drawn." and five meetings, e.g. "0–2 SV Werder Bremen
– Borussia Dortmund · Bundesliga · 16 May 2026".

DE: pills SSSSS / SUSNS, "Spieltag 5 · Fr., 9. Okt. 2026 · 18:30 UTC". FI: pills VVVVV / VTVHV, H/A letters K/V,
"Kierros 5 · pe 9.10.2026 · 18.30 UTC". The console shows no errors. The design check on this page (EN, DE, FI at
375, 700 and 1010px) reports 0 failures in 9 renders.

After review round 1 the page was built again with the same payload: the trail's levels carry the class `lvl`
(no `.seg` rule reaches them), the fourth level reads Matchdays, the group head shows the Bundesliga logo from the
competition index, and the design check again reports 0 failures in 9 renders.
