# Rendered page evidence — no word breaks at its hyphen, and the design check opens every tab

## The design check, every tab of every page

`npm run build` in `site_v2` (the committed sample data), then `scripts/check_design_inventory.py --no-mocks` on
this branch, which opens every tab, at 280, 320, 360, 375, 700 and 1010px in EN, DE and FI. Windows; on main the
same run gives main's Linux pins on every page except the Team page, whose tabs it now opens.

| Page | Split on main's pin | Every tab, main | Every tab, this branch |
|---|---|---|---|
| Match page | 223 | 223 | 2 |
| Team page | 47 | 56 | 0 |
| Home | 13 | 13 | 0 |
| Teams page | 3 | 3 | 0 |
| Competition overview | 21 | 21 | 21 |

- **What is left:** the Competition overview's 21 are the deserved points table's head labels breaking inside a plain word ("verdienten", "Difference"), and the Match page's 2 are a score ("0–0.") breaking at its en dash in the match header; neither has a hyphen, both are within main's pins.
- **Team page, Name in whole words:** 3 failures on main ("Saint-Germain", 102px, in an 82–91px name space of the Top-match row), 0 here.
- **No pin rises:** every other count equals main's; no new failure.

## The build step

- **Where it acts:** on the build, 0 spans inside an attribute, `<title>`, `<option>`, SVG `<text>` or `<script>` (a grep over every built page).
- **What it keeps:** the Paris Saint-Germain Team page has its `<title>` "Paris Saint-Germain FC: Stats, Form, Squad & Fixtures" unchanged and 38 `<span class="nb">Saint-Germain</span>` in its body.
- **Text:** the visible text is unchanged; the unit test compares a page's text before and after.

## Build cost at full scale

The parked Player page state with every player page (57,423 pages, 4.1 GB), built twice per state on this machine,
with the build's node process sampled every 10 seconds:

| | Without the step | With the step |
|---|---|---|
| Peak memory | 695 MB | 741 MB |
| Build time, run 1 / run 2 | 462 s / 298 s | 431 s / 378 s |

- **The step itself:** run alone over all 57,424 built pages, 23.9 s in all, 0.42 ms per page, 56 ms at most; the output grows by 0.10%.
- **Why the memory stays flat:** the middleware sees one page's response at a time and lets it go, so the step works per page by construction.
- **Time:** the two runs of one state differ more than the two states do, so the build time is within this machine's noise; the step's own 24 s is the measure.

## CI time of the design check

The check of main and the check of this branch, each run on this branch's build on one machine, at the scope a
merge request runs (280 and 1010px, EN and DE, `baseline_quick.json`) and at the full scope main runs:

| Scope | Main's check | This branch's check |
|---|---|---|
| Merge request | 227 s | 263 s (+36 s, +16%) |
| Full | 665 s | 741 s (+76 s, +11%) |

- **In CI:** validate:ui takes about 11 minutes on a merge request and 36 to 41 minutes on main's last four pipelines.

## Player row

Players to watch at 280px in DE, every match page: before the gap change, 3 rows ran 4–8px past their box
("Francis-Ikechukwu Onyeka", "Don-Angelo … Annum-Assamoah", "S. Idumbo-Muzambo"); after it, none. The row's gap,
measured on the DFB-Pokal match pages: 8px at 280, 10.3px at 375, 9.2px at 700, 13.1px at 1010 (main: 12px).
