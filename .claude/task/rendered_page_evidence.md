# Rendered page evidence — step 4 MR 1 (rebuilt), the player `shooting` metrics

Branch `refactor/metric-rename-player-shooting`, base main `1fa7e5f`.

Read from `site_v2/dist/` after `npm run build` (66 pages, `audit-seo: 67 built page(s) checked.
OK.`) — never from source, never from `outerHTML`. HTML comments stripped and whitespace collapsed
before any comparison, because Astro splits interpolated text with `<!-- -->`.

## The prediction: nothing moves

Stated in the contract before any code. None of the three names is among the 16 locked rows in
`site_v2/src/lib/metricRows.ts`, and the player surface they feed — the fixture `top_players`
block — carries `shots_on`, the LEG column, which does not move.

Counted STRUCTURALLY: one `<div class="mrow">` per row, one `<div class="mgroup">` per heading, two
comparison blocks per fixture page.

| | base (`1fa7e5f`) | after |
|---|---|---|
| metric rows per comparison block — EN / DE / FI | 12 / 12 / 12 | **12 / 12 / 12** |
| group headings per block | 7 / 7 / 7 | **7 / 7 / 7** |
| distinct rendered labels | 12 / 12 / 12 | **12 / 12 / 12** |
| names ADDED / REMOVED | — | **none / none** |

Across all **19** fixture pages in each locale, both windows: `[12]`, min 12 max 12. The distinct
label set compares **identical in all three locales**, element for element.

⛔⛔ **THIS IS NOT THE PROOF THE RENAME HAPPENED.** An unchanged build is exactly what doing no work
produces — the shape of check the CPO rejected on `!114` ("identical output is ALSO what doing no
work produces"). It is recorded as **the confirmation of a stated prediction**, a different claim.
The evidence the work happened is criterion 2 (0 old-name files in `src` outside the sample, new
names in 15 / 21 / 15 files), the four gates, and the guards watched going red — including the
column-reference resolver reproducing the exact defect that failed round 1.

## Why the player surface cannot show a change

`shape_top_players` (`scripts/export_site_data.py:566`) is a passthrough: `_drop(row,
_TOPPLAYER_DROP)` removes eight internal keys and emits the rest verbatim, so the payload keys are
the mart's column names. Read from the committed sample, a `top_players` member carries `shots_on`,
`goals_total`, `goals_assists`, `saves`, `save_pct`, the duels/dribbles/passes/tackles counts and the
cards — **none of the three names this MR renames.** `shots_on` is the leg column and is not a
catalogue `metric_id`.

The team Squad tab reads `goals`/`assists`, which belong to MR 7. The first batch whose rename
reaches a rendered player value will be `duels` (MR 5) or `goalkeeping` (MR 6); the transient will be
declared there.

## The team page — unchanged, absent for the same pre-existing reason

`site_v2/dist/<loc>/teams/manchester-united-fc/index.html`, `<div class="cb">` inside the
`data-page="performance"` panel, identical to the base build:

    EN  Not enough games this season to rank Manchester United FC against the league.
    DE  Zu wenige Spiele in dieser Saison, um Manchester United FC mit der Liga zu vergleichen.
    FI  Liian vähän otteluita tällä kaudella, jotta Manchester United FC voisi verrata sarjaan.

Team 33's featured season (PL 2026) has one game played, below the `>= 3 finished games` benchmark
floor. Pre-existing; recorded so the gap is never read as damage from this rename.

## ⚠ #98 is visible here and is NOT caused by this MR

The seven group headings render in ENGLISH on the DE and FI pages. GitLab **#98**, open and the
CPO's. Identical before and after.
