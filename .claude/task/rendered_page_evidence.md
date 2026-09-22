# Rendered page evidence — `fix/menu-leaderboards`

What changes on a rendered page: one word, in three places — the sixth item of the header nav,
the same item inside the mobile drawer, and the fourth link of the footer row — on every page of
the site, per locale. No markup, class, CSS, layout or link changes; the element is the same
`<span>` it was, rendering a different string.

## How it was observed

The built `dist` swept page by page for the nav's last item and the footer row (the counts are in
`acceptance_evidence.md`), plus headless Chromium (Playwright, the engine
`check_design_inventory.py` uses) over the served build at **375**, **700** and **1280** px in EN,
DE and FI on Home and the competition Overview. Per page: the nav's computed `display`, its
`scrollWidth` against its `clientWidth`, the last item's text, tag, `href`, width and font, the
drawer's last item, the footer row's text, and the document's `scrollWidth`. `nav.json` and the
header screenshots are in the session scratchpad under `navrenders/`.

## What was observed

The item is a `<span>` with `href` null at every width in every locale — still dead text — at
13px, and the nav never overflows (`scrollWidth == clientWidth` on all nine renders).

| locale | word | item width @700 and @1280 | nav display @375 | nav fits |
|---|---|---|---|---|
| EN | Leaderboards | 98 px | `none` (drawer) | yes |
| DE | Bestenlisten | 89 px | `none` (drawer) | yes |
| FI | Kärkilistat | 76 px | `none` (drawer) | yes |

At 375px the header nav is `display: none` and the six items live in the hamburger drawer, which
is closed at rest — the word is in it (measured: the drawer's last child reads Leaderboards /
Bestenlisten / Kärkilistat), at zero size until the drawer opens. The footer row at 1280px reads
`… Players · Leaderboards · About` in EN and the same position in DE (`Spieler · Bestenlisten ·
Über uns`) and FI (`Pelaajat · Kärkilistat · Tietoa`).

The German word is the longest of the three and the one worth watching; at 89px in a nav whose
row measures 469px against 469px of space, it has room.

⚠ Unchanged and not this branch's: at 700px the page still scrolls sideways (732 EN / 738 DE /
721 FI against a 700px viewport) because of the header's search control, on every page including
the ones this branch does not touch. Recorded because it is visible in the same renders, not
because it moved.
