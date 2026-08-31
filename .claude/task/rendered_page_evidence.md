# Rendered page evidence — step 4 MR 4, the player `passing` metrics

Branch `refactor/metric-rename-player-passing`, base main `1cf0d40`.

Read from `site_v2/dist/` after `npm run build` (66 pages, 57 fixture pages, `audit-seo: 67 built
page(s) checked. OK.`) — never from source, never from `outerHTML`. HTML comments stripped and
whitespace collapsed before any comparison, because Astro splits interpolated text with `<!-- -->`.

**BOTH SIDES WERE BUILT.** The 33 changed files were stashed by explicit path, `npm run build` run
at base content, the dist measured, the stash popped and the tree confirmed back at 33 modified.

| | base (`1cf0d40`) | after |
|---|---|---|
| metric rows per comparison block — EN / DE / FI | 12 / 12 / 12 | **12 / 12 / 12** |
| group headings per block | 7 / 7 / 7 | **7 / 7 / 7** |
| distinct rendered labels | 12 / 12 / 12 | **12 / 12 / 12** |
| names ADDED / REMOVED | — | **none / none** |

Across all **19** fixture pages in each locale, both windows. Whole-token grep over the whole of
`site_v2/dist` finds all five old names in **0** built files.

## ⛔⛔ This measurement CONFIRMS A PREDICTION here — it does not discriminate

`!128` was the exception in this programme: there `defensive_actions_per_match` genuinely rendered,
so a mis-scope would have deleted a visible label and the comparison would have caught it. **I
carried that framing into this batch and it is wrong.** Measured:

  - `site_v2/src/lib/metricRows.ts` declares **16** rows; **12** render. ⚠ An earlier draft said 17,
    counting `field:` string occurrences and so double-counting the nested `team:` override on the
    `clean_sheets` row. Corrected after `bi-analyst-reviewer` and `platform-reviewer` each
    re-derived it independently; the conclusion below is unchanged.
  - The twelve rendered EN labels are `% Duels won · % Save percentage · Clean sheets · Ø Corners ·
    Ø Corners against · Ø Defensive actions… · Ø Duels · Ø Goals · Ø Goals against · Ø Passes ·
    Ø Shots · Ø Shots on target`.
  - **"Ø Key passes" is not among them.** `passes_key_per_match` is one of the rows the committed
    sample cannot feed, and whole-token grep finds its label on **zero** built pages.

So an unchanged build here is the same weak evidence it was on `!125` and `!127` — it is exactly
what doing no work also produces, the shape the CPO rejected on `!114`.

## ⭐ What actually guards the protected team row

`site_v2/scripts/check-metric-labels.test.mjs` extracts every `labelKey` from `metricRows.ts` and
asserts, **in both directions and in all three locales**, that each is defined in `strings.ts` and
that no defined label goes unasked. Rename one side of `metrics.passes_key_per_match.label` without
the other and `npm test` goes red. It passed 76/76.

⚠ `!125` measured that this guard's covered set is entirely TEAM `metrics.*` keys and reaches none
of the 35 player metrics — which is precisely why it is load-bearing **here**, where the thing at
risk is a team row rather than a renamed player metric.

## ⭐ The frontend changes for the first time in step 4

`site_v2/src/lib/types.ts` is the **only** file under `site_v2/` that changes, and it changes one
token: `passes_key?: number | null` → `passes_key_player?: number | null` on the `TopPlayer`
interface. `top_players[]` is built from `mart_player_momentum` (`export_site_data.py:871`), which
renames that column, so the type would otherwise declare a field the payload stops carrying. Its
neighbours in that interface (`goals_total`, `goals_assists`, `saves`, `shots_on`) are leg names
that pass through unrenamed.

**No component reads it**, so the built pages still do not change — but MRs 1–3 each asserted an
empty `site_v2/` diff, and repeating that here would have been the same inherited-claim defect that
cost `!128` two review rounds.

The other four swept frontend files — `i18n/strings.ts`, `lib/metricRows.ts` and both page specs —
are byte-identical and still carry `passes_key_per_match`, verified individually rather than by the
empty diff alone.

## Row count in context

12 is where `!123` left it — 16 catalogue rows minus the four dropped by batches C, D and F. The
sample roll-forward is what takes it back, and it is owed and unscheduled. Nothing in this MR moves
that number in either direction.
