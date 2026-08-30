# Rendered page evidence — step 4 MR 2, the player `discipline` metrics

Branch `refactor/metric-rename-player-discipline`, base main `3e5b25b`.

Read from `site_v2/dist/` after `npm run build` (66 pages, 57 fixture pages, `audit-seo: 67 built
page(s) checked. OK.`) — never from source, never from `outerHTML`. HTML comments stripped and
whitespace collapsed before any comparison, because Astro splits interpolated text with `<!-- -->`.

**BOTH SIDES WERE BUILT.** The base side is not asserted from the base commit's numbers: the 24
changed files were stashed by explicit path, `npm run build` was run at base content, the dist
measured, then the stash popped and the tree confirmed back at 24 modified files. That second build
is not redundant even though `git diff --name-only HEAD -- site_v2/` is empty, because the build's
`prebuild` step (`npm test && node scripts/check-page-specs.mjs`) reads `dbt_project/models/5_marts/**`
and `dbt_project/seeds/`, which this branch DOES change.

## The prediction, and why it is a different one from `!125`'s

`!125` could say its three names never reached the payload at all. **Four of these five do.** The
committed fixture sample carries `offsides`, `penalty_committed`, `cards_yellow` and `cards_red`
under `top_players[]` — ten per fixture across 19 files — and that payload is built from
**`mart_player_momentum`** (`export_site_data.py:871`), a player METRIC mart this MR renames, not
from `mart_player_fixture_stats`. `shape_top_players` filters with a DROP list (`_TOPPLAYER_DROP`)
that names none of the five, so a renamed mart column flows straight through into a payload key.

The prediction was therefore: **the pages still do not change**, for two reasons that both had to
hold — `site_v2/src/data/**` is the declared transient and is not swept, and no `.astro`, `.ts` or
spec file reads any of the five.

Counted STRUCTURALLY: one `<div class="mrow">` per row, one `<div class="mgroup">` per heading, two
comparison blocks per fixture page.

| | base (`3e5b25b`) | after |
|---|---|---|
| metric rows per comparison block — EN / DE / FI | 12 / 12 / 12 | **12 / 12 / 12** |
| group headings per block | 7 / 7 / 7 | **7 / 7 / 7** |
| distinct rendered labels | 12 / 12 / 12 | **12 / 12 / 12** |
| names ADDED / REMOVED | — | **none / none** |

Across all **19** fixture pages in each locale, both windows. The distinct label set compares
**identical in all three locales**, element for element; 7 of the 12 rendered names in each locale
are also declared in the untouched CPO-validated `site/i18n/<loc>.json` corpus and every one of
those matches word for word.

## The sharper measurement: the payload keys are not in the HTML at all

Whole-token grep over the whole of `site_v2/dist`:

| name | built files containing it |
|---|---|
| `cards_yellow` | **0** |
| `cards_red` | **0** |
| `cards_total` | **0** |
| `offsides` | **0** |
| `penalty_committed` | **0** |

Astro renders server-side, so a payload key that no component reads never reaches the emitted HTML.
`01_fixture_page.md:196` describes these four as "available in the payload for an expanded row
(design decision)" and `03_player_profile.md:106` says they "stay unrendered" — the build confirms
both. **So the roll-forward changes the payload keys and still changes no built page.**

⛔⛔ **THIS IS NOT THE PROOF THE RENAME HAPPENED.** An unchanged build is exactly what doing no work
produces — the shape of check the CPO rejected on `!114` ("identical output is ALSO what doing no
work produces"). It is recorded as **the confirmation of a stated prediction**, a different claim.
What proves the work is criterion 2 (48 yml column entries reconciled against their own models'
SQL, in both directions) and criterion 4 (42 column references resolved, and the resolver watched
going red three times, once on an exact reproduction of the `!125` round-2 defect inside this
batch's own code).

## Row count in context

12 is where `!123` left it — 16 catalogue rows minus the four dropped by batches C, D and F. The
sample roll-forward is what takes it back to 16, and it is owed and unscheduled: it needs ingestion
to have run, and there is still no nightly schedule on GitLab. Nothing in this MR moves that number
in either direction.
