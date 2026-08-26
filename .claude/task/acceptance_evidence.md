# Acceptance evidence — the missing team totals in the metric catalogue

Every figure measured on this branch against merged main `21c1ce0`. Where a measurement
contradicted an expectation, the contradiction is what is recorded.

⚠ **EVERY FIGURE HERE IS THE FIVE-ROW ONE.** This started at nine rows and two CPO rulings took
four away. The earlier version of this file was written for nine; none of its numbers survive
here — each was re-derived after the rebuild rather than edited down.

## The headline

| | |
|---|---|
| catalogue rows | **80 → 85** (5 team totals) |
| generated docs blocks | **161 → 181** |
| `{{ doc() }}` references repointed | **20** — the `goals_against` split, 12 team / 8 player |
| blank columns wired to a new block | **30** |
| dangling references after the change | **0** |
| team columns whose BigQuery description was WRONG and is now right | **12** |
| files | 14 code and doc · added 229 · deleted 24 |

## Why five and not nine

The player side of the catalogue carries **28** plain totals (`sum(x)`, no denominator); the team
side carried **4**. Everything team-facing is expressed as a rate — 15 per-match rates and 7
ratios — so the quantities the product actually displays had nothing to point at.

Nine rows were drafted. Two rulings removed four.

**"win, draw, loss are not metrics. they are results of a match."** W/D/L is a categorical
attribute already carried by `result`; counting it tallies a dimension. Removing those three rows
removed the entire cascade they caused, which had been most of the change:

```
                          with W/D/L rows    without them
generated blocks                      188             181
docs-block name collisions              3               0
dbt parse                            FAILS           clean
hand-written blocks renamed             3               0
references repointed                   26              20
files                                  16              14
```

**"use clean_sheets (for the number of matches) and clean_sheets_share (for the percentage)."**
That renames a metric that already ships, so it left this MR entirely — see below.

## The live defect this fixes

The bare `goals_against` block carries the **player** definition — goals conceded while that
player was on the pitch. `persist_docs` has already attached that sentence to **12 TEAM columns**
in BigQuery, where it is wrong. Splitting the block forces every reference to be classified, and
12 of them move to a correct definition.

**Each of the 20 was classified by reading the expression in that model's own SQL**, never from the
model's name. The two that look like exceptions are the ones that matter:

| site | why it is not what the model name suggests |
|---|---|
| `mart_player_match_log` → **`__team`** | a PLAYER-grained model, but `:90` is `if(s.team_sk = f.home_team_sk, f.goals_away, f.goals_home)` — the team's goals against |
| `int_legs__player_match` → **`__player`** | sits beside the team legs, but `:75` passes through `ps.goals_against` from the player-stat row |

Counted from the diff: 12 `__team`, 8 `__player`, and **zero** bare references left.

## Offline verification, re-derived rather than quoted

Three guards that would catch a bad row cannot run here — `assert_metric_catalogue_expr_resolvable`,
`assert_metric_direction_lower_is_better_agree` and the seed's schema tests all need a warehouse.
⚠ **And on an MR they would not see these rows even then**: `--defer --favor-state` resolves
`ref('metric_catalogue')` to main's seed. So each predicate was re-implemented against the file on
disk:

```
catalogue rows: 85
  unique (metric_id, entity)        : OK
  unique label_i18n_key             : OK
  unique (entity, label_en)         : OK
  accepted_values on 5 columns      : OK
  not_null on 9 columns             : OK
  direction <-> lower_is_better     : OK
  expr_resolvable (all rows)        : OK
  DANGLING references               : none
      goals_against__team       defined     12 references
      goals_against__player     defined      8 references
      goals_against             NOT DEFINED   0 references
```

⚠ **The first version of that checker reported 95 unresolved tokens and every one was a
pre-existing row** — it regexed columns out of the model's `.sql` and missed passthroughs. The
checker was wrong, not the seed. It now reads each model's declared column list. Recorded because
a checker that cries wolf is a checker nobody runs.

Gates: all six offline gates green, `sync_metric_docs_blocks --check` green (181 blocks in sync),
`ruff` clean, `dbt parse` clean. Line endings read as BYTES: no doubled CRs, every file uniform,
the seed still CRLF.

## Diff shape

The 24 deletions decompose exactly: **20** repointed `goals_against` lines, **1** in
`metric_columns.md` (the bare block replaced by the pair), **2** in `mart_head_to_head.sql`
(comment), **1** in the wireframes doc (a figure). Everything else is additions.

## The field choices worth attacking

**`format = integer` and a blank `denominator_expr` on all five.** The seed's schema says "Blank
for raw count metrics", and a denominator declares a division the pipeline performs — none of
these five is divided anywhere. All five can also exceed games played, which is why `integer` is
right and `count_fraction` would not be: that format renders "3/5" and belongs to a quantity capped
by the match count.

**`goals_against` (team) is `lower_better`**, with `lower_is_better` in lockstep — checked.

**`goalkeeper_saves` is the provider's TEAM statistics line**, not a sum of the individual
goalkeepers' saves. Two different feeds, and the description says so, because the catalogue's
existing `saves` is a PLAYER metric from the other one.

## What is deliberately NOT here

**`clean_sheets` / `clean_sheets_share` — its own change.** The ruling is right and the defect it
fixes is live: `mart_team_profile.clean_sheets` is a RATE
(`int_team_season__metrics_cumulative.sql:91`) while `mart_team_season.clean_sheets` and
`mart_team_momentum.clean_sheets` are COUNTS. One name, two numbers, one definition attached to
both. ⭐ The FRONTEND already agrees with the ruling — `metricRows.ts:50` serves it as
`count_fraction` with a `denom` mapping, and the committed fixture JSON carries
`"clean_sheets": 2` — so the warehouse is the side out of step. It reaches the 22-metric benchmark
set, the yoy family and an i18n label key.

**~40 further blank columns.** The new blocks also cover the derived family
(`goals_for_sum_season`, `goals_against_delta_yoy`), which resolves to the entity-suffixed block
rather than to its own name, so `--wire-shared-docs` cannot reach them. `--wire-metric-docs` can
and REFUSES: `int_team_momentum__metrics` is absent from `declare_missing_columns.py`'s
`MODEL_ENTITY`, so it will not guess the entity. That is a script edit this contract forbids.

⛔ **The gate is green without them.** The 5 rows create exactly 30 findings and all 30 are closed.
Unfinished work, not a failure — named so a green build is not read as "every new block is wired".

**Team totals for `shots_total`, `passes_total`, `passes_accurate`, `shots_on_goal`**: each would
split an existing player block and dangle 14/19/14/11 references.

## For the CPO

Nothing needs a decision to merge this. Two things to know:

1. **These English names change nothing a visitor sees today.** They go into the exported glossary;
   the site takes its labels from a separate hand-written file. Wiring them to the product is
   separate work.
2. **The clean-sheets rename is queued next**, on your ruling, and it is the one that moves a
   published column.
