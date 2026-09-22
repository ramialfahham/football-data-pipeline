// Pins what the competition page does with its payload: the latest season wins, ranking tables
// are left out, the next round is the flagged one, boards file under the catalogue's groups in
// its order, and a null fact is no row — the rules that keep the page from showing an empty
// block or an older season by accident.

import { test } from "node:test";
import assert from "node:assert/strict";
import {
  boardGroups,
  latestSeasonPayload,
  nextRound,
  seasonFacts,
  standingsSections,
} from "./competitionPayload.mjs";

test("the latest served season is the one shown, whatever order the files come in", () => {
  const picked = latestSeasonPayload([{ season: 2025 }, { season: 2026 }, { season: 2024 }]);
  assert.equal(picked.season, 2026);
  assert.equal(latestSeasonPayload([]), null);
});

test("standings split into sections in served order and the provider's ranking tables are dropped", () => {
  const sections = standingsSections([
    { group_name: "Group A", table_kind: "group", standing_rank: 1 },
    { group_name: "Group A", table_kind: "group", standing_rank: 2 },
    { group_name: "Group B", table_kind: "group", standing_rank: 1 },
    { group_name: "Ranking of third-placed teams", table_kind: "ranking", standing_rank: 1 },
  ]);
  assert.deepEqual(sections.map((s) => [s.name, s.kind, s.rows.length]), [
    ["Group A", "group", 2],
    ["Group B", "group", 1],
  ]);
});

test("the next round is the one the warehouse flagged, and nothing when none is", () => {
  assert.equal(nextRound([{ round: "Regular Season - 4", is_next_round: false },
                          { round: "Regular Season - 5", is_next_round: true }]).round, "Regular Season - 5");
  assert.equal(nextRound([{ round: "Regular Season - 34", is_next_round: false }]), null);
  assert.equal(nextRound(undefined), null);
});

test("boards file under their groups in the catalogue's order, the export's order within a group", () => {
  const boards = [
    { metric_key: "cards_yellow", metric_group: "discipline", rows: [{}] },
    { metric_key: "goals_per_match", metric_group: "goals", rows: [{}] },
    { metric_key: "goals_against_per_match", metric_group: "goals", rows: [{}] },
    { metric_key: "saves_pct", metric_group: "goalkeeping", rows: [] },
    { metric_key: "stray", metric_group: "no_such_group", rows: [{}] },
  ];
  const groups = boardGroups(boards, ["goals", "shooting", "discipline", "goalkeeping"]);
  assert.deepEqual(groups.map((g) => [g.key, g.boards.map((b) => b.metric_key)]), [
    ["goals", ["goals_per_match", "goals_against_per_match"]],
    ["discipline", ["cards_yellow"]],
  ], "an empty board makes no group, a group with no board is absent, an unlisted group is dropped");
  assert.deepEqual(boardGroups([], ["goals"]), []);
});

const summary = {
  matches_played: 27, total_goals: 104, goals_per_match: 3.85, home_wins: 14, away_wins: 8,
  drawn_matches: 5,
  biggest_margin: { fixture_id: 1, slug: "a", goals_home: 0, goals_away: 5, home: {}, away: {} },
  most_goals: { fixture_id: 2, slug: "b", goals_home: 3, goals_away: 4, home: {}, away: {} },
  longest_unbeaten_run: 3, longest_unbeaten_teams: [{ name: "Freiburg" }],
  longest_winless_run: 3, longest_winless_teams: [{ name: "Hamburg" }],
};

test("every served fact becomes one row, in the approved order", () => {
  assert.deepEqual(seasonFacts(summary).map((f) => f.key), [
    "goalsPerMatch", "homeWins", "biggestMargin", "mostGoals", "longestUnbeaten", "longestWinless",
  ]);
});

test("a null served value yields no row, and a missing summary no rows", () => {
  const keys = seasonFacts({ ...summary, home_wins: null, biggest_margin: null, longest_winless_teams: [] })
    .map((f) => f.key);
  assert.deepEqual(keys, ["goalsPerMatch", "mostGoals", "longestUnbeaten"]);
  assert.deepEqual(seasonFacts(null), []);
});
