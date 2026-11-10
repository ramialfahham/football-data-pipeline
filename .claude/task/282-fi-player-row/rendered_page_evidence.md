# Rendered page — the player row under 280px

Measured in Chromium (Playwright) on this branch's build, every `.plrow` on the Match pages (548
per language, 1,879 rows) and Team pages (34 per language, 999 rows). "Row" is the row's `.lrow`
content width, the box the container query reads; linked rows (`a.lrow`) and plain rows measure
the same, because the link's 12px padding is offset by its -12px margin.

| Width | Match row | Match rows in the narrow form | Team rows in the narrow form | Rows sticking out, branch | Match rows sticking out, main |
|---|---|---|---|---|---|
| 280px | 248px | all | all | 0 | FI 5 |
| 300px | 268px | all | — | 0 | FI 1 |
| 310px | 278px | all | — | 0 | — |
| 320px | 288px | 0 | 0 | 0 | — |
| 360px | 328px | 0 | 0 | 0 | — |
| 375px | 343px | 0 | 0 | 0 | — |
| 560px | 243px (two columns) | all | — | 0 | FI 6, DE 3 |
| 600px | 261px (two columns) | all | — | 0 | FI 3 |
| 630px | 275px (two columns) | all | — | 0 | 0 |
| 640px | 279px (two columns) | all | — | 0 | — |
| 700px | 307px (two columns) | 0 | 0 | 0 | — |
| 1010px | 437px | 0 | 0 | 0 | — |

Each count holds for EN, DE and FI. "—" is a width not measured for that column. In the narrow
form the numbers take up to two lines (45px) in DE and FI and one in EN, in the right-hand column;
the position beside them takes up to three lines (54px).

Design check (`scripts/check_design_inventory.py --pages "Match page,Played match page,Team page"
--no-mocks`, 280–1010px, EN, DE and FI): 0 failures; Match page scroll 2184, overflow 12, split 2,
no miss lines, which is main's baseline.

No screenshot: the Browser pane's screenshot fails on this machine, so the evidence is the computed
layout and the design check's measurements.
