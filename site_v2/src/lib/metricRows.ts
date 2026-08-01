// The LOCKED 16-row team metric contract. Shared by the fixture comparison (home vs away,
// per window) and the team page Performance tab (vs the league / vs last season).
//
// This is DISPLAY CONFIG, not computation: order + groups + tiers come from
// docs/wireframes/metrics_display.md (CPO-locked 2026-06-11); `format` + `direction`
// mirror dbt_project/seeds/metric_catalogue.csv (the metric SSoT) — the frontend
// renders these definitions, it does not invent them. Until the catalogue exposes
// group/tier/order columns (GAP-09) this file is their frontend home, per that doc.
//
// `field` is the payload key on w1/w2 (the bare metric name) — NOT the display id.
// Note the intentional field ≠ metrics_display id: row 6 is `shots_on_goal_per_match`.
//
// #370: there is no `label` field here. A metric's display name lives once, per locale, in
// `i18n/strings.ts` (METRIC_LABELS), keyed by the catalogue's own `label_i18n_key` — which is what
// `labelKey` below holds. Render a name with `metricLabel(lang, row.labelKey)`; never re-spell one
// here. The order/group/tier contract from `docs/wireframes/metrics_display.md` is unchanged and still
// lives in this file; only the strings moved.

import type { Direction } from "./bars";

export type RowFormat = "decimal_1" | "decimal_0" | "percent" | "count_fraction";
export type MetricGroup =
  | "Goals" | "Shooting" | "Duels" | "Defending" | "Passing" | "Set pieces" | "Goalkeeping";

export interface MetricRowDef {
  field: string;              // payload key on w1 / w2
  // The catalogue's `label_i18n_key`, verbatim. Resolve it with `metricLabel(lang, labelKey)`.
  // ⚠ Read it from the `label_i18n_key` COLUMN of metric_catalogue.csv, never from `metric_id` —
  // those two deliberately disagree for at least one metric (see row 6). Inferring a key from an id
  // is how you break the binding. `check-metric-labels.test.mjs` cross-checks every one.
  labelKey: string;
  group: MetricGroup;
  tier: 1 | 2 | 3;            // visibility under constraint (never reorders — display doc)
  format: RowFormat;
  direction: Direction;       // drives the green "better" side (never `lower_is_better`)
  sublabel?: string;          // small caption under the label (e.g. the T·I·B aggregate)
  // count_fraction denominator field per window (both served: count + games).
  denom?: { w1: string; w2: string };
}

// Fixed group order (metrics_display.md block order). The comparison renders groups
// in this order with a subhead, and rows in array order within each group.
export const GROUP_ORDER: MetricGroup[] = [
  "Goals", "Shooting", "Duels", "Defending", "Passing", "Set pieces", "Goalkeeping",
];

export const METRIC_ROWS: MetricRowDef[] = [
  { field: "goals_per_match", labelKey: "metrics.goals_per_match.label", group: "Goals", tier: 1, format: "decimal_1", direction: "higher_better" },
  { field: "goals_against_per_match", labelKey: "metrics.goals_against_per_match.label", group: "Goals", tier: 1, format: "decimal_1", direction: "lower_better" },
  { field: "clean_sheets", labelKey: "metrics.clean_sheets.label", group: "Goals", tier: 2, format: "count_fraction", direction: "higher_better", denom: { w1: "games_in_window", w2: "games_played" } },
  { field: "shots_per_match", labelKey: "metrics.shots_per_match.label", group: "Shooting", tier: 2, format: "decimal_1", direction: "higher_better" },
  { field: "danger_zone_ratio", labelKey: "metrics.danger_zone_ratio.label", group: "Shooting", tier: 2, format: "percent", direction: "higher_better" },
  // ⚠ `field` and `labelKey` DISAGREE on this row on purpose. `metric_catalogue.csv` declares
  //   metric_id = shots_on_goal_per_match   →   label_i18n_key = metrics.shots_on_target_per_match.label
  // The internal id says "on goal", the user-facing term is "on target". Do NOT "fix" this to
  // `metrics.shots_on_goal_per_match.label` — the catalogue declares no such key and the label would
  // resolve to nothing.
  { field: "shots_on_goal_per_match", labelKey: "metrics.shots_on_target_per_match.label", group: "Shooting", tier: 1, format: "decimal_1", direction: "higher_better" },
  { field: "finishing_efficiency", labelKey: "metrics.finishing_efficiency.label", group: "Shooting", tier: 1, format: "percent", direction: "higher_better" },
  { field: "duels_per_match", labelKey: "metrics.duels_per_match.label", group: "Duels", tier: 2, format: "decimal_0", direction: "higher_better" },
  { field: "duels_won_pct", labelKey: "metrics.duels_won_pct.label", group: "Duels", tier: 2, format: "percent", direction: "higher_better" },
  // ⚠ `sublabel` is still an ENGLISH string rendered in all three locales. It is a caption, not a
  // metric name, so it is outside this task's criteria — recorded in the contract as residual.
  { field: "defensive_actions_per_match", labelKey: "metrics.defensive_actions_per_match.label", group: "Defending", tier: 2, format: "decimal_1", direction: "higher_better", sublabel: "tackles + interceptions + blocks" },
  { field: "passes_per_match", labelKey: "metrics.passes_per_match.label", group: "Passing", tier: 3, format: "decimal_0", direction: "higher_better" },
  { field: "pass_accuracy", labelKey: "metrics.pass_accuracy.label", group: "Passing", tier: 2, format: "percent", direction: "higher_better" },
  { field: "key_passes_per_match", labelKey: "metrics.key_passes_per_match.label", group: "Passing", tier: 2, format: "decimal_1", direction: "higher_better" },
  { field: "corner_kicks_per_match", labelKey: "metrics.corner_kicks_per_match.label", group: "Set pieces", tier: 3, format: "decimal_1", direction: "higher_better" },
  { field: "corners_against_per_match", labelKey: "metrics.corners_against_per_match.label", group: "Set pieces", tier: 3, format: "decimal_1", direction: "lower_better" },
  { field: "save_ratio", labelKey: "metrics.save_ratio.label", group: "Goalkeeping", tier: 2, format: "percent", direction: "higher_better" },
];
