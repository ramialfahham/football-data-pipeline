// The LOCKED 16-row team comparison contract for the fixture page.
//
// This is DISPLAY CONFIG, not computation: order + groups + tiers come from
// docs/wireframes/metrics_display.md (CPO-locked 2026-06-11); `format` + `direction`
// mirror dbt_project/seeds/metric_catalogue.csv (the metric SSoT) — the frontend
// renders these definitions, it does not invent them. Until the catalogue exposes
// group/tier/order columns (GAP-09) this file is their frontend home, per that doc.
//
// `field` is the payload key on w1/w2 (the bare metric name) — NOT the display id.
// Note the intentional field ≠ metrics_display id: row 6 is `shots_on_goal_per_match`.

import type { Direction } from "./bars";

export type RowFormat = "decimal_1" | "decimal_0" | "percent" | "count_fraction";
export type MetricGroup =
  | "Goals" | "Shooting" | "Duels" | "Defending" | "Passing" | "Set pieces" | "Goalkeeping";

export interface MetricRowDef {
  field: string;              // payload key on w1 / w2
  label: string;              // locked display label (metrics_display.md); EN for now
  labelKey: string;           // catalogue i18n key — per-locale wiring is #370
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
  { field: "goals_per_match", label: "Ø Goals", labelKey: "metrics.goals_per_match.label", group: "Goals", tier: 1, format: "decimal_1", direction: "higher_better" },
  { field: "goals_against_per_match", label: "Ø Goals against", labelKey: "metrics.goals_against_per_match.label", group: "Goals", tier: 1, format: "decimal_1", direction: "lower_better" },
  { field: "clean_sheets", label: "Clean sheets", labelKey: "metrics.clean_sheets.label", group: "Goals", tier: 2, format: "count_fraction", direction: "higher_better", denom: { w1: "games_in_window", w2: "games_played" } },
  { field: "shots_per_match", label: "Ø Shots", labelKey: "metrics.shots_per_match.label", group: "Shooting", tier: 2, format: "decimal_1", direction: "higher_better" },
  { field: "danger_zone_ratio", label: "% Shots from box", labelKey: "metrics.danger_zone_ratio.label", group: "Shooting", tier: 2, format: "percent", direction: "higher_better" },
  { field: "shots_on_goal_per_match", label: "Ø Shots on target", labelKey: "metrics.shots_on_target_per_match.label", group: "Shooting", tier: 1, format: "decimal_1", direction: "higher_better" },
  { field: "finishing_efficiency", label: "% Goals per shot on target", labelKey: "metrics.finishing_efficiency.label", group: "Shooting", tier: 1, format: "percent", direction: "higher_better" },
  { field: "duels_per_match", label: "Ø Duels", labelKey: "metrics.duels_per_match.label", group: "Duels", tier: 2, format: "decimal_0", direction: "neutral" },
  { field: "duels_won_pct", label: "% Duels won", labelKey: "metrics.duels_won_pct.label", group: "Duels", tier: 2, format: "percent", direction: "higher_better" },
  { field: "defensive_actions_per_match", label: "Ø Defensive actions", labelKey: "metrics.defensive_actions_per_match.label", group: "Defending", tier: 2, format: "decimal_1", direction: "neutral", sublabel: "tackles + interceptions + blocks" },
  { field: "passes_per_match", label: "Ø Passes", labelKey: "metrics.passes_per_match.label", group: "Passing", tier: 3, format: "decimal_0", direction: "neutral" },
  { field: "pass_accuracy", label: "% Pass accuracy", labelKey: "metrics.pass_accuracy.label", group: "Passing", tier: 2, format: "percent", direction: "higher_better" },
  { field: "key_passes_per_match", label: "Ø Key passes", labelKey: "metrics.key_passes_per_match.label", group: "Passing", tier: 2, format: "decimal_1", direction: "higher_better" },
  { field: "corner_kicks_per_match", label: "Ø Corners", labelKey: "metrics.corner_kicks_per_match.label", group: "Set pieces", tier: 3, format: "decimal_1", direction: "neutral" },
  { field: "corners_against_per_match", label: "Ø Corners against", labelKey: "metrics.corners_against_per_match.label", group: "Set pieces", tier: 3, format: "decimal_1", direction: "neutral" },
  { field: "save_ratio", label: "% Save percentage", labelKey: "metrics.save_ratio.label", group: "Goalkeeping", tier: 2, format: "percent", direction: "higher_better" },
];
