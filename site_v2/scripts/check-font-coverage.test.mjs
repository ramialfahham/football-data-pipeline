// Regression coverage for check-font-coverage.mjs, on the real font file and string literals.

import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { cmapCodePoints, compare, FONT, missing, visibleText, woff2Tables } from "./check-font-coverage.mjs";

const codePoints = cmapCodePoints(woff2Tables(readFileSync(FONT)).get("cmap"));

test("the font's character map holds the letters the site's three languages use", () => {
  for (const ch of "AZaz09äöüßÄÖÜåÅéçłńćčšžğı–·→▲▼‹›") assert.ok(codePoints.has(ch.codePointAt(0)), ch);
});

test("a control character is not in the font", () => {
  assert.ok(!codePoints.has(0x87));
});

test("visible text keeps text nodes, alt and placeholder, and drops scripts, styles and comments", () => {
  const html = '<p>Köln &amp; &#x2192; &#8212;</p><img alt="Ł"><input placeholder="ğ">'
    + "<script>const x = '中';</script><style>.a::after{content:'中'}</style><!-- 中 -->";
  const t = visibleText(html);
  for (const ch of ["Köln", "&", "→", "—", "Ł", "ğ"]) assert.ok(t.includes(ch), ch);
  assert.ok(!t.includes("中"));
});

test("a character the font lacks is counted per page", () => {
  const found = missing([{ path: "/a/", html: "<p>Urba\u0084ski \u0084</p>" }, { path: "/b/", html: "<p>\u0084 中</p>" }], codePoints);
  assert.deepEqual(found, { "/a/": { "U+0084": 2 }, "/b/": { "U+0084": 1, "U+4E2D": 1 } });
});

test("a count above its pin fails, below it asks for the pin to be lowered, equal passes", () => {
  const found = { "/a/": { "U+0084": 2 } };
  assert.deepEqual(compare(found, { "/a/": { "U+0084": 2 } }), []);
  assert.match(compare(found, { "/a/": { "U+0084": 1 } })[0], /^count rose · \/a\/ · U\+0084 · 2, baseline 1/);
  assert.match(compare(found, { "/a/": { "U+0084": 3 } })[0], /^count fell · \/a\/ · U\+0084 · 2, baseline 3/);
  assert.match(compare(found, { "/b/": { "U+0084": 2 } })[0], /^count rose · \/a\//);
  assert.match(compare({}, { "/b/": { "U+0087": 1 } })[0], /^count fell · \/b\//);
});
