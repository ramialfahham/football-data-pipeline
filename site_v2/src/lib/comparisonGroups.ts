// The rows of a two-team metric comparison, grouped under the catalogue's metric groups in their
// order. A row whose value is missing on BOTH sides is left out (avoid a wall of dashes); a group
// without a row is left out. Rows that are not key metrics stand behind the Show all metrics switch.
import metricRows from "../data/metric_rows.json";
import metricGroups from "../data/metric_groups.json";
import { asNumber } from "./types";
import type { ServedMetricRow, WindowStats } from "./types";

export interface ComparisonGroup {
  key: string;
  rows: ServedMetricRow[];
  hasKey: boolean;
}

export function comparisonGroups(
  home: WindowStats | null | undefined,
  away: WindowStats | null | undefined,
  withoutGroups: string[] = [],
): ComparisonGroup[] {
  const served = metricRows.rows as ServedMetricRow[];
  const hasData = (def: ServedMetricRow): boolean =>
    asNumber(home?.[def.metric_id]) !== null || asNumber(away?.[def.metric_id]) !== null;
  return [...metricGroups.groups]
    .filter((g) => !withoutGroups.includes(g.key))
    .sort((a, b) => a.order - b.order)
    .map((g) => {
      const rows = served.filter((r) => r.metric_group === g.key && hasData(r));
      return { key: g.key, rows, hasKey: rows.some((r) => r.is_key_metric) };
    })
    .filter((g) => g.rows.length > 0);
}

/** The switch has something to do only when the comparison shows a key row and another row. */
export function needsSwitch(groups: ComparisonGroup[]): boolean {
  const rows = groups.flatMap((g) => g.rows);
  return rows.some((r) => r.is_key_metric) && rows.some((r) => !r.is_key_metric);
}
