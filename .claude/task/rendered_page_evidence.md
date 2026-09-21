# Rendered page evidence — `feat/152-metric-groups` (#152)

What changes on a rendered page: the metric-group headings on the team page's Performance tab
(`TeamPerformance.astro`, `.vs-group > span`) and on the fixture comparison
(`MetricComparison.astro`, `.mgroup`) — their text (locale names instead of the raw English key)
and their order (the catalogue's). No markup, CSS or component structure changes; the heading
elements, their classes and their styles are the ones already on `main`.

## How it was observed

Headless Chromium (Playwright, the same engine `check_design_inventory.py` uses) over the sample
build served over HTTP from `site_v2/dist`, at **375** and **700** px, on four pages:
DE and FI `teams/manchester-united-fc/` (Performance tab, "vs league" panel) and DE and FI
`bundesliga/matches/2026-09-18-bayern-munchen-vs-1-fc-union-berlin/` (both windows). For every
heading element: textContent, bounding box, parent width, `scrollWidth > clientWidth` (overflow),
computed font; for the page, `documentElement.scrollWidth` against the viewport. Screenshots
(`<page>@<viewport>.png`) and the raw `report.json` are in the session scratchpad under
`renders/`; the Browser pane's own screenshot is broken on this machine, so Playwright's was used.

## What was observed

**375 px, page scrollWidth 375 on all four pages (no sideways scroll).** Every heading fits its
parent with no overflow; the longest are the ones the reviewer asked about:

| page | heading | width | parent | overflow |
|---|---|---|---|---|
| team DE | Eins-gegen-eins | 113 px | 343 px | no |
| team FI | Yksi vastaan yksi | 126 px | 343 px | no |
| team FI | Erikoistilanteet | 119 px | 343 px | no |
| fixture DE/FI | every `.mgroup` | 343 px (full row) | 343 px | no |

Font on every heading: 11px / 700, unchanged from `main`. Team-page headings at 375: Tore ·
Schüsse · Pässe · Eins-gegen-eins · Defensive · Torwart · Standards (DE); Maalit · Laukaukset ·
Syötöt · Yksi vastaan yksi · Puolustus · Maalivahti · Erikoistilanteet (FI). Fixture headings the
same seven per locale, once per window.

**700 px: headings fit (widest 126 px in a 624 px parent, no overflow), but the page scrollWidth
is 728 (DE) / 707 (FI).** The element past the viewport edge is the site header's search control
(`div.header-actions` → `button.iconbtn`, right edge 728) — on the team page's Overview tab, on
the fixture page and on Home `/de/` alike, none of which this branch touches. Pre-existing and
outside this task; flagged separately, not folded in.

## What the measured check saw

`python scripts/check_design_inventory.py --dist site_v2/dist` → `19 pages · 2 viewports · 2
languages · 76 renders · 0 failures · 0 warnings`, exit 0 (the same run as in
`acceptance_evidence.md`).
