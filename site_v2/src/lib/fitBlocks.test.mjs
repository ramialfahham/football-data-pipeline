// Pins the decisions `fitBlocks.mjs` makes: a name's need is its longest word, never the whole
// name; a block keeps one line only when every row fits; and which lists of result rows it fits.

import { test } from "node:test";
import assert from "node:assert/strict";
import { RESULT_LISTS, fitsOneLine, longestWord } from "./fitBlocks.mjs";

const perLetter = (word) => word.length * 10;

test("a name needs the width of its longest word", () => {
  assert.equal(longestWord("Borussia Mönchengladbach", perLetter), 150);
  assert.equal(longestWord("  1. FC Union Berlin ", perLetter), 60);
});

test("an empty name needs nothing", () => {
  assert.equal(longestWord("", perLetter), 0);
});

test("a block keeps one line only when every row fits", () => {
  assert.equal(fitsOneLine([{ need: 100, room: 120 }, { need: 120, room: 120 }]), true);
  assert.equal(fitsOneLine([{ need: 100, room: 120 }, { need: 121, room: 120 }]), false);
});

test("half a pixel of rounding still fits", () => {
  assert.equal(fitsOneLine([{ need: 120.4, room: 120 }]), true);
});

test("a player's, a team's and a match's result lists take their form by fit; head to head and goals do not", () => {
  const parts = RESULT_LISTS.split(/,(?![^(]*\))/).map((s) => s.trim());
  assert.deepEqual(parts, [
    ".rlist.pm",
    ".rlist:has(.resrow:not(.meet, .goal, .scorer))",
    ".rsplit > .rcol:has(.resrow:not(.meet, .goal, .scorer))",
  ]);
});
