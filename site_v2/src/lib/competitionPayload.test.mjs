// Pins what the competition page does with its payload: the latest season wins, ranking tables
// are left out, the deserved boards are the two ends of the served order, and a null fact is no
// row — the rules that keep the page from showing an empty block or an older season by accident.

import { test } from "node:test";
import assert from "node:assert/strict";
import {
  deservedBoards,
  latestSeasonPayload,
  matchThatMatters,
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

test("the deserved boards are the served rank 1-3 and the three highest ranks, worse reversed", () => {
  const served = ["Mainz", "Union", "Leverkusen", "Köln", "Bremen", "Freiburg", "Schalke", "Dortmund"]
    .map((name, i) => ({ name, deserved_points: 5, deserved_points_gap: i - 3, deserved_points_gap_rank: i + 1 }));
  const boards = deservedBoards(served);
  assert.deepEqual(boards.better.map((r) => r.name), ["Mainz", "Union", "Leverkusen"]);
  assert.deepEqual(boards.worse.map((r) => r.name), ["Dortmund", "Schalke", "Freiburg"]);
});

test("no deserved boards unless at least two rows carry a served rank", () => {
  assert.equal(deservedBoards([{ name: "A", deserved_points: 1, deserved_points_gap: 0, deserved_points_gap_rank: 1 }]), null);
  assert.equal(deservedBoards([{ name: "A", deserved_points: null, deserved_points_gap: null, deserved_points_gap_rank: null },
                               { name: "B", deserved_points: null, deserved_points_gap: null, deserved_points_gap_rank: null }]), null);
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

test("the match that matters is the flagged fixture, and nothing when none is flagged", () => {
  assert.equal(matchThatMatters([{ fixture_id: 1 }, { fixture_id: 2, is_match_that_matters: true }]).fixture_id, 2);
  assert.equal(matchThatMatters([{ fixture_id: 1, is_match_that_matters: false }]), null);
});
