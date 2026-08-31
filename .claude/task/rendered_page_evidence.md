# Rendered page evidence — step 4 MR 7, the player `goals` metrics

Branch `refactor/metric-rename-player-goals`, base main `6f0ee07`.

Read from `site_v2/dist/` after `npm run build` (66 pages, 57 fixture pages, `audit-seo: 67 built
page(s) checked. OK.`) — never from source, never from `outerHTML`. Comments stripped and whitespace
collapsed before any comparison.

| | base (`6f0ee07`) | after |
|---|---|---|
| metric rows per comparison block — EN / DE / FI | 12 / 12 / 12 | **12 / 12 / 12** |
| group headings per block | 7 / 7 / 7 | **7 / 7 / 7** |
| names ADDED / REMOVED | — | **none / none** |

Across all **19** fixture pages in each locale, both windows — measured as 24 `mlabel` and 14
`mgroup` per page, which is the two windows' 12 and 7.

## ⭐ NO frontend file changes — and that is the measured result, not an assumption

`git diff --name-only -- site_v2/` is **empty**. Thirteen `site_v2/src` files carry a swept token and
**every one protects**. Because the committed sample JSON under `site_v2/src/data/` is also untouched,
the built output cannot differ from base by construction; the base-side build was additionally run
explicitly, from a tree stashed by explicit path, earlier in this MR.

  - `PlayerRow.astro:39` reads `player.goals_total` / `player.goals_assists` — **PROVIDER leg
    columns**, not the metric ids — beside `t(lang, "goals")`, a UI word. All three stay. ⚠ This is
    the exact opposite of `!131`, where the same file read renaming payload fields and had to move;
    the claim is re-derived here rather than carried in either direction.
  - `TeamSquad.astro` and `lib/types.ts` stay because of the CPO's payload ruling: the squad block
    keeps the keys `goals` / `assists` while the export's read of them follows the mart.
  - `HeadToHead`, `RecentMatch`, `TeamFixtureRow`, `Masthead`, `YearOverYear` carry the team
    scoreline (`goals_for`/`goals_against`, `standing_goals_diff`, the yoy pair) — the family that
    FAILed `!131` round 1 and is guarded by name here.
  - `i18n/strings.ts`, `lib/metricRows.ts` and both page specs carry TEAM label keys and UI words.

The twelve rendered labels are all TEAM metrics, in every locale: Goals, Goals against, Clean sheets,
Shots, Shots on target, Corners, Corners against, Duels, Duels won %, Save percentage, Passes,
Defensive actions. ⚠ "Shots on **target**" is still the EN wording — **step 5 has not run**, which
this measurement independently confirms.

## ⛔ What the payload ruling means for the Squad tab

The CPO ruled this session: *"Naming conventions in the warehouse are one thing. What we show on the
website is another."* So the chain is deliberately asymmetric:

    mart_player_career.goals_player   →   export: "goals": career.get("goals_player")
                                      →   payload { "goals": 26 }
                                      →   TeamSquad.astro: m.goals        (unchanged)

The rendered line still reads **"26 goals · 8 assists"** — from the i18n dictionary, which no batch
of this programme has ever touched.

⚠ **And this is the one place the asymmetry earned its keep**: because the ruling holds the payload
side still, the export's code and its test could no longer move in lockstep, and **pytest caught a
real rule inversion** in `tests/test_export_site_data.py` (three failures). `!131` recorded that an
automated rename editing both sides together leaves the suite unable to disagree; here it disagreed.

## Criterion 1 is a CONFIRMATION, stated before the work as such

No renamed name reaches a built page: the twelve rendered rows are all TEAM metrics, and the player
metrics this batch renames appear in the payload, not in the comparison block. The dist comparison
therefore proves the twelve rendered rows are untouched by a batch that changed 342 occurrences — it
does **not** discriminate a mis-scope in the player chain. What guards that chain is named in
`acceptance_evidence.md`: the seed check, the hygiene gate's dangling-reference test, the
yml-vs-projection check, and — for the export — the test suite.

⚠ It also does not discriminate a DOCUMENTATION mis-scope, which is what round 1 FAILed on: none of
the prose the sweep corrupted renders on any page. Only the blinded review found that.

## Row count in context

12 is where `!123` left it — 16 catalogue rows minus the four dropped by batches C, D and F. The
sample roll-forward is what takes it back, and it is owed and unscheduled. Nothing in this MR moves
that number.
