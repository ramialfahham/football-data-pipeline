# Metric layer

> The map of the metric layer: where a metric is defined, where it is computed, what makes it NULL,
> and what CI will stop you doing. Short by design.

## Where each thing lives

| You need… | Go to |
|---|---|
| a metric's definition / formula / units | **`dbt_project/seeds/metric_catalogue.csv`** — the single source of truth |
| why a metric column is NULL | [Incomplete data is not calculated](#incomplete-data-is-not-calculated) |
| how to add or change a metric | [Adding or changing a metric](#adding-or-changing-a-metric) |
| what CI will fail you on | [What the guards enforce](#what-the-guards-enforce) |
| which model computes it | [How the layer works](#how-the-layer-works) |
| how a metric is **displayed** (tier, row order within a group, row patterns) | `docs/wireframes/metrics_display.md` |
| what a metric **group** is — its key, its order, its names | [A group is defined once](#a-group-is-defined-once) |
| which past matches form a window, and how it is labelled | `docs/metrics_context_model.md` |
| what a metric is called on screen | the i18n layer — the seed holds only `label_i18n_key` and `label_en` |

No prose document defines a metric. Docs *reference* the seed; they never redefine it.

## Incomplete data is not calculated

**A metric is NULL unless its inputs are available for every match in the window.** We never average
over the matches we happen to have, so a thinly covered competition shows no per-match metrics —
that is the correct output, not a gap.

What counts as *available* differs by entity. A blank **player** stat is a zero only where the
provider counted that stat in the match — someone else in it has a value, or the score, the match
events or the team's own statistics line prove the zero — and missing otherwise; a team match with
no player data at all makes every player metric of that team NULL for any window that contains it.
That cleaning is done once, in `base_apif__fixture_players`, together with the pass-accuracy format,
the player goals reconciled to the score and the match-stat corrections; the issue that ruled them
states each rule. A blank **team** stat is a zero only where the other team's line has a value for
it, the match events prove no card, or the opponent had no shot on target; penalty and own goals
come from the team's goal events only where they add up to its score. That cleaning, with the
match-stat corrections, is done once in `base_apif__fixture_statistics`, which holds a row for every
team of every finished match. A team total summed from players is blank where any player's value is.

A forfeit or walkover (`AWD`/`WO`) counts only where the league table counts it: in `points_won`,
`goals` and `goals_against`. Every other metric leaves it out of numerator and denominator, so it
never counts against a window's coverage either: the match was never played, so there are no
statistics to be missing. `games_expecting_team_stats` is the team-side count of played matches.

## How the layer works

**The seed defines; one model computes.** `metric_catalogue.csv` carries `metric_id`, `entity`,
`label_i18n_key`, `label_en`, `description`, `base_relation`, `numerator_expr`, `denominator_expr`,
`computation_kind`, `lower_is_better`, `format`, `metric_group`, `importance_tier`, `direction`,
`interpretation` and `metric_group_order`. It is the registry and the glossary — the UI glossary
(`metrics.json`) is built from it.

### A group is defined once

A metric group is defined by three things and nowhere else: its **key**, the catalogue's
`metric_group` value on every metric it holds; its **order**, the catalogue's `metric_group_order`,
the same value on every row of the group and the positions 1..N across groups; and its **names**,
site copy keyed by the group key (`metricGroups.<key>.label` in `site_v2/src/i18n/strings.ts`,
one per language). The export publishes the key and order as `metric_groups.json`; every surface
that shows a group heading reads the groups from that file and the heading from the copy. No
document, seed or component spells a group's name or order on its own. Three checks hold it:
`assert_metric_group_order_is_one_per_group` in the warehouse, `tests/test_metric_groups.py` on
the committed export, and `site_v2/scripts/check-metric-labels.test.mjs` on the copy.

**Metrics are generated from the seed.** `scripts/generate_metric_sql.py` writes every surface's
metric SQL between two marker lines in the model: each metric is its catalogue formula over the rows
of that surface's own window — of `int_legs__player_match` for a player, of `int_legs__team_match`
with `int_legs__team_from_players` for a team — NULL unless every row it counts has its input (and,
for a player, the window holds no team match without player data). On a team surface a forfeit
counts only in `points_won`, `goals` and `goals_against`. The window — which matches, and the flags
a row carries — is hand-written in the model; the formula never is. A ratio is always computed from
the window's rows, never composed from pre-summed parts. The surfaces are listed in the script.

| grain | model |
|---|---|
| player, per club-season | `int_player_club_season__metrics` |
| player, per competition-season | `int_player_season__metrics` |
| team, per season, at every matchday | `int_team_season__metrics_cumulative` (`int_team_season__metrics` is its last matchday) |
| team, form window | `int_team_momentum__metrics` |

## Adding or changing a metric

1. Add the `metric_catalogue.csv` row. `description`, `direction` and `interpretation` are required —
   a row without them fails a guard, not a review.
2. Add it to the surface's list in `scripts/generate_metric_sql.py` and run
   `python scripts/generate_metric_sql.py`; the pytest in `test:python` fails when a model and the
   catalogue differ.
3. Run `python scripts/sync_metric_docs_blocks.py` and commit the result.
   `models/docs/metric_columns.md` is **generated** from the seed; hand-editing it fails CI
   (`--check` runs in `validate:governance`).
4. Keep the `description` inside BigQuery's 1,024-character column limit —
   `scripts/check_description_hygiene.py` measures the RENDERED text.
5. Add a 0–1 range test if it is a ratio.

## What the guards enforce

| Guard | Fails when |
|---|---|
| `assert_no_uncatalogued_season_metric` | a canonical model computes a metric with no catalogue row |
| `assert_metric_catalogue_expr_resolvable` | a formula references a column its `base_relation` does not have |
| `assert_metric_meaning_complete` | a row is missing the fields that make it mean something |
| `assert_metric_direction_lower_is_better_agree` | `direction` and `lower_is_better` contradict each other |
| `assert_metric_catalogue_unique_by_entity` | one `metric_id` is defined twice for an entity |
| `assert_form_window_rates_inputs_covered` | a team rate is shown on the form window while an input of its formula is missing from a non-awarded game of that window — the rule above, checked from the catalogue's own formula on every rate the surface carries |
| `assert_season_rates_inputs_covered` | the same on the season surface, at every matchday |
| `assert_player_metrics_follow_catalogue_formula` | a player surface's value differs from its catalogue formula recomputed from the legs over the same window |
| `assert_base_player_stats_cleaned` | a cleaned player row breaks a cleaning rule: a blank the provider counted, a part above its whole, goals that miss the score where a source adds up |
| `assert_player_match_cleaning_answer_key` | the cleaning returns anything but the hand-worked value of a real case |
| `assert_player_stat_corrections_within_limit` | a competition-season's share of corrected or blanked player rows exceeds the limit |
| `assert_team_metrics_follow_catalogue_formula` | a team surface's value differs from its catalogue formula recomputed from the legs over the same window, a forfeit counted only where the rule counts it |
| `assert_base_team_stats_cleaned` | a cleaned team line breaks a cleaning rule: a blank the rule fills, a goal split the events do not prove, a part above its whole, a contradiction left in place, a team of a finished match without a row |
| `assert_team_match_cleaning_answer_key` | the team cleaning returns anything but the hand-worked value of a real case |
| `assert_team_stat_corrections_within_limit` | a competition-season's share of corrected or blanked team lines exceeds the limit |
| `assert_team_form_window_follows_the_rule` | an upcoming side's form window or season record holds other matches than `docs/metrics_context_model.md` §4 names |
| `assert_team_yoy_pairs_the_same_games_played` | the year-over-year comparison pairs a season with anything but the previous season's first N matches |
| `tests/test_generate_metric_sql.py` | the generated metric SQL differs from what the catalogue generates |

Plus the standard model tests: ratios asserted in 0–1, `not_null` and `relationships` on keys,
`unique` on the grain.

**Exempt from the drift guard**, because they are not metrics: surrogate and foreign keys, the
coverage counts, the `*_sum_season` raw intermediates, and the playing-time facts (appearances,
starts, substitute appearances, minutes) which are dimensions. ⚠ Exempt is not the same as absent —
`points_won` *is* in the team model and clears the guard through the `_sum_season` exemption.
`league_rank` is a standings lookup and is a catalogue row for the glossary only.

## Facts from the provider, metrics from the warehouse

Two kinds of number reach a page, and the catalogue governs one of them.

- **Facts taken from the provider as published.** A match score. The official league table:
  rank, played, won, drawn, lost, goals scored and conceded, goal difference, points, form. The
  league publishes these and the provider passes them on; the warehouse does not compute them and
  must not — the official table carries deductions, halved points and tie-break orders that no
  recomputation from fixtures reproduces. They live in `fct_standings` and `mart_standings` as the
  row was published, and a page renders them as they are. Tallies of match results at a grain no
  team or player is measured on — a competition-season's matches, goals, home wins, the biggest
  margin, the longest run — are the same kind: results counted, not a metric defined.
- **Metrics the warehouse computes.** Everything in the catalogue: goals per match, deserved
  points, shots on goal difference. One formula, one model, the guards above.

The two never mix inside one block: a table is the provider's row, a board is catalogue metrics.
Where they overlap — the provider's points and the catalogue's `points_won` tally — a
reconciliation test guards the pair rather than one replacing the other.

## What this is NOT

There is no metric engine at run time. The catalogue defines each metric; a script writes the formula
into the models as plain SQL, and a test per entity recomputes every metric from the legs to prove
the models return it.
