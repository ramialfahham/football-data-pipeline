# Rendered page evidence — batch F, finishing_efficiency → finishing_efficiency_pct

Branch `refactor/metric-rename-team-finishing-efficiency`, base main `cdd2218`.

Read from `site_v2/dist/` after `npm run build` (66 pages built, `audit-seo: 67 built page(s)
checked. OK.`) — never from source, never from `outerHTML`. HTML comments are stripped and
whitespace collapsed before any comparison, because Astro splits interpolated text with `<!-- -->`.
Both the before and the after were built and measured; the before was taken on the untouched tree at
`cdd2218`, not reconstructed from batch E's numbers.

## The fixture metric comparison — 13 → 12, which is what the contract predicted

Counted STRUCTURALLY: one `<div class="mrow">` per row, one `<div class="mgroup">` per heading. Each
fixture page renders two comparison blocks (W1 and W2), so a 12-row page shows 24 `mrow` and 14
`mgroup`.

⛔ Not a substring test. `Ø Corners` occurs inside `Ø Corners against`, and a containment check
certifies a MISSING row as present — that is how `!116`'s evidence reported 16 rendered names when
the truth was 14. Every label below is a whole rendered element text.

| | before (`cdd2218`) | after |
|---|---|---|
| metric rows per comparison block — EN / DE / FI | 13 / 13 / 13 | **12 / 12 / 12** |
| group headings per block | 7 / 7 / 7 | **7 / 7 / 7** |
| rendered names ADDED | — | **none, in any locale** |
| rendered names REMOVED | — | **exactly one per locale** |

Across all **19** fixture pages in each locale, both windows: `[12]` (min 12, max 12).

The one removed name per locale, and it is this metric's own row:

| locale | removed |
|---|---|
| EN | `% Goals per shot on target` |
| DE | `% Trefferquote` |
| FI | `% Viimeistelytehokkuus` |

⭐ **Why it is absent rather than wrong.** `finishing_efficiency_pct` IS one of the LOCKED 16 in
`site_v2/src/lib/metricRows.ts`, and the committed export sample still serves the old
`finishing_efficiency` key, so `MetricComparison.astro`'s `hasData()` drops a row where neither side
has a value. Honest-absent behaviour — omitted, never blank, never a fabricated zero
(`14_team_stats.md` §6). It closes with the final sample roll-forward, which is owed after F and is
deliberately not in this branch.

⭐ **The Shooting heading survives**, which was the other half of the prediction: the group keeps
`Ø Shots` and `Ø Shots on target`. All seven headings render in all three locales, before and after.

Programme running total: 16 → 15 (C) → 13 (D) → 13 (E) → **12 (F)**.

Reference page, all three locales:
`site_v2/dist/<loc>/2-bundesliga/matches/2026-08-28-eintracht-braunschweig-vs-hertha-bsc/index.html`

## The wording of every surviving name is unchanged

Compared against the UNTOUCHED CPO-validated corpus `site/i18n/<loc>.json`, by exact equality of
whole strings:

| locale | corpus-declared names rendered, before | after | lost | gained |
|---|---|---|---|---|
| EN | 7 | 7 | none | none |
| DE | 8 | 7 | `% Trefferquote` | none |
| FI | 8 | 7 | `% Viimeistelytehokkuus` | none |

⚠ EN is 7 both times, and that is not an omission. v2's EN label for this metric diverges from the
MVP corpus by design — the corpus says "% Conversion rate" and v2 keeps its own locked wording — so
this row was never in the EN compared set. That divergence is the reason
`check-metric-labels.test.mjs` carries an EN exemption keyed on the metric id, and re-pointing that
exemption is part of this diff.

## The team page — criterion 4, unchanged

Read from the `<div class="cb">` element inside the `data-page="performance"` panel of
`site_v2/dist/<loc>/teams/manchester-united-fc/index.html`. Matched on the element, not by searching
for a phrase.

    EN  Not enough games this season to rank Manchester United FC against the league.
    DE  Zu wenige Spiele in dieser Saison, um Manchester United FC mit der Liga zu vergleichen.
    FI  Liian vähän otteluita tällä kaudella, jotta Manchester United FC voisi verrata sarjaan.

Byte-identical before and after. The metric ROWS render on no built team page in this sample: the
featured season (team 33, PL 2026) has one game played, below the `>= 3 finished games` benchmark
floor, so `season.benchmarks` is empty and the whole Performance tab renders the absent state. That
is pre-existing and is recorded here so the gap is never read as damage from this rename.

## ⚠ #98 is visible in this evidence and is NOT caused here

The seven group headings render in ENGLISH on the DE and FI pages — `Defending · Duels ·
Goalkeeping · Goals · Passing · Set pieces · Shooting` in all three locales. That is GitLab **#98**,
open and the CPO's (the words are his). It is identical before and after this branch.
