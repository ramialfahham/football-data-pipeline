// The LOCKED 16-row team metric contract. Shared by the fixture comparison (home vs away,
// per window) and the team page Performance tab (vs the league / vs last season).
//
// This is DISPLAY CONFIG, not computation: row order within a group and tiers come from
// docs/wireframes/metrics_display.md (LOCKED); `format` + `direction` mirror
// dbt_project/seeds/metric_catalogue.csv (the metric SSoT) — the frontend renders these
// definitions, it does not invent them. A row's `group` is the catalogue's `metric_group` KEY
// verbatim; the groups themselves — which exist and in what order — come from
// `src/data/metric_groups.json` (the export's copy of the catalogue's key + `metric_group_order`),
// and a group's name per locale is `metricLabel(lang, "metricGroups.<key>.label")`. Nothing about
// a group is spelled here (#152).
//
// `field` is the payload key on w1/w2 (the bare metric name) — NOT the display id.
// Note the intentional field ≠ metrics_display id: row 6 is `shots_on_goal_per_match`.
//
// A row is a display SLOT, and one slot can bind a different catalogue metric per surface: the
// fixture windows serve `clean_sheets` (a count) where the team page ranks `clean_sheets_pct`
// (a proportion). `field`/`labelKey`/`format` are the FIXTURE binding; the team surface reads
// `teamBinding(row)`, which returns the row's `team` override or the row itself.
//
// #370: there is no `label` field here. A metric's display name lives once, per locale, in
// `i18n/strings.ts` (METRIC_LABELS), keyed by the catalogue's own `label_i18n_key` — which is what
// `labelKey` below holds. Render a name with `metricLabel(lang, row.labelKey)`; never re-spell one
// here. The row order and tier contract from `docs/wireframes/metrics_display.md` still lives in
// this file; the strings and the groups moved out.

import type { Direction } from "./bars";
import type { SingleFormat } from "./format";
import metricGroups from "../data/metric_groups.json";

export type RowFormat = "decimal_1" | "decimal_0" | "percent" | "count_fraction";

/** The catalogue's group keys in the catalogue's order, from the exported copy. Every `group:`
 *  below is one of them — `check-metric-labels.test.mjs` asserts it, and that each has a name in
 *  every locale. */
export const GROUP_KEYS_IN_ORDER: string[] = [...metricGroups.groups]
  .sort((a, b) => a.order - b.order)
  .map((g) => g.key);

/** What the TEAM surface binds for a slot whose two surfaces measure different things.
 *  Only `clean_sheets` needs one: the fixture windows serve the COUNT of shut-outs beside the
 *  matches behind it, while the league benchmark and the year-over-year delta serve
 *  `clean_sheets_pct`, the proportion — two catalogue metrics, one row of the display contract. */
export interface TeamBinding {
  field: string;              // key on the benchmark's `metric_key` / the `{field}_delta_yoy` column
  labelKey: string;
  format: SingleFormat;
}

export interface MetricRowDef {
  field: string;              // payload key on w1 / w2
  // The catalogue's `label_i18n_key`, verbatim. Resolve it with `metricLabel(lang, labelKey)`.
  // ⚠ Read it from the `label_i18n_key` COLUMN of metric_catalogue.csv, never from `metric_id` —
  // those two deliberately disagree for at least one metric (see row 6). Inferring a key from an id
  // is how you break the binding. `check-metric-labels.test.mjs` cross-checks every one.
  labelKey: string;
  group: string;              // the catalogue's `metric_group` key, verbatim
  tier: 1 | 2 | 3;            // visibility under constraint (never reorders — display doc)
  format: RowFormat;
  direction: Direction;       // drives the green "better" side (never `lower_is_better`)
  sublabel?: string;          // small caption under the label (e.g. the T·I·B aggregate)
  // count_fraction denominator field per window (both served: count + games). Fixture surface
  // only — a team season is ranked against a league, which is what `team` below binds instead.
  denom?: { w1: string; w2: string };
  team?: TeamBinding;         // set only where the team surface measures something else
}

/** The binding the TEAM surface renders for a row. Without an override that is the row itself;
 *  `count_fraction` is a fixture-window form (numerator beside its denominator), and the team
 *  surface serves neither pair, so it reads as a percent there. */
export function teamBinding(row: MetricRowDef): TeamBinding {
  return row.team ?? {
    field: row.field,
    labelKey: row.labelKey,
    format: row.format === "count_fraction" ? "percent" : row.format,
  };
}

