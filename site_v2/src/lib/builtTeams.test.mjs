// Pins the list of team pages a build makes: the slug inside each payload of src/data/teams.

import { test } from "node:test";
import assert from "node:assert/strict";
import { mkdirSync, mkdtempSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { readBuiltTeams } from "./builtTeams.mjs";

test("every team payload is one built page, named by its served slug", () => {
  const dir = mkdtempSync(join(tmpdir(), "teams-"));
  mkdirSync(join(dir, "teams"));
  writeFileSync(join(dir, "teams", "108.json"), JSON.stringify({ slug: "bayern-munich" }));
  writeFileSync(join(dir, "teams", "157.json"), JSON.stringify({ slug: "germany" }));
  writeFileSync(join(dir, "teams", "notes.txt"), "not a payload");
  const built = readBuiltTeams(dir);
  assert.deepEqual([...built].sort(), ["bayern-munich", "germany"]);
  assert.equal(built.has("eritrea"), false, "a team with no payload has no page");
});

test("a build without team payloads makes no team page", () => {
  assert.equal(readBuiltTeams(mkdtempSync(join(tmpdir(), "teams-"))).size, 0);
});
