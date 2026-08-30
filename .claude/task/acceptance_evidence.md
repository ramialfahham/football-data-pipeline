# Acceptance evidence — step 4, MR 1 (rebuilt): the three player `shooting` metrics

Branch `refactor/metric-rename-player-shooting`, from main `1fa7e5f`.

    shots_total           →  shots_player
    shots_on_goal         →  shots_on_goal_player
    finishing_efficiency  →  finishing_efficiency_player_pct     (PLAYER entity only)

⚠ **THIS IS A REBUILD.** The first attempt failed review 4–1 and was reverted with nothing
committed. Every gate below was run unpiped with its exit code read bare.

⚠ **THE FOUR CRITERIA ARE NEW.** The B–F set expired with `!123`; its criterion 3 rested on the
`npm test` label guard, and that guard reaches **none** of the 35 player metrics — measured, not
assumed (`check-metric-labels.test.mjs:36-38`, `asked = rowKeys ∪ heroKeys` is 17 + 3 keys, every one
a team `metrics.*` key).

criteria_demonstrated:
  - **Criterion 1 — no rendered name changed its words.** The built pages are structurally identical to the base: **12 metric rows and 7 group headings per comparison block in EN, DE and FI** across 19 fixture pages, distinct-label sets equal element-for-element. ⚠ This confirms a stated prediction; it is NOT proof the rename happened — "no change" is also what doing nothing produces, the check the CPO rejected on `!114`.
  - **Criterion 2 — old names gone, and nothing half-renamed.** Whole-token `git grep` over `site_v2/src` excluding `src/data`: **0 files**. The new names are present — `shots_player` in **15** files, `shots_on_goal_player` in **21**, `finishing_efficiency_player_pct` in **15**.
  - **Criterion 3 — two guards passed AND each watched going RED.** `sync_metric_docs_blocks.py --check` (exit 0, 173 blocks) broken by reverting the seed's `shots_player` `metric_id` → **RED, exit 1** ("missing block: shots_total / block no longer in the seed: shots_player"). `check_description_hygiene.py` (exit 0) broken by reverting one re-pointed team reference in `int_legs.yml` → **RED, exit 1** ("int_legs__team_match.shots_total - unresolved docs block: 'shots_total'"). Both restored, both green.
  - ⭐ **Criterion 4 — every column reference resolves against the relation it reads.** The static resolver follows sources through CTE chains for **both dotted and bare** references: **31 references checked, 0 broken.** Watched going RED on a reproduction of the round-1 defect (`reads s.shots_player where s = fct_fixture_player_stats, which does not emit 'shots_player'`) and, in its extended form, on the round-2 defect (`bare read of 'shots_total' inside CTE 'aggregated' whose source is int_player_club_season__metrics, which does not emit it`). Both exit 1; restored, green.

## Why criterion 4 exists

Round 1 shipped five models that could not execute, and **nine offline gates went green on it** —
docs-block sync, description hygiene, layer contract, UI i18n, `dbt parse`, pytest, sqlfluff,
`npm test` and the site build. None of them resolves a column reference. Four human reviewers caught
it by reading SQL. Criterion 4 is the mechanical version of that read.

It is a floor, not a ceiling: it is static, it resolves 25 of 28 references, and `data:build:mr`
remains the authority. Stated as a limit rather than implied.

## ⛔ Round 2 failed 5–0 on this same defect, and the record is here rather than tidied away

Two defects, both real, both now closed. Four reviewers found the first independently; `bi-analyst`
found the second:

| where | what | why it escaped |
|---|---|---|
| `int_player_season__metrics.sql:45-46` | `sum(shots_total) as shots_player` — a BARE read of `club_season` = `int_player_club_season__metrics`, which renamed that column in this same branch | the bare rule asked whether the ALIAS matched the inner name, not whether the SOURCE had moved |
| `03_player_profile.md:126` | prose naming `shots_player` in a line documenting the matchstats payload, which comes from `mart_player_fixture_stats` — a provider surface that does not rename | the file was treated as wholly player-scoped |

⛔⛔ **AND IT IS ONE MISTAKE, NOT TWO.** For dotted reads I asked the right question — *does the
source relation rename this column?* For bare reads I asked a different one. Where the two diverge,
the rule fails. That single inconsistency produced both round-2 defects and, in a different shape,
round 1's. Corrected to one rule applied uniformly across alias / dotted / bare / prose / seed.

