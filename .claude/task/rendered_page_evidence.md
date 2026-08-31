# Rendered page evidence — step 4 MR 6, the player `goalkeeping` metrics

Branch `refactor/metric-rename-player-goalkeeping`, base main `9ee88a4`.

Read from `site_v2/dist/` after `npm run build` (66 pages, 57 fixture pages, `audit-seo: 67 built
page(s) checked. OK.`) — never from source, never from `outerHTML`. HTML comments stripped and
whitespace collapsed before any comparison.

**BOTH SIDES WERE BUILT.** The changed files were stashed by explicit path under a `TEMP-` label,
`npm run build` run at base content (tree confirmed at 0 modified), the dist measured, the stash
popped and the tree confirmed back at the full changed count (42 after the round-1 fixes).

| | base (`9ee88a4`) | after |
|---|---|---|
| metric rows per comparison block — EN / DE / FI | 12 / 12 / 12 | **12 / 12 / 12** |
| group headings per block | 7 / 7 / 7 | **7 / 7 / 7** |
| distinct rendered labels | 12 / 12 / 12 | **12 / 12 / 12** |
| names ADDED / REMOVED | — | **none / none** |

Across all **19** fixture pages in each locale, both windows. The two protected team labels this
batch puts at risk — **`"% Save percentage"`** (`saves_pct`) and **`"Ø Goals against"`**
(`goals_against_per_match`) — are among the seven names also declared in the CPO-validated
`site/i18n/*.json` corpus, and were compared word for word against it: identical in all three
locales. Whole-token grep over `dist` finds `save_pct` and `shots_on_goal_against` in **0** files.

## ⛔⛔ THE ONE PART OF THIS MR THAT NO GATE COVERS

This is the first batch of step 4 to change a **rendering component**, and the chain it sits in is
guarded by nothing. Each link was checked, not assumed:

    mart_player_momentum.sql:47,68   emits saves_player and saves_player_pct
    shared.yml:266,301               declares them
    export_site_data.py:66           _TOPPLAYER_DROP does NOT drop them — it is a DROP-list, so the
                                     renamed column reaches the payload with NO export edit
    types.ts:50-51                   TopPlayer.saves_player / saves_player_pct
    PlayerRow.astro:37               reads player.saves_player / player.saves_player_pct

  - **No typecheck exists.** `site_v2/package.json`: `build` is bare `astro build`; `prebuild` is
    `npm test && node scripts/check-page-specs.mjs`. A stale `player.saves` against a renamed
    `TopPlayer` compiles silently.
  - **No test references `PlayerRow`, `TopPlayer` or `top_players`** — grepped across `site_v2/**`.
  - **The GK line renders on 0 of 67 built pages.** Measured directly over `dist` for
    `</b> (saves|Paraden|torjuntaa) ·`. Ranking is goals → assists → key passes, so no goalkeeper
    reaches `top_player_rank <= 5` in the committed sample.

**A mis-scope here would ship a goalkeeper line reading `0` and a blank percentage, with every gate
green and the dist comparison unchanged.** The chain is verified by reading it end to end. That is
stated as what it is — a manual verification of an unguarded path — not dressed up as a passing check.

## ⭐ The same line carries a renaming and a protected token

    <b>{player.saves_player ?? 0}</b> {t(lang, "saves")} · <b>{percent(player.saves_player_pct, lang)}</b>

`player.saves` / `player.save_pct` moved; **`t(lang, "saves")` did not** — it is a UI word key
defined in `strings.ts` as `saves: "saves"` / `"Paraden"` / `"torjuntaa"`, not a metric. Nothing in
this programme had put both on one line before, so the classifier decides it by ROLE — the
characters immediately preceding the token — and prints a separate reason for each.

## Criterion 1 is a CONFIRMATION, and this contract said so before the work

`!130` had to correct this claim mid-flight after measuring it. Here it was declared up front: with
the GK line rendering on zero pages, the dist comparison **cannot** catch a `PlayerRow.astro`
mistake. What it does prove is that the twelve rendered rows — including the two protected team
labels above — are untouched by a batch that renamed 217 tokens.

## Frontend containment, re-derived

Exactly **two** `site_v2/` files change (`PlayerRow.astro`, `lib/types.ts`), **6 changed lines, 4
tokens**. The other **ten** swept frontend files were each checked individually and are
byte-identical: `i18n/strings.ts`, `lib/metricRows.ts`, both page specs, and six components
(`HeadToHead`, `RecentMatch`, `DeservedHero`, `MetricSeasonRow`, `TeamFixtureRow`, `YearOverYear`).
`lib/types.ts` moves 2 of its 11 occurrences — only `TopPlayer`'s; `FormMatch`, `RecentMeeting`,
`HeadToHead`, `TeamFixture` and `TeamSeason` keep theirs.

## ⛔ Round 1 broke a SECOND rendering binding, and this file's first draft missed it

`bi-analyst-reviewer` found it. `export_site_data.py:166` renamed the TEAM scoreline field inside
`_TEAM_FIXTURE_FIELDS`, so the export would have stopped emitting `goals_against` while
`components/team/TeamFixtureRow.astro:23` still read `fx.goals_against` to render every team's
fixture score line — `${goals_for}–${goals_against}` — on the team profile.

⚠ **The dist comparison could not see it.** The build reads the frozen sample under
`site_v2/src/data/**`, which this MR correctly leaves untouched, so the built pages kept showing the
right values and the 12/12/12 table below was unchanged. The defect was **latent**: it would have
surfaced the first time the export actually ran.

⭐ So there are **two** unguarded rendering chains in this batch, not one. The first draft of this
file disclosed only the GK line, and asserted the dist comparison's limits for that chain alone.
Both chains are now fixed and disclosed, and the general lesson is the same for both: **a comparison
built from a frozen sample cannot see a change to the code that produces the sample.**

## Row count in context

12 is where `!123` left it — 16 catalogue rows minus the four dropped by batches C, D and F. The
sample roll-forward is what takes it back, and it is owed and unscheduled. Nothing in this MR moves
that number.
