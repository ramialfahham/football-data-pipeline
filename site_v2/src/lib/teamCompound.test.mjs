import { test } from "node:test";
import assert from "node:assert/strict";
import { teamBeforeCompound } from "./teamCompound.mjs";

test("a several-word team keeps the Finnish hyphen on its last word", () => {
  const out = teamBeforeCompound("fi", "Hertha BSC");
  assert.deepEqual([...out.slice("Hertha BSC".length)].map((c) => c.codePointAt(0)), [0x00a0, 0x2011]);
});

test("a one-word team and every other language are unchanged", () => {
  assert.equal(teamBeforeCompound("fi", "HJK"), "HJK-");
  assert.equal(teamBeforeCompound("en", "Hertha BSC"), "Hertha BSC");
  assert.equal(teamBeforeCompound("de", "HJK"), "HJK");
});
