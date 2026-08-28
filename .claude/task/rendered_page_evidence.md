# Rendered page evidence — batch C, the three `shooting` share metrics

Branch `refactor/metric-rename-team-shooting-shares`, base main `9e2aaf9`.

⚠ **THIS FILE WAS STALE AND IT COST A REVIEW ROUND.** Until now it held the rendered evidence for
the "export sample refresh after #90" MR — two tasks ago — and `!116` merely NAMED it as stale
rather than replacing it. `bi-analyst-reviewer` FAILed batch C round 1 for exactly that: a stale
document at the expected path is functionally the same gap as no document, and it had by then
misled two reviewers in a row. Replaced rather than named this time.

Read from `site_v2/dist/` after `npm run build` (66 pages built, `audit-seo: 67 built page(s)
checked. OK.`) — never from source, never from `outerHTML`. HTML comments are stripped before
collapsing text, because Astro splits interpolated text with `<!-- -->`.

## The fixture metric comparison — the surface this diff actually changes

Counted STRUCTURALLY (`<div class="mrow">` per row, `<div class="mgroup">` per heading, inside each
`<div class="cmp">`), not by matching label text. A substring test is not a presence test where one
label is a prefix of another, and this metric set is full of `X` / `X against` pairs.

| | before (`9e2aaf9`) | after |
|---|---|---|
| metric rows per comparison block — EN / DE / FI | 16 / 16 / 16 | **15 / 15 / 15** |
| group headings | 7 | **7 — none lost** |
| blocks with no `Goalkeeping` heading | 0 | **0** |

Across all **19** fixture pages in each locale, both windows: w1 row counts `[15]`, w2 row counts
`[15]` (min 15, max 15). Every page renders both comparison blocks — 38 `cmp` blocks over 19 EN
pages — so no page is silently absent from that aggregate.

Reference page, all three locales:
`site_v2/dist/<loc>/2-bundesliga/matches/2026-08-28-eintracht-braunschweig-vs-hertha-bsc/index.html`

## Which row went, and why that is the declared transient

The rendered-name set difference isolates the cause. Exactly one name is removed per locale and
**nothing is added**:

| locale | removed |
|---|---|
| EN | `% Shots from box` |
| DE | `% Schüsse aus dem Strafraum` |
| FI | `% Laukaukset boksista` |

All three are `danger_zone_ratio`'s label. The committed export sample still serves the OLD payload
key, so `MetricComparison.astro`'s `hasData()` omits the row — **omitted, never blank, never a
fabricated zero**, per `docs/wireframes/14_team_stats.md` §6. `Shooting` keeps its heading because
it still has 3 of its 4 rows, unlike `!116` where `saves_pct` was `Goalkeeping`'s only row.

⭐ The contract predicted **16 → 15 with no heading lost** before any code was written. That is
what the build produced.

Of batch C's three names only `danger_zone_ratio` is one of the LOCKED 16: `shot_accuracy` is a
payload field the 16-row contract in `metricRows.ts` deliberately drops, and `shot_share` is not in
the fixture payload at all. The transient closes with the final refresh after F, which must be a
ROLL-FORWARD (`!118` proved a past fixture can never be re-exported).

## Wording — nothing moved

Every metric name rendered on the built fixture pages was compared word for word against the
untouched CPO-validated corpus `site/i18n/<loc>.json`, for the names that corpus declares:
**EN 8 compared, DE 9, FI 9, wording differences NONE.** The single reported divergence is
pre-existing and already exempted by name in `check-metric-labels.test.mjs` (EN
`finishing_efficiency` renders `% Goals per shot on target` against the corpus's
`% Conversion rate`).

## The team page — absent state unchanged

`site_v2/dist/<loc>/teams/manchester-united-fc/index.html`, all three locales:

- EN — *"Not enough games this season to rank Manchester United FC against the league."*
- DE — *"Zu wenige Spiele in dieser Saison, um Manchester United FC mit der Liga zu vergleichen."*
- FI — *"Liian vähän otteluita tällä kaudella, jotta Manchester United FC voisi verrata sarjaan."*

That page's featured season has one game played, below the `>= 3 finished games` benchmark floor, so
the Performance tab renders its absent state on main exactly as it does here. Recorded so the gap is
never read as damage from this rename.

## Old names on the built site

`grep -rl` over `site_v2/dist/` for all three old names → **0 files** of 66 built pages plus every
asset.

## ⚠ Known, out of scope, and NOT made worse here

The seven metric GROUP HEADINGS render in English on the DE and FI pages
(`MetricComparison.astro:40`, `TeamPerformance.astro:89`/`:110`). Pre-existing, filed as GitLab
**#98**, and a §10 naming decision — the German and Finnish words are the CPO's. This MR changes no
component and no heading, so the instance count is unchanged.
