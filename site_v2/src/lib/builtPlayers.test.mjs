// Pins the list of player pages a build makes: every player a Home or competition board links to,
// keyed by player id, with the served slug a squad row needs to link to the page.

import { test } from "node:test";
import assert from "node:assert/strict";
import { mkdirSync, mkdtempSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { readBuiltPlayers } from "./builtPlayers.mjs";

test("every board player is one built player page, keyed by player id", () => {
  const dir = mkdtempSync(join(tmpdir(), "players-"));
  writeFileSync(join(dir, "landing.json"), JSON.stringify({ top_players: [
    { rows: [{ player_id: 1, slug: "a-1" }, { player_id: 2, slug: "b-2" }] },
    { rows: [{ player_id: 1, slug: "a-1" }, { slug: "no-id" }] },
  ] }));
  mkdirSync(join(dir, "competitions", "BL1"), { recursive: true });
  writeFileSync(join(dir, "competitions", "BL1", "2026.json"), JSON.stringify({ player_boards: [
    { rows: [{ player_id: 3, slug: "c-3" }, { player_id: 2, slug: "b-2" }] },
  ] }));
  const built = readBuiltPlayers(dir);
  assert.deepEqual([...built.entries()], [[1, "a-1"], [2, "b-2"], [3, "c-3"]],
    "a player on two boards is one page; a row without an id links nowhere");
  assert.equal(built.has(4), false, "a player no board names has no page");
});

test("a build without boards makes no player page", () => {
  assert.equal(readBuiltPlayers(mkdtempSync(join(tmpdir(), "players-"))).size, 0);
});
