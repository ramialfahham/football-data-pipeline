# Evidence — rename the team metric `goals_for` to `goals`

Step 1 of 4 in the catalogue naming programme. Every figure measured on this branch against merged
main `d95a04f`.

## The headline

| | |
|---|---|
| catalogue rows | 86, unchanged |
| fields changed on the one row | 2 (`metric_id`, `label_i18n_key`) |
| formula, direction, group, tier, description, interpretation | byte-identical |
| generated docs blocks | **183 → 182** |
| description references repointed | **18** (12 team, 6 player) |
| dangling `{{ doc() }}` after the change | **0** |
| model SQL files changed | **0** |
| columns renamed | **0** |
| files | 11 dbt files, +52 / −57 |

## What was bigger than the first draft of the contract predicted

The contract first said 12 references. It is 18. Renaming the metric made `goals` exist for both
entities with different formulas (team `sum(goals_for)` from the scoreline, player
`sum(goals_total)` from player stats), so the generator applied its one-name-two-meanings rule and
replaced the bare `goals` block with `goals__team` and `goals__player`. That dangled the six
existing `doc('goals')` references as well as the twelve `doc('goals_for')` ones. The contract was
amended before any file outside its original scope was touched.

## Classification, by reading the model rather than the name

All 12 `goals_for` references are the team scoreline; all 6 `goals` references sit on player-grain
models. The one that does not follow from its file name: `mart_player_match_log` is a player model,
but its `goals_for` is `if(team_sk = home_team_sk, f.goals_home, f.goals_away)`
(`mart_player_match_log.sql:89-90`), the fixture scoreline, so it takes the team block. Its own
`goals_total` is a different column and carries no description reference. Confirmed independently
by analytics-engineer-reviewer, which re-read all 18 rather than trusting this contract.

## Offline verification

| check | result |
|---|---|
| `sync_metric_docs_blocks.py --check` | OK, 182 blocks match the seed and the model YAML |
| `check_description_hygiene.py` | ok, 1604 descriptions, 244 blocks resolved, all within limits |
| `dbt parse` (1.7.19 / bigquery 1.7.2) | clean, 0 errors, 0 dangling references |
| seed tests re-derived offline | 86 rows, 15 fields, no duplicate `(metric_id, entity)`, no duplicate `label_i18n_key`, no duplicate `(entity, label_en)` |
| `python -m pytest tests/` | 1007 passed, 1 skipped, 14 subtests |
| remaining `goals_for` in the repo | 77 bare plus 23 derived, every one a COLUMN name, which is the intended outcome |

## Mutations, watched failing

| mutation | guard | result |
|---|---|---|
| one reference pointed back at `doc('goals_for')`, the block the rename deleted | `dbt parse` | **Compilation Error** |
| a block appended by hand to the generated file | `sync_metric_docs_blocks.py --check` | **failed, with the "do not edit the generated file" message** |

Restored after each; the code diff is byte-identical across both review rounds.

## Review

Round 1: analytics-engineer PASS, football-analytics-expert PASS, scope-auditor FAIL. The FAIL was
about authority rather than code: the contract cited a plan file outside the repo for a §10 naming
decision while `escalations.log` held no entry. Fixed at the root by recording the whole naming
programme, six rulings in the CPO's own words, in `escalations.log`, and repointing `refs` at it.
Round 2: scope-auditor PASS. The code did not move between rounds.
