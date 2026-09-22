# Rendered page evidence — `fix/menu-statistics`

What changes on a rendered page: one word, in three places — the sixth item of the header nav,
the same item inside the mobile drawer, and the fourth link of the footer row — on every page of
the site, per locale. No markup, class, CSS, layout or link changes; the element is the same
`<span>` it was, rendering a different string. The word is shorter than the one it replaces in
all three languages, so nothing can gain an overflow it did not have.

## How it was observed

The built `dist` swept page by page for the nav's last item and the footer row (the counts are in
`acceptance_evidence.md`), plus headless Chromium (Playwright, the engine
`check_design_inventory.py` uses) over the served build at **375**, **700** and **1280** px in EN,
DE and FI on Home and the competition Overview. Per page: the nav's computed `display`, its
`scrollWidth` against its `clientWidth`, the last item's text, tag, `href`, width and font, the
drawer's last item, the footer row's text, and the document's `scrollWidth`. `nav.json` is in the
session scratchpad under `navrenders/`.

## What was observed

The item is a `<span>` with `href` null at every width in every locale — still dead text — at
13px, and the nav never overflows (`scrollWidth == clientWidth` on all nine renders).

| locale | word | item width @700 and @1280 | nav row | nav display @375 |
|---|---|---|---|---|
| EN | Statistics | 70 px (was 98) | 435 px in 435 | `none` (drawer) |
| DE | Statistiken | 79 px (was 89) | 459 px in 459 | `none` (drawer) |
| FI | Tilastot | 61 px (was 76) | 438 px in 438 | `none` (drawer) |

At 375px the header nav is `display: none` and the six items live in the hamburger drawer, closed
at rest. The footer row at 1280px reads `… Players · Statistics · About` in EN, `… Spieler ·
Statistiken · Über uns` in DE and `… Pelaajat · Tilastot · Tietoa` in FI.

⚠ Unchanged and not this branch's: at 700px the page still scrolls sideways because of the
header's search control, on every page including the ones this branch does not touch.
