// Pins how a served round reads: its copy key in the page's language with the served number and
// group letter filled in; no key served is no name.

import { test } from "node:test";
import assert from "node:assert/strict";
import { roundName } from "./roundName.mjs";

const COPY = {
  de: { roundGroupStageMatchday: "{n}. Gruppenspieltag", roundFinal: "Finale" },
  fi: { roundGroupMatchday: "{g}-lohko, {n}. kierros" },
};
const t = (lang, key, vars = {}) =>
  COPY[lang][key].replace(/\{(\w+)\}/g, (_, k) => String(vars[k] ?? ""));

test("the served key reads in the page's language with its number and letter", () => {
  assert.equal(roundName(t, "de", "roundGroupStageMatchday", 3, null), "3. Gruppenspieltag");
  assert.equal(roundName(t, "fi", "roundGroupMatchday", 2, "A"), "A-lohko, 2. kierros");
});

test("a name without a number or letter reads as it is", () => {
  assert.equal(roundName(t, "de", "roundFinal", null, null), "Finale");
});

test("no served key is no name, never the provider's text", () => {
  assert.equal(roundName(t, "de", null, 6, null), null);
});
