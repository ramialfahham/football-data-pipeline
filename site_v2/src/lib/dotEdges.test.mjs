// Pins when a separator dot is hidden: only when it sits below the text before it, or has no text
// before it. The page's dots are wrapped by wholeWords.mjs (its own test).

import { test } from "node:test";
import assert from "node:assert/strict";
import { startsLine } from "./dotEdges.mjs";

test("a dot on the same line as the text before it stays", () => {
  assert.equal(startsLine([10, 24], [10, 24]), false);
});

test("a dot on a later line than the text before it is hidden", () => {
  assert.equal(startsLine([26, 40], [10, 24]), true);
});

test("a dot with no text before it is hidden", () => {
  assert.equal(startsLine([10, 24], null), true);
});

test("a dot a pixel lower than its neighbour's baseline still stays", () => {
  assert.equal(startsLine([11, 25], [10, 24]), false);
});
