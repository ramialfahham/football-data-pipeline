# Rendered page evidence — step 4 MR 3, the player `defending` metrics

Branch `refactor/metric-rename-player-defending`, base main `a3fb952`.

Read from `site_v2/dist/` after `npm run build` (66 pages, 57 fixture pages, `audit-seo: 67 built
page(s) checked. OK.`) — never from source, never from `outerHTML`. HTML comments stripped and
whitespace collapsed before any comparison, because Astro splits interpolated text with `<!-- -->`.

**BOTH SIDES WERE BUILT.** The 28 changed files were stashed by explicit path, `npm run build` run
at base content, the dist measured, the stash popped and the tree confirmed back at 28 modified.

## ⭐ Why this measurement is a REAL check here, and was not on `!125` or `!127`

On the two previous batches an unchanged build only *confirmed a prediction* — none of those names
was rendered, so nothing could have moved. **This batch is different.**
`defensive_actions_per_match` is one of the **12 rendered metric rows**, and its stem
`defensive_actions` is the player metric being renamed. It appears in five frontend files, all
PROTECTED tokens:

    site_v2/src/lib/metricRows.ts:98              field: "defensive_actions_per_match"
    site_v2/src/i18n/strings.ts:630 / 669 / 708   the EN / DE / FI labels
    site_v2/src/components/team/TeamPerformance.astro:61
    site_v2/src/specs/competition/matches/fixture.spec.json:46
    site_v2/src/specs/teams/team.spec.json:75

**Mis-scope any one of them and a rendered label disappears from every built page.** So a clean
comparison is evidence that the team/player split held, not merely that nothing was expected to
change.

Counted STRUCTURALLY: one `<div class="mrow">` per row, one `<div class="mgroup">` per heading, two
comparison blocks per fixture page.

| | base (`a3fb952`) | after |
|---|---|---|
| metric rows per comparison block — EN / DE / FI | 12 / 12 / 12 | **12 / 12 / 12** |
| group headings per block | 7 / 7 / 7 | **7 / 7 / 7** |
| distinct rendered labels | 12 / 12 / 12 | **12 / 12 / 12** |
| names ADDED / REMOVED | — | **none / none** |

Across all **19** fixture pages in each locale, both windows. 7 of the 12 rendered names in each
locale are also declared in the untouched CPO-validated `site/i18n/<loc>.json` corpus and every one
matches word for word.

**The protected row itself, present after the rename** — the specific thing that would have broken:

    EN  "Ø Defensive actionstackles + interceptions + blocks"   19 built pages
    DE  "Ø Defensivaktionentackles + interceptions + blocks"    19 built pages
    FI  "Ø Puolustustoimettackles + interceptions + blocks"     19 built pages

(The run-together label is the row plus its `T · I · B` subtitle with tags stripped; it reads that
way on the base build too, so it is not a defect introduced here.)

## Not one frontend file changed

`git diff --name-only -- site_v2/` is **empty**. Five frontend files were deliberately swept rather
than skipped, so the classifier printed a decision for each; all five decisions were PROTECT and
none was written. Whole-token grep over `site_v2/dist` finds all five old names in **0** built
files — Astro renders server-side, so a payload key no component reads never reaches the HTML.

⛔⛔ **THIS IS STILL NOT THE PROOF THE RENAME HAPPENED.** An unchanged build is also what doing
nothing produces — the check the CPO rejected on `!114`. What it proves *here* is narrower and
worth stating exactly: **the protected team row survived a batch that renamed its stem.** What
proves the work is criterion 2 (72 yml column entries reconciled against their own models, the
frontend diff empty, the surviving old names pinned by count per file) and criterion 4 (48
references resolved, the resolver repaired and re-proved red on the `!125` round-2 defect).

## Row count in context

12 is where `!123` left it — 16 catalogue rows minus the four dropped by batches C, D and F. The
sample roll-forward is what takes it back to 16, and it is owed and unscheduled. Nothing in this MR
moves that number in either direction.
