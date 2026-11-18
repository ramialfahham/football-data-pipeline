// The catalogue's metric groups in their order, for the pages that group metrics themselves. The
// groups — which exist and in what order — come from `src/data/metric_groups.json` (the export's
// copy of the catalogue's key + `metric_group_order`); a group's name per locale is
// `metricLabel(lang, "metricGroups.<key>.label")`. The rows a page shows come from
// `src/data/metric_rows.json`.
import metricGroups from "../data/metric_groups.json";
import metricRows from "../data/metric_rows.json";
import type { ServedMetricRow } from "./types";

/** The catalogue's group keys in the catalogue's order, from the exported copy. */
export const GROUP_KEYS_IN_ORDER: string[] = [...metricGroups.groups]
  .sort((a, b) => a.order - b.order)
  .map((g) => g.key);

// A served row is a display slot; the team surface binds another catalogue metric in one of them.
// A team season is ranked against a whole league, where matches played differ between teams, so the
// clean-sheets slot reads the proportion there (docs/wireframes/metrics_display.md, row 3).
const TEAM_BINDINGS: Record<string, Pick<ServedMetricRow, "metric_id" | "label_i18n_key" | "format" | "per_match">> = {
  clean_sheets: { metric_id: "clean_sheets_pct", label_i18n_key: "metrics.clean_sheets_pct.label", format: "percent", per_match: false },
};

/** The row the TEAM surface renders for a served row. Without a binding that is the row itself. */
export function teamBinding(row: ServedMetricRow): ServedMetricRow {
  const bound = TEAM_BINDINGS[row.metric_id];
  return bound ? { ...row, ...bound } : row;
}

/** A club's comparison rows: the served rows bound to the team surface, in their groups, each kept
 *  when its metric is one of the club's comparison metrics (`compared`, served) and `has` finds a
 *  value for it. */
export function teamComparisonGroups(compared: string[], has: (metricId: string) => boolean) {
  const keys = new Set(compared);
  const served = metricRows.rows as ServedMetricRow[];
  return [...metricGroups.groups]
    .sort((a, b) => a.order - b.order)
    .map((g) => {
      const rows = served
        .filter((r) => r.metric_group === g.key)
        .map(teamBinding)
        .filter((r) => keys.has(r.metric_id) && has(r.metric_id));
      return { key: g.key, rows, hasKey: rows.some((r) => r.is_key_metric) };
    })
    .filter((g) => g.rows.length > 0);
}
