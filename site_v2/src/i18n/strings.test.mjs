import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";

const HERE = dirname(fileURLToPath(import.meta.url));
const competitions = JSON.parse(readFileSync(join(HERE, "../data/competitions.json"), "utf8"));
const { t, inCompetition, playersInCompetition } = await import("./strings.ts");

const headNoun = (name) => name.replace(/ of .*$/, "").split(/[\s-]+/).pop();

test("German reads im before a Cup or Pokal and in der before every other competition", () => {
  for (const [code, { name }] of Object.entries(competitions)) {
    const article = ["Cup", "Pokal"].includes(headNoun(name)) ? "im" : "in der";
    assert.equal(inCompetition("de", code, name), `${article} ${name}`, code);
  }
});

test("English and Finnish name the competition without an article", () => {
  assert.equal(inCompetition("en", "DFBP", "DFB-Pokal"), "in DFB-Pokal");
  assert.equal(inCompetition("fi", "BL1", "Bundesliga"), "kilpailussa Bundesliga");
});

test("the Players to watch intro takes the Finnish inessive and reads as inCompetition elsewhere", () => {
  assert.equal(playersInCompetition("fi", "BL1", "Bundesliga"), "Bundesliigassa");
  assert.equal(playersInCompetition("fi", "PL", "Premier League"), "Valioliigassa");
  assert.equal(playersInCompetition("fi", "LMX", "Liga MX"), "kilpailussa Liga MX");
  assert.equal(playersInCompetition("en", "PL", "Premier League"), "in Premier League");
  assert.equal(playersInCompetition("de", "BL1", "Bundesliga"), "in der Bundesliga");
});

test("a placeholder used twice is filled twice", () => {
  const s = t("en", "formIntroPrev", { competition: "Bundesliga" });
  assert.ok(!s.includes("{competition}"), s);
  assert.equal(s.split("Bundesliga").length - 1, 2, s);
});
