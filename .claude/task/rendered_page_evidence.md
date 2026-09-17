# Rendered page evidence — `feat/153-design-inventory` (#153 items 1–3)

Read by `scripts/check_design_inventory.py` (headless Chromium, Playwright 1.63.0, viewports
375×900 and 700×900, `reduced_motion: reduce`, one context per viewport) from `site_v2/dist`
built by `astro build` on the committed sample (`competitions/BL1/2026.json`; the untracked
`DFBP` and `EURO` payloads parked outside the tree, or the SEO audit refuses the build) and
from a fresh render of every mock generator the block standard lists. Every number is what the
check printed or what a probe beside it read from the same DOM.

## 1. The full run

`python scripts/check_design_inventory.py --langs en,fi,de` →
`18 pages · 2 viewports · 3 languages · 82 renders · 0 failures · 0 warnings`, exit 0.
Built: Home, Competitions index, Competition overview (`en/bundesliga/`), Match page
(`en/bundesliga/matches/2026-09-18-bayern-munchen-vs-1-fc-union-berlin/`), Team page
(`en/teams/1-fc-koln/`), each in en/fi/de. Mocks (en, fi by the FI toggle): competition-overview,
competition-matchdays, competition-rankings, home, competition-hub league/groups/cup/offseason,
matches next/past, top players, top teams, home legacy.

## 2. What the same check measured BEFORE the consolidation (the mocks, `--no-built`)

`16 pages · 2 viewports · 2 languages · 54 renders · 252 failures` on the tree as it stood after
!195, among them: `Block heading · font-size=13px · measured 11px` on every older mock;
`Block heading gap · gap(next)=14px · measured 49.0px` on the approved Matchdays render and the
four hub kinds (34px group margin + 15px date-heading padding), `23.0px` on the offseason hub
(the fact row's 9px), `43.0px` on the legacy Home; `Row link · hover · measured rgb(22, 25, 32)`
(the surface) on every older mock and `press · measured ink@11%` on the four newest (the
overlay's `.fx a:hover` outranked `:active`); `Fact row value · measured 14px / 600 / ink`;
`Ordered-by number · measured ink` on the deserved boards; `Table row · border 1px`; `Tab bar ·
scrollWidth 355 > clientWidth 343` (EN) and `398 > 343` (FI) on the four-tab hub; `Tag ·
text-transform none · font-weight 400` on the Next tag; `Breadcrumb current page · measured
rgb(139, 144, 153)` (the mock CSS inverted the site's colours).

## 3. The built pages before the last two stylesheet rules

`--no-built` off, `--langs en,fi,de`: `Team page · Block heading gap · measured 35.0px` (the
hero card's inner margin — resolved by reading a bordered box's edge as the first line, which is
what a reader sees), `Match page · measured nothing` (the segment control's 1×1 radio was taken
for a sibling), `Competition overview · measured 27.0px` (the first match row's 12px padding
under "Next matches": the rule now zeroes it, as it zeroes a first fact row's). Then
`Team page · 29.0px` at 375 (the first year-over-year row's 10px padding) and `19.0px` at 700
(the label baseline-aligned 5px under its 18px number): the row's padding is zeroed like a fact
row's — the second row too in the two-column layout — and the first line is the topmost edge
inside the sibling, the number, not the label.

## 4. The Matchdays picker after the nesting (fresh render, 375px)

Visible matchday at load: `4`; after the visible step's next arrow: `5`; after prev twice: `3`;
`#md-3` focused, ArrowRight: `4` checked, `4` visible. `.mdstep` laid out: 1 of 34.
Markup vs the render of record with the nesting normalised away: 0 residual diff lines over 538.

## 5. The built competition tab bar

`dist/{lang}/bundesliga/index.html` → en `Overview | Matchdays | Rankings`, de `Übersicht |
Spieltage | Rankings`, fi `Yleiskatsaus | Kierrokset | Rankingit`; the check's `Tab bar · fits`
and `Tab · one-line` pass at 375 in all three. The four-tab bar it replaces measured
`355 > 343` (EN) and `398 > 343` (FI) on the hub mock before this branch.

## 6. The RED proof

`red.html` at 375 and 700: `Block heading · measured 11px`; `Block heading gap · measured 34.0px`;
`Row link · hover · rgb(22, 25, 32)` and `press · rgb(22, 25, 32)`; `Table row · border 1px` and
`[table 1] · row 1 measured color(srgb 0.945098 0.952941 0.968627 / 0.05), expected plain`;
`Tab bar · scrollWidth 376 > clientWidth 343` (375 only); `Fact row value · 14px / 600 / ink`.
`green.html`: `2 renders · 0 failures`. An empty page: `expected inventory elements · measured 0`.
