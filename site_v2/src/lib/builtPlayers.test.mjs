// Pins the list of player pages a build makes: the export's player_pages.json, keyed by player id,
// with the served slug a row needs to link to the page.

import { test } from "node:test";
import assert from "node:assert/strict";
import { mkdtempSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { readBuiltPlayers } from "./builtPlayers.mjs";

test("every listed player is one built page, keyed by player id", () => {
  const dir = mkdtempSync(join(tmpdir(), "players-"));
  writeFileSync(join(dir, "player_pages.json"), JSON.stringify({ pages: { 1: "a-1", 2: "b-2" } }));
  const built = readBuiltPlayers(dir);
  assert.deepEqual([...built.entries()], [[1, "a-1"], [2, "b-2"]]);
  assert.equal(built.has(3), false, "a player the list does not name has no page");
});

test("a build without the list makes no player page", () => {
  assert.equal(readBuiltPlayers(mkdtempSync(join(tmpdir(), "players-"))).size, 0);
});
