// Pins the list of match pages a build makes: one entry per payload file, keyed by fixture id,
// with the slug and competition a row needs to link to it, and the played flag.

import { test } from "node:test";
import assert from "node:assert/strict";
import { mkdtempSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { readBuiltFixtures } from "./builtFixtures.mjs";

test("every payload is one built match page, keyed by its fixture id", () => {
  const dir = mkdtempSync(join(tmpdir(), "fixtures-"));
  writeFileSync(join(dir, "11.json"), JSON.stringify({ fixture_id: 11, slug: "a-vs-b", league_code: "BL1", is_played: true }));
  writeFileSync(join(dir, "12.json"), JSON.stringify({ fixture_id: 12, slug: "c-vs-d", league_code: "PL" }));
  writeFileSync(join(dir, "notes.txt"), "not a payload");
  const built = readBuiltFixtures(dir);
  assert.deepEqual([...built.keys()], [11, 12]);
  assert.deepEqual(built.get(11), { file: "11.json", slug: "a-vs-b", league_code: "BL1", is_played: true });
  assert.equal(built.get(12).is_played, false, "a next-match payload carries no played flag");
  assert.equal(built.has(13), false, "a match without a payload has no page");
});
