# Rendered-page evidence — feat/844-seo-build-gate (PR C2)

> Required by #827 for any `site_v2/src/**` diff. Every claim below is read from the BUILT output
> (`site_v2/dist/`), never from source and never from `outerHTML` — the rule #862 produced after a
> source grep and an `outerHTML` check both certified a defect as fixed while it was still shipping.

## 1. The live defect, before and after

`[team].astro` built its title by concatenating `team.name` and a competition name. Both are
locale-independent: `team.name` is the provider name, and `src/data/competitions.json` carries ONE
`name` per competition (verified — its entries have only `name` and `slug`, built from the
registry's single field by `_competitions_index()`). So all three locales shipped the same string.

**Before** (on `main`): `<title>Manchester United — Premier League</title>` in de, en AND fi.

**After**, read from `dist/{de,en,fi}/teams/manchester-united/index.html`:

```
de  Manchester United — Statistiken, Form & Saisonbilanz | Matchday Pilot
en  Manchester United — Stats, Form & Season Records | Matchday Pilot
fi  Manchester United — tilastot, muoto ja kauden tulokset | Matchday Pilot
    -> titles distinct 3/3, descriptions distinct 3/3

de  Palmeiras gegen Atletico-MG — Form, direkter Vergleich & Statistiken | Serie A
en  Palmeiras vs Atletico-MG — Form, Head-to-Head & Stats | Serie A
fi  Palmeiras – Atletico-MG — muoto, keskinäiset ottelut ja tilastot | Serie A
    -> titles distinct 3/3, descriptions distinct 3/3
```

**A second defect the first version of this check would have missed.** The Finnish fixture
DESCRIPTION was byte-identical to the English one (`aboutNoH2h` was `"{home} vs {away} · {round}."`
in both) while German differed. The cross-locale check as first written asked "are they ALL
identical", saw variety, and said nothing. It now fails on ANY group of locales sharing a value, and
the Finnish string was corrected. Regression-locked by a test.

## 2. The emitted surface, from `dist/en/teams/manchester-united/index.html`

```
<meta name="robots" content="noindex">
<link rel="canonical" href="https://matchdaypilot.com/en/teams/manchester-united/">
<link rel="alternate" hreflang="de|en|fi" href="https://matchdaypilot.com/{lang}/teams/manchester-united/">
<link rel="alternate" hreflang="x-default" href="https://matchdaypilot.com/en/teams/manchester-united/">
og:type / og:site_name / og:locale / og:url / og:title / og:description / og:image
twitter:card=summary_large_image / twitter:title / twitter:description / twitter:image
<script type="application/ld+json"> @graph = [BreadcrumbList(3 items), SportsTeam]
```

The `SportsTeam` node carries `name`, `sport`, `logo`, `foundingDate: "1878"`,
`location: {Place, England}`, `memberOf: {SportsOrganization, Premier League}` — every value a
served payload field, nothing computed. Canonical is absolute and self-referential on all 10 pages.

## 3. The gate FAILS, proven rather than assumed

Finnish `seoTeamTitle` was temporarily set to the English string and the build re-run:

```
audit-seo: 1 violation(s) in 10 built page(s):
  - /teams/manchester-united/: title is BYTE-IDENTICAL across en/fi — the localised template
    is not reaching the output: "Manchester United — Stats, Form & Season Records | Matchday Pilot"
seo-audit: the built site violates its own page specs (see the list above).
build exit = 1
```

Reverted; `build exit = 0`. The gate stops CI and the deploy workflow, both of which run
`npm run build`.

**It also failed for real, twice, on first run** — that is how the locale-landing defect above was
found. The first build reported 21 violations: the three scaffolds had no canonical and no hreflang
and all shipped `<title>Matchday Pilot</title>`. The original plan proposed EXEMPTING the scaffolds;
that would have hidden this.

## 4. Whole-build assertions

```
dist/robots.txt          -> "User-agent: *\nDisallow: /"
dist/sitemap-index.xml   -> present (NOT sitemap.xml — a checker looking for that passes vacuously)
dist/sitemap-0.xml       -> 9 <loc> entries = 10 built pages minus the excluded root redirect
```

The sitemap is generated while the site is `noindex` and is referenced by nothing, so its
cap-splitting and locale logic get exercised on every build instead of first running at go-live.

## 5. Page-count driver, free from the build hook

```
[seo-audit] page-count driver: /robots.txt -> 1, /[lang]/teams/[team] -> 3,
            /[lang]/[competition]/matches/[fixture] -> 3, /[lang] -> 3, / -> 1
```

Route PATTERN -> emitted file count, from `astro:build:done`'s `assets` map. This is the one thing a
`dist/` walker genuinely cannot reconstruct, and it is the honest reason the verifier is an
integration — not the `--ignore-scripts` bypass the plan cited, which does not exist in this
pipeline (neither workflow passes that flag; both run `npm run build`).

## 6. The one RENDERING change: the locale landing now composes the site chrome

**This section exists because `bi-analyst-reviewer` FAILed the first version of this document.** It
said in §1 that the landing "gained the standard header/footer" and then in §6 that "nothing changes
a pixel" — a contradiction, and the second half was wrong. `[lang]/index.astro` moved from a
hand-rolled bare `<html><body><h1>` to `Layout`, so `SiteHeader` and `SiteFooter` render on that
route **for the first time**. That is a composition #827 requires evidence for. Measured against the
live dev server, not read from source:

**Accessibility tree @ 700x800** — the composition is real and correctly landmarked:
`banner` (brand link "Matchday"+"Pilot", "Main navigation" with 6 items, search, theme toggle, menu)
→ `heading "Matchday Pilot v2 — under construction"` → the blurb → `contentinfo` (brand, 5 links,
"Imprint (pending)", "EN · DE · FI · Data: API-Football"). One `h1`, inside a real document outline.

**Geometry @ 320x720** — the width the header is tightest at:

| | px |
|---|---|
| `horizontalScroll` | **false** (`scrollWidth` 320 = viewport 320) |
| brand | 16 → 140 |
| `.header-actions` | 180 → 304 |
| **clearance between them** | **40** |
| `.mainnav` | `display: none` (below the 700px breakpoint, as designed) |
| `h1` | 16 → 304, 288 wide, no overflow |

**Console** — `read_console_messages(onlyErrors: true)` → **no errors**.

**No screenshot.** `computer{action:"screenshot"}` fails in this environment ("the Browser pane is
not displayed"), a limitation already recorded in the handover. The geometry above is the stronger
evidence for the question actually at issue — whether the chrome fits and the page overflows — since
it gives measured pixel clearance rather than an eyeball on whether two boxes touch.
