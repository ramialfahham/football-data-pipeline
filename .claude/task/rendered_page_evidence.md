# Rendered page evidence — batch D, the two `passing` metrics

Branch `refactor/metric-rename-team-passing`, base main `62d3b18`.

Read from `site_v2/dist/` after `npm run build` (66 pages built, `audit-seo: 67 built page(s)
checked. OK.`) — never from source, never from `outerHTML`. HTML comments are stripped before
collapsing text, because Astro splits interpolated text with `<!-- -->`.

## The fixture metric comparison

Counted STRUCTURALLY (`<div class="mrow">` per row, `<div class="mgroup">` per heading, inside each
`<div class="cmp">`), not by matching label text.

| | before (`62d3b18`) | after |
|---|---|---|
| metric rows per comparison block — EN / DE / FI | 15 / 15 / 15 | **13 / 13 / 13** |
| group headings | 7 | **7 — none lost** |
| blocks with no `Goalkeeping` heading | 0 | **0** |

Across all **19** fixture pages in each locale, both windows: w1 `[13]`, w2 `[13]` (min 13, max 13).

Reference page, all three locales:
`site_v2/dist/<loc>/2-bundesliga/matches/2026-08-28-eintracht-braunschweig-vs-hertha-bsc/index.html`

## Which rows went

Exactly two names removed per locale, **nothing added**:

| locale | removed |
|---|---|
| EN | `% Pass accuracy` · `Ø Key passes` |
| DE | `% Angekommene Pässe` · `Ø Schlüsselpässe` |
| FI | `% Syöttötarkkuus` · `Ø Avainsyötöt` |

Both are `Passing` rows whose payload keys this MR renamed. The committed export sample still serves
the OLD keys, so `MetricComparison.astro`'s `hasData()` omits them — **omitted, never blank, never a
fabricated zero**, per `docs/wireframes/14_team_stats.md` §6. `Passing` keeps its heading: it had 3
rows and loses 2, leaving `passes_per_match`.

⭐ The contract predicted **15 → 13 with no heading lost** before any code was written. That is what
the build produced.

The transient closes with the final refresh after F, which must be a ROLL-FORWARD — `!118` proved a
past fixture can never be re-exported, because `mart_team_momentum` and `mart_team_season_record`
are keyed on `upcoming_fixture_sk` and hold pre-match form only.

⚠ **The gap is now 3 rows below the locked 16 and will grow again on F.** 16 → 15 (C) → 13 (D). E
renames nothing that the fixture payload carries, so E holds at 13; F takes it to 12. Nothing is
broken by that — the rows are honestly absent — but it is worth seeing as a trend rather than as
four separate one-offs.

## Wording — nothing moved

Every metric name rendered on the built fixture pages was compared word for word against the
untouched CPO-validated corpus `site/i18n/<loc>.json`, for the names that corpus declares:
**EN 7 compared, DE 8, FI 8, wording differences NONE.**

## The team page — absent state unchanged

`site_v2/dist/<loc>/teams/manchester-united-fc/index.html`:

- EN — *"Not enough games this season to rank Manchester United FC against the league."*
- DE — *"Zu wenige Spiele in dieser Saison, um Manchester United FC mit der Liga zu vergleichen."*
- FI — *"Liian vähän otteluita tällä kaudella, jotta Manchester United FC voisi verrata sarjaan."*

One game played, below the `>= 3 finished games` benchmark floor — unchanged by this rename, and
recorded so the gap is never read as damage from it.

## Old names on the built site

`grep -rl` over `site_v2/dist/` for `pass_accuracy` and `key_passes_per_match` → **0 files** of 66
built pages plus every asset.

## ⚠ Known, out of scope, and NOT made worse here

The seven metric GROUP HEADINGS render in English on the DE and FI pages
(`MetricComparison.astro:40`, `TeamPerformance.astro:89`/`:110`). Pre-existing, filed as GitLab
**#98**, a §10 naming decision. This MR changes no component and no heading.