⚠ **My own resolver repeated the mistake in miniature**: built for dotted references only, it
reported "25 of 28 resolved, 0 broken" while a model sat broken on a bare read. It now follows
sources for both shapes — 31 checked, 0 broken — and catches both earlier rounds' defects.

## The five surfaces of one defect

The same mistake — *a reference to an upstream column is not the metric's own name* — appeared in
three places. Two were caught by this branch's own guards before review:

| surface | wrong | right |
|---|---|---|
| self-aliasing aggregate | `sum(p.shots_player) as shots_player` | `sum(p.shots_total) as shots_player` |
| dotted read of a renamed relation | `y.shots_on_goal_this_season` left as-is | follows its source |
| seed formula field | `numerator_expr = sum(shots_player)` | `sum(shots_total)` — the leg column |

The seed one is the sharpest: `base_relation` stayed `int_legs__player_match`, which emits
`shots_total`, so the catalogue's own formula would have named a column existing nowhere. The
correct sibling proves the rule — `shots_on_goal_player` keeps `sum(shots_on)` because its leg
column was never the same word as its metric_id. Seed occurrences are now decided **by CSV field**;
`base_relation` / `numerator_expr` / `denominator_expr` are references and never move. All three
formulas verified after the change:

    shots_player                     sum(shots_total)                        int_legs__player_match
    shots_on_goal_player             sum(shots_on)
    finishing_efficiency_player_pct  sum(goals_total - goals_penalty) / sum(shots_on)

## Decisions, printed

**14 dotted reads enumerated individually** — 12 read a metric relation that renamed the column and
follow it; **2 read a provider relation and do not** (`int_player_club_season__metrics` `s` =
`fct_fixture_player_stats`; `int_player_momentum__metrics` `p` = `int_legs__player_match`).
**13 alias writes** renamed. **4 bare upstream reads** protected inside their self-aliasing
aggregates; **30 own-column references** renamed. Provider surfaces excluded outright per the CPO's
ruling — measured, every occurrence in them is a dotted read.

⚠ My first shape rule protected ALL dotted reads, which would have left `mart_player_profile` and
`int_player_profile__yoy` reading columns their own upstream had just renamed. The yml-column guard
caught it — and that guard had itself to be fixed first, because it was comparing the new yml name
against the *pre*-rename SQL on disk instead of the post-transform state.

## Gates

| gate | exit | result |
|---|---|---|
| `sync_metric_docs_blocks.py --check` | 0 | 173 blocks match the seed and the model YAML |
| `check_description_hygiene.py` | 0 | **1604 descriptions**, 235 blocks resolved, zero dangling `doc()` |
| `check_layer_contract.py` | 0 | passed |
| `check_ui_i18n_metrics.py` | 0 | 13 shown metrics resolve in 3 locale files |
| `dbt parse` (1.7.19) | 0 | clean, zero error lines |
| static column-reference resolver | 0 | 25/28 resolved, 0 broken, 3 reported |
| `sqlfluff lint` — 9 changed models | 1 | **zero LT05**; see below |
| `pytest -q` (repo root) | 0 | **1009 passed, 1 skipped, 14 subtests** — identical to the `1fa7e5f` baseline |
| `npm test` (`site_v2/`) | 0 | 76/76 |
| `npm run build` | 0 | 66 pages, `audit-seo: 67 built page(s) checked. OK.` |

⭐ **1604 descriptions — exactly the base count.** That is the CPO's "re-point them" ruling measured:
blanking the 12 borrowed references would have left 1592. Docs blocks 238 → 235, the three orphans
predicted in advance (`opponent_shots_total__player`, `opponent_shots_on_goal__player`,
`shots_on_goal_sum_season__player`), each verified to have zero references before removal.

⛔ **THE LINT FAILURES ARE PROVED PRE-EXISTING FOR THIS DIFF, not carried over from the reverted
attempt.** Three files report `LT02`/`TMP`/`PRS` (the `dbt_utils`-under-jinja class `CLAUDE.md`
warns about) plus `ST11`. Re-linted **unmodified** — stashed by explicit path, linted, popped — and
the output is **byte-identical** (`diff` exit 0), with **zero LT05 in either**.

## #96 — the six `accepted_values` lists, checked by eye

The two 18-name PLAYER benchmark lists and the 14-name rate-board list carry `shots_on_goal` and
`finishing_efficiency` and moved together; the three 22-name TEAM lists are untouched. Fifth
consecutive batch to reproduce #96 — only `data:build:mr` can catch a wrong entry.
