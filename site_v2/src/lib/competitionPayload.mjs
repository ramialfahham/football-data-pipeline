// What the competition page does with its payload before rendering: pick the season to show,
// split the standings into the sections a page draws, take the ends of the served deserved order,
// and turn the season summary into the fact rows that have something to show. Selection over
// served columns only — no number is computed here; a value the mart serves as null yields no row.
//
// Plain JS for the same reason as competitionOrder.mjs: `competitionPayload.test.mjs` imports it
// under bare `node --test`.

/** The season to show for one competition: the latest season present among the served payloads.
 *  After a season ends this keeps its final table and its numbers on the page until the next
 *  season's first data arrives; between seasons the standings block is the previous season's. */
export function latestSeasonPayload(payloads) {
  let best = null;
  for (const p of payloads) {
    if (!best || Number(p.season) > Number(best.season)) best = p;
  }
  return best;
}

/** The standings sections a page draws, in served order: one per section name, the provider's
 *  cross-group ranking tables left out. Rows keep their served order (section, then rank). */
export function standingsSections(standings) {
  const sections = new Map();
  for (const row of standings ?? []) {
    if (row.table_kind === "ranking") continue;
    const key = row.group_name ?? "";
    if (!sections.has(key)) sections.set(key, { name: key, kind: row.table_kind, rows: [] });
    sections.get(key).rows.push(row);
  }
  return [...sections.values()];
}

/** The two deserved-points boards: the rows the warehouse ranked 1..3 by the gap
 *  (deserved_points_gap_rank — the teams with fewer points than deserved, most under-rewarded
 *  first) and the three highest ranks in reverse (the most over-rewarded first). The order is
 *  the served rank's; the page reads its two ends. Fewer than two ranked rows: no boards. */
export function deservedBoards(deserved, size = 3) {
  const rows = (deserved ?? []).filter((r) => r.deserved_points_gap_rank != null);
  if (rows.length < 2) return null;
  return {
    better: rows.slice(0, size),
    worse: rows.slice(-size).reverse(),
  };
}

/** The season facts that have something to show, in the approved order. Each is {key, value,
 *  context} where value is a served number, a served score or a served match, and context names
 *  the match, round or teams behind it. A null served value yields no fact. */
export function seasonFacts(summary) {
  if (!summary) return [];
  const facts = [];
  if (summary.goals_per_match != null) {
    facts.push({ key: "goalsPerMatch", value: { number: summary.goals_per_match, decimals: 1 },
                 context: { goals: summary.total_goals, matches: summary.matches_played } });
  }
  if (summary.home_wins != null && summary.matches_played != null) {
    facts.push({ key: "homeWins", value: { count: summary.home_wins, of: summary.matches_played },
                 context: { draws: summary.drawn_matches, awayWins: summary.away_wins } });
  }
  if (summary.biggest_margin) {
    facts.push({ key: "biggestMargin", value: { score: summary.biggest_margin }, context: { match: summary.biggest_margin } });
  }
  if (summary.most_goals) {
    facts.push({ key: "mostGoals", value: { score: summary.most_goals }, context: { match: summary.most_goals } });
  }
  if (summary.longest_unbeaten_run != null && (summary.longest_unbeaten_teams ?? []).length > 0) {
    facts.push({ key: "longestUnbeaten", value: { matches: summary.longest_unbeaten_run },
                 context: { teams: summary.longest_unbeaten_teams } });
  }
  if (summary.longest_winless_run != null && (summary.longest_winless_teams ?? []).length > 0) {
    facts.push({ key: "longestWinless", value: { matches: summary.longest_winless_run },
                 context: { teams: summary.longest_winless_teams } });
  }
  return facts;
}

/** The next matchday's flagged fixture, if the warehouse flagged one. */
export function matchThatMatters(nextMatchday) {
  return (nextMatchday ?? []).find((fx) => fx.is_match_that_matters) ?? null;
}
