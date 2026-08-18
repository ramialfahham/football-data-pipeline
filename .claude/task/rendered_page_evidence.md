# Rendered-page evidence — feat/shared-competition-order

> Required by #827 for any `site_v2/src/**` diff. Read from the BUILT output (`site_v2/dist/`) and
> the running page, never from source. Replaces the previous file wholesale (it documented
> `feat/62-5-competitions-index-page`, a different branch and page).

Build: `npm run build` in `site_v2` -> **60 pages**, `audit-seo: 61 built page(s) checked. OK.`
Served from `dist/` on 127.0.0.1:8901 and measured live.

## 1. What changed on the page, before vs after

The home page's first block. Both rows read from the committed payload and the built HTML, not
from intent.

| | Before (on `main`) | After |
|---|---|---|
| Group order | `VL, APD, UCL, UECL` | `UCL, LIBER` |
| First competition | Veikkausliiga (Finland) | UEFA Champions League |
| Fixtures shown | 12 | 4 |
| Dates spanned | **2** (2026-08-03 + 08-04) | **1** (2026-08-18) |
| `region_rank` in payload | absent | present on every group |

The before-row is the sample committed on `main`, read with `json.load`; the after-row is the
regenerated payload plus the built pages.

⚠ **The fixture COUNT dropping 12 -> 4 is not a regression.** It is the matchday rule meeting a
quiet Tuesday: 4 matches is genuinely all there is on 2026-08-18. The old 12 reached that number by
spilling into the following day, which is what the CPO's "we will show what we have" rejects.

## 2. Group order, per locale, read out of `dist/`

| | de | en | fi |
|---|---|---|---|
| Group order | UEFA Champions League, Copa Libertadores | same | same |
| `.fxrow` count | 4 | 4 | 4 |

UEFA is `region_rank` 1, CONMEBOL 3 — so the rendered order is the region order. Identical across
all three locales, as expected for an ordering rule that reads no locale.

⚠ **Today's data does not DISCRIMINATE the old rule from the new one.** UCL also kicks off earlier
(19:00 vs 22:00), so pure chronology would have produced this same order today. What proves the
change is the unit test seen RED (`acceptance_evidence.md`), not this screenshot. Recorded because
a rendered page that agrees with both rules is not evidence for either.

## 3. Geometry, measured live

At a 440px viewport: `scrollHeight` **3301px**, `documentElement.scrollWidth` equals
`clientWidth` — **no horizontal overflow**. 2 groups, 4 `.fxrow` rows.

⚠ This is a LIGHT day and the number should not be read as the block's size. `10_home.md`'s
measurement recorded a busiest day of **57** fixtures; on such a day this block is materially
taller than anything measured here. That is the accepted consequence of "show what we have", and
the decision about it (a "more matches" control, #908) is the CPO's — see the contract's
`decisions_reserved`. Not pre-empted with a new cap.

## 4. The build gate caught a real coherence break

The first build after regenerating `landing.json` FAILED:

```
- /en/: dead internal link: /en/champions-league/matches/2026-08-18-fenerbahce-vs-lyon/
  … 8 such errors across /en/ and /fi/
seo-audit: the built site violates its own page specs
```

Cause: the home page now links to the 2026-08-18 matchday, but the committed fixture sample was
still the 2026-08-03 set, so those four match pages were never built.
`site_v2/src/data/README.md` documents exactly this — *"⚠ Refresh as a set… regenerate
`landing.json`, then update the `.gitignore` allowlist and the committed files to match it, in the
same commit"* — and names `audit-seo` as the only thing that catches a mismatch. It did.

Fixed by exporting the four payloads the new landing references (1547770, 1622620, 1622621,
1622622) and adding their allowlist rows. Rebuild: **60 pages, audit OK**, fixture pages 39 -> 51.

## 5. Not covered here

The competitions page was not re-verified in the browser: `compareCompetitions` is unchanged and
its 7 tests pass unedited, so its behaviour cannot have moved. No dbt model, seed or mart was
touched. The three blocks the mock shows and the live page still lacks (Top players, Top teams) and
the browse restructure are out of this change's scope by the contract.
