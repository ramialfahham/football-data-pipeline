# Rendered page evidence — `fix/german-coverage`

What changes on a rendered page: one word, in German only. The header's search control reads
`Mannschaften, Spieler suchen…` instead of `Teams, Spieler suchen…` on every German page. No
element, class, CSS rule or layout rule is added or altered; the other two languages are
byte-identical.

The second half of this branch changes no rendered page at all — it changes which pages the
measured check opens.

## How it was observed

Headless Chromium (Playwright, the engine `check_design_inventory.py` uses) over the sample build
served from `site_v2/dist`, at **375, 700, 1024, 1280 and 1440** px, in EN, DE and FI, on
`bundesliga/` (the competition Overview). The two wider-than-usual viewports are deliberate: the
control being changed is **hidden at 375 and 700**, so measuring only the check's own viewports
would have proved nothing about it. For German, the previous string was swapped back into the same
element in the same page and re-measured, so the two readings differ by the word and nothing else.

## What was observed

| viewport | `.searchbox` width, before → after | clipped | `.header-actions` | page scrollWidth |
|---|---|---|---|---|
| 375 px | hidden → hidden | — | 124 | 375 of 375 |
| 700 px | hidden → hidden | — | 80 | 728 of 700 (pre-existing) |
| 1024 px | 182 → **227** | no | 226 → 271 | 1024 of 1024 |
| 1280 px | 182 → **227** | no | 226 → 271 | 1280 of 1280 |
| 1440 px | 182 → **227** | no | 226 → 271 | 1440 of 1440 |

- **+45px on the box, +0px on the page.** `scrollWidth` equals the viewport at every width where
  the control is visible, before and after. Nothing is pushed off.
- **No clipping**: `scrollWidth <= clientWidth` on the box itself at every width.
- **German is now the widest of the three** and still fits: EN 180, FI 192, DE 227.
- **The 700px overflow is not this branch's.** 728 of 700 both before and after the change, and
  present in EN (704) and FI (707) too. It is the header's search control area, disclosed on
  earlier branches and still unfiled.
- ⚠ **The control is invisible at both viewports the design check measures.** At 375 and 700 the
  icon-only button shows instead. So the gate this branch extends still could not catch a
  search-box defect in any language — a separate gap from the one being closed, named on the MR
  head rather than folded in.

## The check's own rendering, after the change

`python scripts/check_design_inventory.py --dist site_v2/dist`, no flags:
`20 pages · 2 viewports · 3 languages (pages per language: en 20, de 7, fi 20) · 94 renders ·
0 failures · 0 warnings`.
Every built page is now opened in German as well; the 13 design mocks are not, because they carry
no German text — their generators emit an English string and a marked Finnish width probe into one
file, toggled by CSS.
