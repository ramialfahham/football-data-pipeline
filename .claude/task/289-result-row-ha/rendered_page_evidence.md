# Rendered page — the Result row's two-line form

Measured in Chromium (Playwright), branch build against main 0953e41c's build, each page loaded once
per build and resized through 280–1010px in 10px steps; every result row compared one to one.

| Page | Language | Two-line rows | H/A not opening line 2 | H/A on line 1 in two lines | Chip or score off line 1 | One-line rows moved | Over two lines without a wrap |
|---|---|---|---|---|---|---|---|
| Match | EN / DE / FI | 109,557 / 118,973 / 101,487 | 0 | 0 | 0 | 0 | 0 |
| Team | EN / DE / FI | 3,125 / 3,495 / 2,955 | 0 | 0 | 0 | 0 | 0 |
| Player | EN / DE / FI | 12,828 / 13,849 / 13,293 | 0 | 0 | 0 | 0 | 0 |

Rows over two lines by a wrap between words or items, which criterion 5 allows: a long opponent's
name at the narrowest widths, and line 2 with a long competition ("Auswärts · AFC Champions League ·
26. Okt.") in rows up to about 420px wide. A Player row's own line (minutes, goals, assists) stays under line 2 as the
approved Player page has it; it is a separate registry part and is not counted against the two.

Home or away left alone in the one-line form, where a name still wraps: Match EN 4,197, DE 3,620,
FI 4,655 against main's EN 18,352, DE 25,957 and FI 15,339 home or away left alone on a line.

The header's line: `border-bottom` on `.mp .mast .team` read 1px solid under the first team on
main at 375 and 560px, upcoming and played, EN, DE and FI; the branch's built stylesheet carries no
border on `.mp .mast .team`.

Before the script marks a list, and with JavaScript off, every result row shows exactly one home or
away: 11,070 rows each way (60 Match, 34 Team and 30 Player pages per language at 280, 360, 420,
560, 700 and 1010px), 0 with both or neither.

The design check (`scripts/check_design_inventory.py --pages "Match page,Played match page,Team
page,Player page" --no-mocks`, 280–1010px, EN, DE, FI), with the Fitted block rule naming the
result lists: 10,494 renders, 0 failures, 0 warnings; Match page scroll 2184, overflow 12, split 2,
classes 1; Played match page scroll 2, classes 1; Team page overflow 3; Player page 0 — main's
baseline.

Gates: check_component_registry.py 0 failures (146 table rows), check_page_css.py 0 counts off the
baseline, the copy, layer, i18n and description gates pass; site npm test 195 passed, fitBlocks.test.mjs
included; tests/test_check_component_registry.py and tests/test_design_inventory.py 103 passed.

No screenshot: the Browser pane's screenshot fails on this machine, so the evidence is the computed
layout.
