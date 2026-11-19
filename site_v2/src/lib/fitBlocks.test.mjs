// Pins the decisions `fitBlocks.mjs` makes: a match row's name needs its longest word; a box's
// lines are counted once per line, whatever the size of its words; a block keeps one line only when
// every row fits; and which lists of result rows it fits.

import { test } from "node:test";
import assert from "node:assert/strict";
import { RESULT_LISTS, fitsOneLine, lineCount, longestWord, oneLineInside } from "./fitBlocks.mjs";

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

test("a smaller word on the same line counts as that line", () => {
  // a 15px name and an 11px "HOME" beside it, baseline-aligned
  assert.equal(lineCount([{ top: 100, bottom: 120 }, { top: 106, bottom: 118 }]), 1);
});

test("a word that wraps opens a second line", () => {
  assert.equal(lineCount([{ top: 100, bottom: 120 }, { top: 106, bottom: 118 }, { top: 120, bottom: 140 }]), 2);
});

test("a name on one line inside its box fits", () => {
  assert.equal(fitsOneLine(oneLineInside(1, 120, 120)), true);
});

test("a name that wraps does not fit", () => {
  assert.equal(fitsOneLine(oneLineInside(2, 100, 120)), false);
});

test("one unbreakable word that runs past its box does not fit, though it is one line", () => {
  assert.equal(fitsOneLine(oneLineInside(1, 140, 120)), false);
});

test("a box with no text takes no line", () => {
  assert.equal(lineCount([]), 0);
});

test("a player's, a team's and a match's result lists and head to head take their form by fit; goals do not", () => {
  const parts = RESULT_LISTS.split(/,(?![^(]*\))/).map((s) => s.trim());
  assert.deepEqual(parts, [
    ".rlist.pm",
    ".rlist:has(.resrow:not(.meet, .goal, .scorer))",
    ".rsplit > .rcol:has(.resrow:not(.meet, .goal, .scorer))",
    ".rlist:has(.resrow.meet:not(.goal))",
  ]);
});