// Groups render in `GROUP_KEYS_IN_ORDER` with a subhead; rows in array order within each group.
export const METRIC_ROWS: MetricRowDef[] = [
  { field: "goals_per_match", labelKey: "metrics.goals_per_match.label", group: "goals", tier: 1, format: "decimal_1", direction: "higher_better" },
  { field: "goals_against_per_match", labelKey: "metrics.goals_against_per_match.label", group: "goals", tier: 1, format: "decimal_1", direction: "lower_better" },
  // ⚠ The ONE row whose two surfaces bind different catalogue metrics. The fixture windows serve
  //   `clean_sheets`, a count of shut-outs, rendered against the matches behind it (3/5). The team
  //   page ranks `clean_sheets_pct`, the proportion, because teams are compared across a league.
  //   Read the team side through `teamBinding()`; never assume `field` covers both.
  { field: "clean_sheets", labelKey: "metrics.clean_sheets.label", group: "goals", tier: 2, format: "count_fraction", direction: "higher_better", denom: { w1: "games_in_window", w2: "games_played" },
    team: { field: "clean_sheets_pct", labelKey: "metrics.clean_sheets_pct.label", format: "percent" } },
  { field: "shots_per_match", labelKey: "metrics.shots_per_match.label", group: "shooting", tier: 2, format: "decimal_1", direction: "higher_better" },
  { field: "shots_inside_box_pct", labelKey: "metrics.shots_inside_box_pct.label", group: "shooting", tier: 2, format: "percent", direction: "higher_better" },
  // ⚠ `field` and `labelKey` DISAGREE on this row on purpose. `metric_catalogue.csv` declares
  //   metric_id = shots_on_goal_per_match   →   label_i18n_key = metrics.shots_on_target_per_match.label
  // Do NOT "fix" this to `metrics.shots_on_goal_per_match.label` — the catalogue declares no such
  // key and the label would resolve to nothing.
  // ⭐ The REASON changed in step 5, the INSTRUCTION did not. This used to be a genuine term split
  // (internal id "on goal", user-facing label "on target"); RULING 2 closed it, so the label now
  // reads "Ø Shots on goal" and both say "on goal". What is left is only a LEGACY KEY NAME, which
  // is still the join key and still the only thing that resolves this label.
  { field: "shots_on_goal_per_match", labelKey: "metrics.shots_on_target_per_match.label", group: "shooting", tier: 1, format: "decimal_1", direction: "higher_better" },
  { field: "finishing_efficiency_pct", labelKey: "metrics.finishing_efficiency_pct.label", group: "shooting", tier: 1, format: "percent", direction: "higher_better" },
  { field: "duels_per_match", labelKey: "metrics.duels_per_match.label", group: "one_on_one", tier: 2, format: "decimal_0", direction: "higher_better" },
  { field: "duels_won_pct", labelKey: "metrics.duels_won_pct.label", group: "one_on_one", tier: 2, format: "percent", direction: "higher_better" },
  // ⚠ `sublabel` is still an ENGLISH string rendered in all three locales. It is a caption, not a
  // metric name, so it is outside this task's criteria — recorded in the contract as residual.
  { field: "defensive_actions_per_match", labelKey: "metrics.defensive_actions_per_match.label", group: "defending", tier: 2, format: "decimal_1", direction: "higher_better", sublabel: "tackles + interceptions + blocks" },
  { field: "passes_per_match", labelKey: "metrics.passes_per_match.label", group: "passing", tier: 3, format: "decimal_0", direction: "higher_better" },
  { field: "passes_accuracy_pct", labelKey: "metrics.passes_accuracy_pct.label", group: "passing", tier: 2, format: "percent", direction: "higher_better" },
  { field: "passes_key_per_match", labelKey: "metrics.passes_key_per_match.label", group: "passing", tier: 2, format: "decimal_1", direction: "higher_better" },
  { field: "corners_per_match", labelKey: "metrics.corners_per_match.label", group: "set_pieces", tier: 3, format: "decimal_1", direction: "higher_better" },
  { field: "corners_against_per_match", labelKey: "metrics.corners_against_per_match.label", group: "set_pieces", tier: 3, format: "decimal_1", direction: "lower_better" },
  { field: "saves_pct", labelKey: "metrics.saves_pct.label", group: "goalkeeping", tier: 2, format: "percent", direction: "higher_better" },
];
