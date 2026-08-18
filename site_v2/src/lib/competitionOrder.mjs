// CPO-approved ordering rule (.claude/task/escalations.log, 2026-08-16): mart_competition_index
// carries ordering FACTS only (next/last kickoff, region_rank); this page applies the actual
// ORDER BY, per the CPO's correction of an earlier draft that wanted to pre-bake it in the mart —
// "I don't agree that sorting has to be decided in the mart."
//
// Sort key, in order: has an upcoming fixture > days to next kickoff BUCKETED BY CALENDAR DAY
// (not the raw timestamp — a same-day tiebreak by clock time would rank a 10:15 kickoff above a
// 19:00 kickoff for no reason a reader cares about) > region_rank (the one hand-set judgement) >
// next kickoff time (deterministic same-day tiebreak) > league_code (full determinism).
// Competitions with nothing upcoming sort last, most-recently-played first.
//
// The SAME key orders the category headings too (2026-08-16 note: "apply the same key to the
// category headings, ordered by each group's earliest next kickoff") — that is where national
// teams rank ahead of club leagues during an international break, with no special case.
//
// Plain JS, not TypeScript: this module is imported directly by `competitionOrder.test.mjs` under
// bare `node --test`, which only supports `.ts` imports via Node's native type-stripping — on by
// default since Node >=22.18/23.6, but NOT guaranteed by this repo's declared `engines: >=22`
// floor (platform-reviewer finding, #62 step 5 round 1). Every other test in this codebase that
// needs something from a `.ts` file text-scans it instead
// (`site_v2/scripts/check-metric-labels.test.mjs`'s own documented reason) rather than depending
// on that capability; this file follows the same house pattern by not being TypeScript at all.
// Astro's own build (which compiles `CompetitionIndexGrid.astro`'s import of this file) is
// unaffected either way — Vite/esbuild handle plain JS natively.

/**
 * @typedef {import("./types.js").CompetitionIndexRow} CompetitionIndexRow
 * @typedef {{ key: string, labelEn: string, labelI18nKey: string, rows: CompetitionIndexRow[] }} CompetitionCategory
 */

// Datetimes in competition_index.json are always "YYYY-MM-DD HH:MM:SS+00:00" — fixed-width and
// always UTC — so plain string comparison IS chronological comparison. Avoids `new Date(...)`
// parsing a space-separated (non-ISO-T) string inconsistently across engines.
/** @param {string} datetime */
function dayOf(datetime) {
  return datetime.slice(0, 10);
}

/**
 * @param {CompetitionIndexRow} a
 * @param {CompetitionIndexRow} b
 * @returns {number}
 */
export function compareCompetitions(a, b) {
  const aUpcoming = a.next_kickoff_datetime !== null;
  const bUpcoming = b.next_kickoff_datetime !== null;
  if (aUpcoming !== bUpcoming) return aUpcoming ? -1 : 1;

  if (aUpcoming) {
    const aTime = /** @type {string} */ (a.next_kickoff_datetime);
    const bTime = /** @type {string} */ (b.next_kickoff_datetime);
    const aDay = dayOf(aTime);
    const bDay = dayOf(bTime);
    if (aDay !== bDay) return aDay < bDay ? -1 : 1;
    if (a.region_rank !== b.region_rank) return a.region_rank - b.region_rank;
    if (aTime !== bTime) return aTime < bTime ? -1 : 1;
    return a.league_code < b.league_code ? -1 : a.league_code > b.league_code ? 1 : 0;
  }

  // Neither has an upcoming fixture: most recently played first. A competition with no fixture
  // history at all (both datetimes null) sorts last of all — there is nothing to rank it by.
  const aLast = a.last_kickoff_datetime;
  const bLast = b.last_kickoff_datetime;
  if (aLast !== bLast) {
    if (aLast === null) return 1;
    if (bLast === null) return -1;
    return aLast > bLast ? -1 : 1;
  }
  return a.league_code < b.league_code ? -1 : a.league_code > b.league_code ? 1 : 0;
}

/**
 * Groups rows by competition_type, sorts rows within each group, then orders the groups
 * themselves by their own earliest-sorting member — the SAME key, applied one level up.
 * @param {CompetitionIndexRow[]} rows
 * @returns {CompetitionCategory[]}
 */
export function groupAndOrderCompetitions(rows) {
  /** @type {Map<string, CompetitionIndexRow[]>} */
  const byType = new Map();
  for (const row of rows) {
    const bucket = byType.get(row.competition_type);
    if (bucket) bucket.push(row);
    else byType.set(row.competition_type, [row]);
  }

  /** @type {CompetitionCategory[]} */
  const categories = [];
  for (const [key, groupRows] of byType) {
    const sorted = [...groupRows].sort(compareCompetitions);
    categories.push({
      key,
      labelEn: sorted[0].category_label_en,
      labelI18nKey: sorted[0].category_label_i18n_key,
      rows: sorted,
    });
  }

  categories.sort((a, b) => compareCompetitions(a.rows[0], b.rows[0]));
  return categories;
}
