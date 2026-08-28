# Rendered page evidence — batch E, the deserved chain

Branch `refactor/metric-rename-team-deserved-chain`, base main `db47b0a`.

Read from `site_v2/dist/` after `npm run build` (66 pages built, `audit-seo: 67 built page(s)
checked. OK.`) — never from source, never from `outerHTML`. HTML comments stripped before collapsing
text, because Astro splits interpolated text with `<!-- -->`.

## The fixture metric comparison — unchanged, and that is the point

Counted structurally (`<div class="mrow">` per row, `<div class="mgroup">` per heading, inside each
`<div class="cmp">`).

| | before (`db47b0a`) | after |
|---|---|---|
| metric rows per comparison block — EN / DE / FI | 13 / 13 / 13 | **13 / 13 / 13** |
| group headings | 7 | **7** |
| rendered names removed | — | **none** |
| rendered names added | — | **none** |

Across all **19** fixture pages in each locale, both windows: `[13]` (min 13, max 13).

⭐ The contract predicted **13 → 13, unchanged**, before any code — because neither renamed metric
is among the LOCKED 16 in `site_v2/src/lib/metricRows.ts` (0 hits, verified). E is the first batch
of the programme where the declared transient does not grow. The rendered-name set difference is
**empty in every locale**, which is a stronger statement than a matching count: nothing appeared,
nothing vanished, nothing was re-worded.

Running total across the programme: 16 → 15 (C) → 13 (D) → **13 (E)**. F takes it to 12.

Reference page, all three locales:
`site_v2/dist/<loc>/2-bundesliga/matches/2026-08-28-eintracht-braunschweig-vs-hertha-bsc/index.html`

## The deserved-vs-actual hero — the surface these two metrics actually drive

`DeservedHero.astro` is the one component that reads this chain, via the export payload key `sotd`.
That key is **deliberately unchanged** (it is also an i18n placeholder inside translated sentences
in all three locales), so the component's binding is untouched and its rendered output cannot move.

⚠ The hero renders on NO built page in this sample, and that is pre-existing, not caused here: the
featured season (team 33, PL 2026) has one game played, below the `>= 3 finished games` benchmark
floor, so the team Performance tab renders its absent state instead. The same reason criterion 4
reads an absent state rather than a metric row.

## Wording — nothing moved

Every metric name rendered on the built fixture pages compared word for word against the untouched
corpus `site/i18n/<loc>.json`, for the names it declares: **EN 7, DE 8, FI 8, differences NONE.**

## The team page — absent state unchanged

`site_v2/dist/<loc>/teams/manchester-united-fc/index.html`:

- EN — *"Not enough games this season to rank Manchester United FC against the league."*
- DE — *"Zu wenige Spiele in dieser Saison, um Manchester United FC mit der Liga zu vergleichen."*
- FI — *"Liian vähän otteluita tällä kaudella, jotta Manchester United FC voisi verrata sarjaan."*

## Old names on the built site

`grep -rl` over `site_v2/dist/` for `sot_difference_per_match` and `sot_points_gap` → **0 files**
of 66 built pages plus every asset.

## ⚠ A wording target for STEP 5, found here and deliberately not touched

The EN hero sentences at `site_v2/src/i18n/strings.ts:94-95` read "shots-on-target difference".
Step 5 renames nine CATALOGUE `label_en` rows from "on target" to "on goal"; these are UI SENTENCE
strings, not catalogue labels, so the nine-row list may not cover them. Wording is §10 — flagged for
step 5 rather than fixed in a rename MR.

## ⚠ Known, out of scope, not made worse

GitLab **#98** — the seven metric group headings render in English on DE/FI. Pre-existing, §10, and
this MR touches no component and no heading.
