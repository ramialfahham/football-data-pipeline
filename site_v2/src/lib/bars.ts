// Pure DISPLAY helpers for the comparison row. No metric facts are produced here:
// a bar width is how long to draw a rectangle (a different frontend could draw it
// differently); the "better" side is the locked design's green encoding of the
// served `direction` (project_v2_frontend_design: "better value coloured green per
// metric_catalogue.direction"). Neither is a stored fact — no DQ test asserts them.

export type Direction = "higher_better" | "lower_better" | "neutral";
export type Side = "home" | "away" | null;

const isNum = (v: unknown): v is number => typeof v === "number" && Number.isFinite(v);

// Relative bar length: each side's value as a share of the larger of the two present
// values → 0..100. Presentation only (never a probability).
export function barWidth(
  value: number | null | undefined,
  other: number | null | undefined,
): number {
  if (!isNum(value)) return 0;
  const max = Math.max(Math.abs(value), isNum(other) ? Math.abs(other) : 0);
  if (max <= 0) return 0;
  return Math.round((Math.abs(value) / max) * 100);
}

// Which side is the better value, for the green highlight. Null (no green) when a
// value is missing, the metric is directionless (neutral), or the two are equal.
export function betterSide(
  home: number | null | undefined,
  away: number | null | undefined,
  direction: Direction,
): Side {
  if (!isNum(home) || !isNum(away) || direction === "neutral" || home === away) return null;
  const homeBetter = direction === "higher_better" ? home > away : home < away;
  return homeBetter ? "home" : "away";
}

// Stacked-bar shares for the head-to-head record bar: each of W/D/L as a % of the
// total meetings. Presentation widths (how wide to draw each segment), not facts.
export function stackShares(
  wins: number | null | undefined,
  draws: number | null | undefined,
  losses: number | null | undefined,
): { w: number; d: number; l: number } {
  const w = isNum(wins) ? wins : 0;
  const d = isNum(draws) ? draws : 0;
  const l = isNum(losses) ? losses : 0;
  const total = w + d + l;
  if (total <= 0) return { w: 0, d: 0, l: 0 };
  return { w: (w / total) * 100, d: (d / total) * 100, l: (l / total) * 100 };
}

// Year-over-year delta display: the arrow (↑/↓ by the raw sign of the change) + a
// class resolved from the metric's direction (up = better → green, down = worse →
// red, flat = no change → muted). Display encoding of served values, not a fact.
export function deltaView(
  delta: number | null | undefined,
  lowerIsBetter: boolean,
): { arrow: string; cls: "up" | "down" | "flat" } {
  if (!isNum(delta) || delta === 0) return { arrow: "", cls: "flat" };
  const rose = delta > 0;
  const better = lowerIsBetter ? !rose : rose;
  return { arrow: rose ? "↑" : "↓", cls: better ? "up" : "down" };
}
