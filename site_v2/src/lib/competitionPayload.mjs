// What the competition page does with its payload before rendering: pick the season to show,
// split the standings into the sections a page draws, find the round the warehouse flagged next,
// file the Rankings tab's boards under their metric groups, and turn the season summary into the
// fact rows that have something to show. Selection over served columns only — no number is
// computed here; a value the mart serves as null yields no row.
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

/** The round the warehouse flagged as next (the Matchdays tab opens on it; the header's round
 *  reads it), or null when none is flagged — after the season, or before the first round. */
export function nextRound(rounds) {
  return (rounds ?? []).find((r) => r.is_next_round) ?? null;
}

/** The Rankings tab's boards filed under their metric groups: one entry per group key, in the
 *  order the keys are given (the catalogue's, from metric_groups.json), holding the boards the
 *  export served for that group in the export's order (the ruled order within a group). A group
 *  with no board is absent; a board whose group the catalogue does not list is dropped, since a
 *  group heading it could sit under does not exist. */
export function boardGroups(boards, groupKeys) {
  const byGroup = new Map(groupKeys.map((key) => [key, []]));
  for (const board of boards ?? []) {
    if (!board.rows?.length) continue;
    byGroup.get(board.metric_group)?.push(board);
  }
  return [...byGroup].filter(([, list]) => list.length > 0).map(([key, list]) => ({ key, boards: list }));
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
