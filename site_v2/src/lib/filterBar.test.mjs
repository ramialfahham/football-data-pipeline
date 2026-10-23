// Pins the Filter bar's two choice rules: a filter offers only what its rows carry, in its own
// order, and a combination counts only when a row matches both filters.

import { test } from "node:test";
import assert from "node:assert/strict";
import { leavesARow, offered } from "./filterBar.mjs";

test("a filter offers only the values its rows carry, in the filter's order", () => {
  assert.deepEqual(offered(["UEFA", "CONMEBOL", "CAF", "OFC"], ["CAF", "UEFA", null, "UEFA"]), ["UEFA", "CAF"]);
  assert.deepEqual(offered(["club", "national"], ["club", "club"]), ["club"]);
});

test("a combination leaves a row only when one row matches both filters", () => {
  const rows = [{ entity: "club", region: "UEFA" }, { entity: "national", region: "OFC" }];
  assert.equal(leavesARow(rows, { entity: "club", region: "UEFA" }), true);
  assert.equal(leavesARow(rows, { entity: "club", region: "OFC" }), false);
});

test("an unset filter matches every row", () => {
  assert.equal(leavesARow([{ entity: "club", region: "AFC" }], { entity: "", region: "AFC" }), true);
});
