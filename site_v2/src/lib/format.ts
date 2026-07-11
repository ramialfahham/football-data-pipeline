// Display formatting for the v2 site. FORMAT-ONLY — this file may format served
// values (locale number/date, percent = ratio×100, fraction denominators defined
// by the metric's `format`); it computes no metric facts. Nulls render as the
// en-dash "–" (never a fabricated 0), per site_architecture.md data-honesty.

export type Lang = "de" | "en" | "fi";
export const DASH = "–";

const LOCALE: Record<Lang, string> = { de: "de-DE", en: "en-GB", fi: "fi-FI" };
const isNum = (v: unknown): v is number => typeof v === "number" && Number.isFinite(v);

function nf(lang: Lang, min: number, max: number): Intl.NumberFormat {
  return new Intl.NumberFormat(LOCALE[lang], {
    minimumFractionDigits: min,
    maximumFractionDigits: max,
  });
}

export function decimal1(v: number | null | undefined, lang: Lang): string {
  return isNum(v) ? nf(lang, 1, 1).format(v) : DASH;
}
export function decimal0(v: number | null | undefined, lang: Lang): string {
  return isNum(v) ? nf(lang, 0, 0).format(v) : DASH;
}
export function integer(v: number | null | undefined, lang: Lang): string {
  return isNum(v) ? nf(lang, 0, 0).format(v) : DASH;
}
// Signed integer ("+17" / "−1" / "0"), for goal difference. Formatting only.
export function signedInteger(v: number | null | undefined, lang: Lang): string {
  return isNum(v)
    ? new Intl.NumberFormat(LOCALE[lang], { signDisplay: "exceptZero", maximumFractionDigits: 0 }).format(v)
    : DASH;
}
// `percent` metrics are served as a 0..1 ratio; the format multiplies by 100 for
// display (no naked %, the adjacent count row carries the volume — metrics_display.md).
export function percent(ratio: number | null | undefined, lang: Lang): string {
  return isNum(ratio) ? `${nf(lang, 0, 0).format(ratio * 100)}%` : DASH;
}
// `count_fraction` (e.g. clean sheets 3/5): numerator and denominator are both
// served (count + games); this only renders them as a fraction.
export function countFraction(
  num: number | null | undefined,
  den: number | null | undefined,
  lang: Lang,
): string {
  if (!isNum(num) || !isNum(den)) return DASH;
  return `${nf(lang, 0, 0).format(num)}/${nf(lang, 0, 0).format(den)}`;
}
// `points_fraction` (e.g. 13/15): the format's denominator is the maximum points
// obtainable = games × 3 (3 per game), per the display contract (metrics_display.md
// §window header / 01_fixture_page.md §5.3a). Presentation scaffold of the format,
// not a metric fact.
export function pointsFraction(
  points: number | null | undefined,
  games: number | null | undefined,
  lang: Lang,
): string {
  if (!isNum(points) || !isNum(games)) return DASH;
  return `${nf(lang, 0, 0).format(points)}/${nf(lang, 0, 0).format(games * 3)}`;
}

// Metric formats that take a single value (see metric_catalogue.csv `format`).
export type SingleFormat = "decimal_1" | "decimal_0" | "percent" | "integer";
export function formatValue(
  v: number | null | undefined,
  format: SingleFormat,
  lang: Lang,
): string {
  switch (format) {
    case "decimal_1": return decimal1(v, lang);
    case "decimal_0": return decimal0(v, lang);
    case "percent": return percent(v, lang);
    case "integer": return integer(v, lang);
  }
}

// ---- dates ---- kickoff is served as a UTC ISO string ("2026-07-26 22:30:00+00:00").
// Rendered in UTC so the static build is deterministic across machines and matches the
// stored kickoff; local-timezone display is a later enhancement (01_fixture_page.md §5.2).
function toDate(iso: string | null | undefined): Date | null {
  if (!iso) return null;
  const d = new Date(iso.replace(" ", "T"));
  return Number.isNaN(d.getTime()) ? null : d;
}
export function formatDate(iso: string | null | undefined, lang: Lang): string {
  const d = toDate(iso);
  if (!d) return DASH;
  return new Intl.DateTimeFormat(LOCALE[lang], {
    weekday: "short", day: "numeric", month: "short", year: "numeric", timeZone: "UTC",
  }).format(d);
}
export function formatShortDate(iso: string | null | undefined, lang: Lang): string {
  const d = toDate(iso);
  if (!d) return DASH;
  return new Intl.DateTimeFormat(LOCALE[lang], {
    day: "numeric", month: "short", timeZone: "UTC",
  }).format(d);
}
export function formatTime(iso: string | null | undefined, lang: Lang): string {
  const d = toDate(iso);
  if (!d) return DASH;
  return new Intl.DateTimeFormat(LOCALE[lang], {
    hour: "2-digit", minute: "2-digit", hourCycle: "h23", timeZone: "UTC",
  }).format(d);
}
