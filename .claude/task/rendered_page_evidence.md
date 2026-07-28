# Rendered-page evidence — feat/rename-matchday-pilot (PR C1)

> Required by #827 for any `site_v2/src/**` diff. Produced against the real Astro dev server
> (`preview_start` name `v2`, port 4321) and the real `npm run build` output — not the source.
>
> **This document is on its second version, and the reason matters.** Version 1 claimed
> `staleBrandAnywhere: false` from a regex over `document.documentElement.outerHTML`. That check was
> looking at the wrong surface and the claim was FALSE: `SiteFooter.astro` still rendered the old
> wordmark, so every page shipped `MatchdayPilot` in the header and `MatchdayIQ` in the footer.
> `cto-reviewer` caught it.

## The defect this document initially missed

`SiteFooter.astro:31` was never renamed. Proof, from one built page before the fix:

```
$ grep -o 'Matchday<span class="iq">[A-Za-z]*</span>' dist/en/teams/manchester-united/index.html
Matchday<span class="iq">Pilot</span>      <- header
Matchday<span class="iq">IQ</span>         <- footer, SAME PAGE
```

**Why every grep in the contract's own impact_map was structurally incapable of finding it:** the
wordmark is split across markup — `Matchday` then `<span>IQ</span>` — so the file contains no literal
`"Matchday IQ"` substring and no `mdiq`. `outerHTML` preserves that split, which is why the v1 check
passed. Only **rendered text** joins them into `MatchdayIQ`.

**The rule this produces:** verify a rename against `textContent` / `body.innerText`, never against
source greps or `outerHTML`.

A second, self-inflicted instance of the same class: the explanatory comment I first added to
`SiteFooter` was an HTML comment containing the literal old brand — and **Astro emits `<!-- -->` into
the built page**, so the note shipped the stale string straight back into the output. Both wordmark
comments are now Astro expression comments (`{/* … */}`), which are not emitted.

## Corrected check — rendered text, every built page

```
dist/de/brasileirao/matches/…/index.html    Pilot  Pilot
dist/de/teams/manchester-united/index.html  Pilot  Pilot
dist/en/brasileirao/matches/…/index.html    Pilot  Pilot
dist/en/teams/manchester-united/index.html  Pilot  Pilot
dist/fi/brasileirao/matches/…/index.html    Pilot  Pilot
dist/fi/teams/manchester-united/index.html  Pilot  Pilot
(the 3 locale scaffolds and / carry no wordmark — they do not use Layout)

$ grep -rl "Matchday IQ\|MatchdayIQ\|matchdayiq" dist/     ->  NONE
```

Live DOM, team page:

```
brandTexts          ["MatchdayPilot", "MatchdayPilot"]   (header AND footer)
allAgree            true
staleInRenderedText false      <- the check that actually answers the question
```

## Layout — the risk `bi-analyst-reviewer` raised

The wordmark grew. `.brand` is `flex: none` (`system.css:363`); below 700px `.mainnav` is
`display:none`, so only the brand and three 36px icon buttons share the row.

Measured by swapping only the wordmark text in the live DOM, so both strings were measured under
identical computed styles:

| | px |
|---|---|
| Old `MatchdayIQ` | **105** |
| New `MatchdayPilot` | **124** |
| Growth from the rename | **+19** |
| Space before `.header-actions` | **164** |
| **Clearance remaining** | **40** |

**Header @ 320x720** — `brandRight 140`, `actionsLeft 180`, **clearance 40px**, `mainNavDisplay: none`,
`horizontalScroll: false`.

**Header @ 700x800** (nav returns) — brand right 149, nav 171→583, actions left 601;
`brandOverlapsNav: false`, `navOverlapsActions: false`, no horizontal scroll.

**Footer @ 320x720** — a different container (`.footer-in`) and NOT measured in v1: brand 16→120
(104px, smaller footer type), `footerBrandOverflows: false`, `horizontalScroll: false`.

Accessibility tree confirms the approved treatment survives: `link "Matchday"` with a child
`generic "Pilot"` — the two-tone `.iq` span is still nested in the brand link, so only the word
changed.

## Console

`read_console_messages(onlyErrors: true)` → **no errors**.

## Locale interpolation — the `{brand}` indirection

```
en  Sample data · v2 preview (Matchday Pilot)
de  Beispieldaten · v2-Vorschau (Matchday Pilot)
fi  Esimerkkidata · v2-esikatselu (Matchday Pilot)
```

The placeholder INTERPOLATES in every locale rather than rendering literally. A literal `{brand}`
would otherwise have shipped silently.

## Known and deliberately untouched

`system.css:2` carries `MATCHDAY IQ — v2 DESIGN SYSTEM` in its header comment. Visible in the dev
server only, where Astro inlines CSS unminified; the build strips it, which is why the `dist/` sweep
above is clean. `system.css` is the LOCKED design system and out of scope for this PR by decision —
that comment goes with whoever next opens the file for a real reason (the owed chip-sizing change).

## Not captured, and why

**No screenshot.** `computer{action:"screenshot"}` fails here — *"the Browser pane is not displayed,
so the page is not compositing frames"* — a limitation already recorded in the handover. For this
question the geometry measurements are stronger than a screenshot: they give actual pixel clearance
rather than an eyeball on whether two boxes touch.
