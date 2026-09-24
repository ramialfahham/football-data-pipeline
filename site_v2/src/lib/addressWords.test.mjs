import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { assertNoClash, translatePath, word, wordLanguages, WORDS } from "./addressWords.mjs";

test("word reads the table and throws on an unknown key or language", () => {
  assert.equal(word("de", "teams"), "mannschaften");
  assert.equal(word("fi", "stats"), "tilastot");
  assert.throws(() => word("de", "standing"));
  assert.throws(() => word("sv", "teams"));
});

test("every word is named in every language and none carries an umlaut", () => {
  const langs = wordLanguages();
  assert.deepEqual([...langs].sort(), ["de", "en", "fi"]);
  for (const [key, byLang] of Object.entries(WORDS)) {
    assert.deepEqual(Object.keys(byLang).sort(), [...langs].sort(), key);
    for (const w of Object.values(byLang)) assert.match(w, /^[a-z0-9-]+$/, `${key}: ${w}`);
  }
});

test("a key path translates to every language and back", () => {
  const cases = [
    ["teams/x/", { de: "mannschaften/x/", fi: "joukkueet/x/" }],
    ["players/p-1/", { de: "spieler/p-1/", fi: "pelaajat/p-1/" }],
    ["competitions/", { de: "wettbewerbe/", fi: "kilpailut/" }],
    ["bundesliga/matches/", { de: "bundesliga/spiele/", fi: "bundesliga/ottelut/" }],
    ["bundesliga/stats/", { de: "bundesliga/statistiken/", fi: "bundesliga/tilastot/" }],
    ["bundesliga/matches/m-1/", { de: "bundesliga/spiele/m-1/", fi: "bundesliga/ottelut/m-1/" }],
    ["*/matches/*/index.html", { de: "*/spiele/*/index.html", fi: "*/ottelut/*/index.html" }],
    ["bundesliga/", { de: "bundesliga/", fi: "bundesliga/" }],
    ["", { de: "", fi: "" }],
  ];
  for (const [en, byLang] of cases) {
    for (const [lang, localised] of Object.entries(byLang)) {
      assert.equal(translatePath(en, "en", lang), localised, `${en} -> ${lang}`);
      assert.equal(translatePath(localised, lang, "en"), en, `${localised} <- ${lang}`);
    }
  }
});

test("only the position decides: a name that spells a word elsewhere passes through", () => {
  assert.equal(translatePath("teams/matches/", "en", "de"), "mannschaften/matches/");
  assert.equal(translatePath("bundesliga/x/stats/", "en", "de"), "bundesliga/x/stats/");
  assert.equal(translatePath("teams/", "de", "en"), "teams/");
});

test("assertNoClash refuses a slug that equals a word in any language", () => {
  assert.doesNotThrow(() => assertNoClash(["bundesliga", "premier-league"]));
  assert.throws(() => assertNoClash(["bundesliga", "spiele"]), /spiele = matches \(de\)/);
  assert.throws(() => assertNoClash(["stats"]), /stats = stats \(en\)/);
});

test("today's committed competitions clash with no word", () => {
  const comps = JSON.parse(readFileSync(new URL("../data/competitions.json", import.meta.url), "utf8"));
  assertNoClash(Object.values(comps).map((c) => c.slug));
});
