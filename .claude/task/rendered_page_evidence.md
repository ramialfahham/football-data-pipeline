# Rendered page evidence — step 4 MR 5, the player `duels` metrics

Branch `refactor/metric-rename-player-duels`, base main `9ea88b5`.

Read from `site_v2/dist/` after `npm run build` (66 pages, 57 fixture pages, `audit-seo: 67 built
page(s) checked. OK.`) — never from source, never from `outerHTML`. HTML comments stripped and
whitespace collapsed before any comparison, because Astro splits interpolated text with `<!-- -->`.

**BOTH SIDES WERE BUILT.** The 33 changed files were stashed by explicit path under a `TEMP-`
label, `npm run build` run at base content (tree confirmed at 0 modified), the dist measured, the
stash popped and the tree confirmed back at 33 modified.

| | base (`9ea88b5`) | after |
|---|---|---|
| metric rows per comparison block — EN / DE / FI | 12 / 12 / 12 | **12 / 12 / 12** |
| group headings per block | 7 / 7 / 7 | **7 / 7 / 7** |
| distinct rendered labels | 12 / 12 / 12 | **12 / 12 / 12** |
| names ADDED / REMOVED | — | **none / none** |

Across all **19** fixture pages in each locale, both windows. The branch measurement was taken
twice, from two separate builds, and reproduces byte-identically.

Whole-token grep over the whole of `site_v2/dist` finds all four old stems in **0** files — and all
four new names in **0** files as well. Nothing in this batch reaches the frontend in either
direction.

## ⛔⛔ I CLAIMED THIS COMPARISON DISCRIMINATED. I MEASURED IT. IT DOES NOT.

The contract's first draft said: `"% Duels won"` and `"Ø Duels"` are among the 12 rendered rows, so
mis-scoping the TEAM `duels_won_pct` would delete a visible label and this comparison would catch
it. That was reasoning, not evidence, so it was tested — `duels_won_pct` → `duels_won_player_pct`
applied to `metricRows.ts` and `strings.ts` exactly as a mis-scope would, then `npm run build`:

**The build never completes.** `prebuild` is `npm test && node scripts/check-page-specs.mjs`, and
both fail before Astro renders anything. There is no dist to compare, so the comparison cannot be
what catches it. ⚠ On the first attempt this nearly went unnoticed: the failed build left the
PREVIOUS dist in place, and measuring it printed a perfectly healthy `"% Duels won"`. A stale
artifact reported as a fresh measurement is the same shape as reading `tail`'s exit code instead of
the gate's.

So this table is the same evidence class as `!125`, `!127` and `!129`: it confirms the delivered
tree is correct. **It is not a discriminating check**, and `!128` remains the only batch of step 4
where the dist comparison would itself have caught a mis-scope.

## ⭐ What actually discriminates — measured under the same mis-scope

**1. `npm test`, 75 pass / 1 fail:**

    ✖ every labelKey is a label_i18n_key the catalogue actually declares
      AssertionError: label keys the catalogue does not declare in label_i18n_key:
      metrics.duels_won_player_pct.label. Read the column; never infer the key from
      the metric_id or the payload field.

⭐ **This is a stronger guard than the one `!129` named.** That MR pointed at
`check-metric-labels.test.mjs`'s `metricRows.ts` ↔ `strings.ts` binding, which a consistent
two-sided rename would satisfy. The assertion that actually fires binds `metricRows.ts` to the
**SEED's `label_i18n_key` column** — and the team row keeps `metrics.duels_won_pct.label`, so no
edit of the two frontend files alone can satisfy it. On the delivered tree: **76/76**.

**2. `check-page-specs.mjs`, exit 1**, read UNPIPED (`> file 2>&1` then `$?`, not through `tail`):

    - specs/teams/team.spec.json: blocks[4] … i18n key "metrics.duels_won_pct.label"
      does not exist in the EN dict
    - specs/competition/matches/fixture.spec.json: blocks[1] … same

Two independent bindings, both in `prebuild`, both pointing at the seed and the specs rather than at
the two files a mis-scope would touch.

## The frontend does not change at all this batch

`git diff --name-only -- site_v2/` is **empty**, and that is re-derived here rather than inherited:
`!129` was the first frontend source change of step 4 and said so loudly, so the opposite claim had
to be measured, not assumed — carrying a previous batch's claim forward is what cost `!128` two
rounds. All four swept frontend files were checked individually and still carry the TEAM keys
(`strings.ts` 3, `metricRows.ts` 1, both page specs 1 each), and no new name appears anywhere under
`site_v2/src/` outside the committed sample.

## Row count in context

12 is where `!123` left it — 16 catalogue rows minus the four dropped by batches C, D and F. The
sample roll-forward is what takes it back, and it is owed and unscheduled. Nothing in this MR moves
that number in either direction.
