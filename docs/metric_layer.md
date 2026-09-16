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
| how a metric is **displayed** (group, tier, order, row patterns) | `docs/wireframes/metrics_display.md` |
| which past matches form a window, and how it is labelled | `docs/metrics_context_model.md` |
| what a metric is called on screen | the i18n layer — the seed holds only `label_i18n_key` and `label_en` |

No prose document defines a metric. Docs *reference* the seed; they never redefine it.

## Incomplete data is not calculated

**A metric is NULL unless its inputs are available for every match in the window.** We never average
over the matches we happen to have, so a thinly covered competition shows no per-match metrics —
that is the correct output, not a gap.

What counts as *available* differs by entity: a blank **player** stat is a zero (the player did
nothing), so it is available; a blank **team** stat means we do not know, so it is not.

A forfeit or walkover (`AWD`/`WO`) is the one thing that does not count against a season's coverage:
the match was never played, so there are no statistics to be missing. `games_expecting_team_stats`
is the team-side match count that leaves them out.

## How the layer works

**The seed defines; one model computes.** `metric_catalogue.csv` carries `metric_id`, `entity`,
`label_i18n_key`, `label_en`, `description`, `base_relation`, `numerator_expr`, `denominator_expr`,
`computation_kind`, `lower_is_better`, `format`, `metric_group`, `importance_tier`, `direction` and
`interpretation`. It is the registry and the glossary — the UI glossary (`metrics.json`) is built
from it.

Each metric is computed in exactly one place, so the same metric cannot be derived three different
ways. The canonical models are:

| grain | model |
|---|---|
| player, per club-season | `int_player_club_season__metrics` — the **atoms** source |
| player, per competition-season | `int_player_season__metrics` — **composes** the atoms |
| team, per season | `int_team_season__metrics` |

⚠ **Which player model depends on whether the metric is summable.** A COUNT that adds up across
clubs — goals, assists, passes, saves — goes in the **atoms** model, because both consumers sum it.
A ratio, a per-90 or a count composite does **not** add up, so it is derived where it is consumed:
in `int_player_season__metrics`, and in `mart_player_career` for the career log. That is the COMPOSE
pattern, and putting a ratio in the atoms model breaks it.

## Adding or changing a metric

1. Add the computation to the canonical model for its grain (see the table above).
2. Add the `metric_catalogue.csv` row. `description`, `direction` and `interpretation` are required —
   a row without them fails a guard, not a review.
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

There is no bespoke metric engine, and no test that re-derives a metric from the raw legs to
cross-check the model. The model computes it once, the catalogue defines it, and the guards stop the
two diverging. That is the whole mechanism.
