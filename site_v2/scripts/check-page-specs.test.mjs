// Regression coverage for check-page-specs.mjs (#826 review finding: a CI gate whose own logic
// has zero test coverage can silently lose a check -- e.g. someone "simplifying" validateSpec --
// with nothing left to catch the regression this gate exists to prevent). Node's built-in test
// runner: zero new dependency, `node --test` (wired into `prebuild`, see package.json).

import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import {
  specPathFor,
  extractKeysFromEnBlock,
  validateSpec,
  collectEnI18nKeys,
  collectMartNames,
  ENTITY_VALUES,
  SCHEMA_FILE,
} from "./check-page-specs.mjs";

test("specPathFor mirrors the real page paths this repo has today", () => {
  assert.match(specPathFor("[lang]/teams/[team].astro").replace(/\\/g, "/"), /specs\/teams\/team\.spec\.json$/);
  assert.match(
    specPathFor("[lang]/[competition]/matches/[fixture].astro").replace(/\\/g, "/"),
    /specs\/competition\/matches\/fixture\.spec\.json$/,
  );
});

test("specPathFor only strips a LEADING [lang] segment; deeper brackets still stripped, extension still swapped", () => {
  assert.match(specPathFor("[competition]/index.astro").replace(/\\/g, "/"), /specs\/competition\/index\.spec\.json$/);
});

test("extractKeysFromEnBlock catches every key on a packed, comma-separated line", () => {
  // Regression lock for the real bug caught while building this checker: several EN keys are
  // packed onto one line (e.g. `squadGk: "Goalkeepers", squadDef: "Defenders",`), and a
  // line-anchored regex only caught the first.
  const fake = '  squadGk: "Goalkeepers", squadDef: "Defenders", squadMid: "Midfielders",\n  seasonToDate: "season to date",\n';
  const keys = extractKeysFromEnBlock(fake);
  assert.deepEqual([...keys].sort(), ["seasonToDate", "squadDef", "squadGk", "squadMid"]);
});

test("extractKeysFromEnBlock allows hyphenated key names", () => {
  const keys = extractKeysFromEnBlock('  some-key: "value",\n');
  assert.ok(keys.has("some-key"));
});

test("validateSpec: a well-formed spec produces no issues", () => {
  const issues = [];
  validateSpec(
    "fake.spec.json",
    { page: "x.astro", entity: "team", blocks: [{ block: "Team header", mart: "mart_team_profile", i18n_keys: ["founded"] }] },
    new Set(["mart_team_profile"]),
    new Set(["founded"]),
    issues,
  );
  assert.deepEqual(issues, []);
});

test("validateSpec: a block mart array with multiple marts validates each one", () => {
  const issues = [];
  validateSpec(
    "fake.spec.json",
    { page: "x.astro", entity: "team", blocks: [{ block: "Squad / roster", mart: ["mart_roster", "mart_player_career"] }] },
    new Set(["mart_roster", "mart_player_career"]),
    new Set(),
    issues,
  );
  assert.deepEqual(issues, []);
});

test("validateSpec: flags a missing required field", () => {
  const issues = [];
  validateSpec("fake.spec.json", { entity: "team", blocks: [{ block: "x", mart: "mart_x" }] }, new Set(["mart_x"]), new Set(), issues);
  assert.ok(issues.some((i) => i.includes('missing required string field "page"')));
});

test("validateSpec: flags an entity outside the enum", () => {
  const issues = [];
  validateSpec(
    "fake.spec.json",
    { page: "x.astro", entity: "nonsense", blocks: [{ block: "x", mart: "mart_x" }] },
    new Set(["mart_x"]),
    new Set(),
    issues,
  );
  assert.ok(issues.some((i) => i.includes('"entity" must be one of')));
});

test("validateSpec: flags a mart that is not a real file, naming the block and the bad value", () => {
  const issues = [];
  validateSpec(
    "fake.spec.json",
    { page: "x.astro", entity: "team", blocks: [{ block: "Upcoming / Results", mart: "mart_team_fixturezz" }] },
    new Set(["mart_team_fixtures"]),
    new Set(),
    issues,
  );
  assert.ok(issues.some((i) => i.includes("Upcoming / Results") && i.includes('mart "mart_team_fixturezz"')));
});

test("validateSpec: flags an i18n key that is not in the EN dict, naming the block and the bad key", () => {
  const issues = [];
  validateSpec(
    "fake.spec.json",
    { page: "x.astro", entity: "team", blocks: [{ block: "Vs-benchmark", mart: "mart_x", i18n_keys: ["median", "mediant"] }] },
    new Set(["mart_x"]),
    new Set(["median"]),
    issues,
  );
  assert.ok(issues.some((i) => i.includes("Vs-benchmark") && i.includes('i18n key "mediant"')));
  assert.ok(!issues.some((i) => i.includes('"median"')));
});

test("validateSpec: reports every violation in one pass, not just the first", () => {
  const issues = [];
  validateSpec(
    "fake.spec.json",
    {
      page: "x.astro",
      entity: "team",
      blocks: [
        { block: "A", mart: "mart_missing_1" },
        { block: "B", mart: "mart_x", i18n_keys: ["missingKey"] },
      ],
    },
    new Set(["mart_x"]),
    new Set(),
    issues,
  );
  assert.equal(issues.length, 2);
});

test("real EN dict extraction stays above the self-check floor (guards against a silent strings.ts reformat)", () => {
  const { keys, error } = collectEnI18nKeys();
  assert.equal(error, null);
  assert.ok(keys.size >= 50);
});

test("real mart directory has at least the marts both committed specs reference", () => {
  const marts = collectMartNames();
  for (const name of ["mart_team_profile", "mart_team_fixtures", "mart_roster", "mart_head_to_head"]) {
    assert.ok(marts.has(name), `expected ${name} to exist under dbt_project/models/5_marts/**`);
  }
});

test("page-spec.schema.json's required/enum fields match this checker's hardcoded equivalents", () => {
  // The runtime checker does not load this schema file (see its own top comment for why) -- this
  // is the automated cross-check that keeps the hand-written schema doc and the hand-rolled
  // checker from silently diverging (2026-07-26 review finding).
  const schema = JSON.parse(readFileSync(SCHEMA_FILE, "utf8"));
  assert.deepEqual(schema.required, ["page", "entity", "blocks"]);
  assert.deepEqual(new Set(schema.properties.entity.enum), ENTITY_VALUES);
  assert.deepEqual(schema.properties.blocks.items.required, ["block", "mart"]);
});
