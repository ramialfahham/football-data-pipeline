# Rendered-page evidence — feat/62-5-competitions-index-page (#62 step 5)

> Required by #827 for any `site_v2/src/**` diff. Read from the BUILT output (`site_v2/dist/`) and
> from the running preview, never from source and never from `outerHTML` alone.
>
> Replaces the previous version wholesale, which described `feat/367-landing-page` (#367, the home
> page) — a different branch and a different page. Per that file's own note and the corrections-
> replace rule: an artifact describing a superseded/unrelated build cannot discharge the evidence
> requirement for the diff under review.

Build: `npm run build` in `site_v2` -> 48 pages emitted, `audit-seo: 49 built page(s) checked. OK.`
(48 built + `/robots.txt` = 49; the audit's own driver line: `/[lang]/competitions -> 3`).
Preview: `preview_start` name `v2`, tab `seed`, port 4321.

## 1. What renders, per locale — read out of `dist/{lang}/competitions/index.html`

| | de | en | fi |
|---|---|---|---|
| `<title>` | Alle Fußballwettbewerbe | All football competitions | Kaikki jalkapallokilpailut |
| `<h1>` | Wettbewerbe | Competitions | Kilpailut |
| canonical | `https://matchdaypilot.com/de/competitions/` | `https://matchdaypilot.com/en/competitions/` | `https://matchdaypilot.com/fi/competitions/` |
| hreflang set | de, en, fi, x-default | de, en, fi, x-default | de, en, fi, x-default |
| `.comp-row` count | 48 | 48 | 48 |
| `.comp-category` count | 8 | 8 | 8 |
| `<a>` count | 5 | 5 | 5 |
| bytes | 24,608 | 24,447 | 24,607 |

Distinct titles 3/3, distinct descriptions 3/3 — read from built output, not asserted:

```
de  Jede Liga, jeder Pokal und jeder internationale Wettbewerb, den wir abdecken, gruppiert nach Art und Region.
en  Every league, cup and international competition we cover, grouped by type and region.
fi  Jokainen sarja, cup ja kansainvälinen kilpailu, jota seuraamme, ryhmiteltynä tyypin ja alueen mukaan.
```

None byte-identical across locales; `check_copy_gate.py` passes independently (see §6).

Breadcrumb (EN, verbatim from `dist/en/competitions/index.html`, `<nav class="crumb"
aria-label="...">`): `Home › Competitions` (`Home` a real link to `/en/`, `Competitions` an inert
`<span class="here">`, matching the established crumb pattern on every other page).
DE: `Startseite › Wettbewerbe`. All three locales' `aria-label` is the translated
"breadcrumb navigation" string, not the literal English word — a naive `aria-label="breadcrumb"`
grep misses it; this was confirmed by reading the raw markup, not by that grep.

`48` matches the full row count in the committed `competition_index.json` (all rows render, none
dropped) and `8` matches the number of distinct `competition_type` values present in that file —
both counted independently from the file, not copied from the acceptance-criteria wording.

## 2. Anchor inventory and row inertness — decision 3, verified two ways

**Built output**, all three locales, identical shape: 5 anchors —
`["/{lang}/", "/{lang}/competitions/", "/{lang}/competitions/", "/{lang}/", "/{lang}/"]` — 3× home
(logo, breadcrumb, footer or nav-adjacent link already present on every page) and 2× the
competitions page itself (the crumb "here" is a span, not a link — the 2 hits are the swapped
`SiteHeader` nav item plus... re-derive, don't assume: these are the only two ways this build
links to `/competitions/` at all, both pre-existing chrome, not something this page's body adds).

**Live DOM, same page** (`document.querySelectorAll('a')` in the running preview): identical 5
hrefs, byte-for-byte the same list as the built HTML — confirms dev preview and static build agree.

**Row inertness, live-checked directly rather than inferred from the component source**:
`document.querySelectorAll('.comp-row')` → 48 elements, all `<div>`, zero of them are or contain an
`<a>` (`rowsWithAnchor: 0`). No row is a link anywhere in the rendered output — decision 3 (#47 not
built, rows stay inert until it ships) holds in what actually renders, not just in the component's
source intent.

## 3. Geometry, measured live (not derived from CSS source)

**Mobile, 375×812** (the preset last used to find and fix the overflow bug in §4):
`documentElement.clientWidth` 375, `scrollWidth` 375 — no horizontal overflow anywhere on the page,
`.inner` renders at its actual 375px (below the 680px cap, so the cap doesn't bind). 8 categories,
48 rows, `pageScrollHeight` 3,970px.

**Desktop, 1280×900**: `.inner`'s computed `max-width` is `680px` and its measured
`getBoundingClientRect().width` is exactly `680` — decision 1 (ship at 680px, not the mock's
1080px) is what's actually rendering, not just what the CSS says on paper. The first category's
`.comp-grid` computes `grid-template-columns: 308px 308px` — two columns, matching decision 1's
"two-column layout, not three." `documentElement.scrollWidth` 1265 equals `clientWidth` 1265 — no
horizontal overflow at this width either. `pageScrollHeight` 2,561px (shorter than mobile, as
expected from two columns instead of one).

## 4. Mobile overflow bug — found and fixed this round, not present in the original build

While gathering geometry for this evidence file, the region filter (8 buttons: All + 7
confederation codes, very different label lengths — "All" vs "North & Central America") was found
overflowing the mobile viewport. The shared `.seg` class (used elsewhere for 2–3 short, similar-
length labels, e.g. the fixture page's H1/H2 toggle) is `display:flex` with no `flex-wrap` and
`.seg-btn{flex:1}` — fine for short equal-length labels, broken for 8 labels of very different
length.

**Before fix** (measured at 375×812): `documentElementScrollWidth: 645` vs `clientWidth: 375` — 4
of the 8 region buttons extended past the right edge of the viewport.

**Fix**: added a `.seg.wrap` modifier in `system.css` (`flex-wrap: wrap` +
`.seg-btn{flex:0 1 auto}`), applied only to the region filter's container
(`class="seg wrap"` in `CompetitionIndexGrid.astro`). The 3-item entity filter (All/Clubs/National
teams — short, similar-length labels) stays on the plain, non-wrapping `.seg` behaviour; nothing
about its rendering changed.

**After fix, re-measured this round** (§3 above, both at mobile 375×812 and desktop 1280×900):
`overflowingRegionButtons: 0` at both widths, `scrollWidth` equals `clientWidth` at both widths.

This is exactly the class of defect `bi-analyst-reviewer`'s live-rendering requirement exists to
catch: `node --test`, `check-page-specs.mjs` and `check_copy_gate.py` were all green through this
entire bug's lifetime — none of them touch geometry.

## 5. Filter behaviour, live-verified (both axes, including the combined-empty case)

Clicking the `Clubs` entity-filter label and the `Oceania` region-filter label together (the two
narrowest live filters — the current data has zero club competitions in OFC) leaves zero visible
`.comp-row` elements; the inline script's `applyEmptyCategoryCollapse()` then sets `hidden` on
every `.comp-category` (all 8, since none has a surviving visible row), and the page shows no
empty-state placeholder — matching the acceptance criterion ("a category left with zero visible
rows disappears entirely, no empty-state placeholder"). Un-checking either filter restores the
previously-hidden categories via the same script re-running on `change`.

## 6. Not covered here

No BigQuery was queried in this session (the underlying `competition_index.json` was already
priced and committed in the prior #62-step-4 MR, `!67` — this diff makes no export or dbt change).
`python scripts/check_copy_gate.py` and `node scripts/check-page-specs.mjs` were run and are green,
but their pass/fail output lives in `.claude/task/acceptance_evidence.md`, not duplicated here.
Screenshots were not taken — `computer{action:"screenshot"}` fails in this environment ("the
Browser pane is not displayed, so the page is not compositing frames"), a known, previously-
documented limitation; geometry and DOM state were instead verified directly via
`javascript_tool`/`read_page`, which do work and are what every measurement above is drawn from.
