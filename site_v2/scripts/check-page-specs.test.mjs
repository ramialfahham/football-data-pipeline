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
  validateSeo,
  collectEnI18nKeys,
  collectMartNames,
  ENTITY_VALUES,
  SEO_REQUIRED,
  CANONICAL_VALUES,
  HREFLANG_VALUES,
  URL_PERMANENCE_VALUES,
  SCHEMA_FILE,
} from "./check-page-specs.mjs";

/** A minimal VALID seo block (#844), so the pre-existing validateSpec tests keep asserting what
 * they were written to assert instead of drowning in "seo is required". `title`/`description` name
 * i18n keys, which every caller below must include in its key set. */
const SEO_OK = {
  canonical: "self",
  hreflang: "all-locales",
  title: "seoTitleKey",
  description: "seoDescKey",
  schema_org: "SportsTeam",
  links: { inbound_hub: "competition", outbound: ["fixture"] },
  minimum_data: "one season row",
  page_count_driver: "count(teams) x count(locales)",
  url_permanence: "permanent",
};
const SEO_KEYS = ["seoTitleKey", "seoDescKey"];

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
    { page: "x.astro", entity: "team", seo: SEO_OK, blocks: [{ block: "Team header", mart: "mart_team_profile", i18n_keys: ["founded"] }] },
    new Set(["mart_team_profile"]),
    new Set(["founded", ...SEO_KEYS]),
    issues,
  );
  assert.deepEqual(issues, []);
});

test("validateSpec: a block mart array with multiple marts validates each one", () => {
  const issues = [];
  validateSpec(
    "fake.spec.json",
    { page: "x.astro", entity: "team", seo: SEO_OK, blocks: [{ block: "Squad / roster", mart: ["mart_roster", "mart_player_career"] }] },
    new Set(["mart_roster", "mart_player_career"]),
    new Set(SEO_KEYS),
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
      seo: SEO_OK,
      blocks: [
        { block: "A", mart: "mart_missing_1" },
        { block: "B", mart: "mart_x", i18n_keys: ["missingKey"] },
      ],
    },
    new Set(["mart_x"]),
    new Set(SEO_KEYS),
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
  assert.deepEqual(schema.required, ["page", "entity", "blocks", "seo"]);
  assert.deepEqual(new Set(schema.properties.entity.enum), ENTITY_VALUES);
  assert.deepEqual(schema.properties.blocks.items.required, ["block", "mart"]);
  // #844: the seo block's required set and every enum, cross-checked the same way. The previous
  // version of this test asserted only the top-level `required` and the entity enum, so a new
  // sub-object could drift from the checker unnoticed — which is the drift this test exists to stop.
  assert.deepEqual(schema.properties.seo.required, SEO_REQUIRED);
  assert.deepEqual(new Set(schema.properties.seo.properties.canonical.enum), CANONICAL_VALUES);
  assert.deepEqual(new Set(schema.properties.seo.properties.hreflang.enum), HREFLANG_VALUES);
  assert.deepEqual(new Set(schema.properties.seo.properties.url_permanence.enum), URL_PERMANENCE_VALUES);
  assert.deepEqual(schema.properties.seo.properties.links.required, ["inbound_hub", "outbound"]);
});

// --- the SEO gate's declaration half (#844) --------------------------------------------------

test("validateSeo: a well-formed block produces no issues", () => {
  const issues = [];
  validateSeo("fake.spec.json", { seo: SEO_OK }, new Set(SEO_KEYS), issues);
  assert.deepEqual(issues, []);
});

test("validateSeo: a page with NO seo block is refused — this is the whole point of #844", () => {
  const issues = [];
  validateSeo("fake.spec.json", { page: "x.astro" }, new Set(), issues);
  assert.equal(issues.length, 1);
  assert.match(issues[0], /missing required "seo" block/);
});

test("validateSeo: every required field is reported, not just the first", () => {
  const issues = [];
  validateSeo("fake.spec.json", { seo: {} }, new Set(), issues);
  for (const field of SEO_REQUIRED) {
    assert.ok(issues.some((i) => i.includes(`seo.${field} is required`)), `expected a complaint about seo.${field}`);
  }
});

test("validateSeo: title/description must be REAL i18n keys — a literal would not go through t()", () => {
  const issues = [];
  validateSeo("fake.spec.json", { seo: { ...SEO_OK, title: "Bayern — Stats" } }, new Set(SEO_KEYS), issues);
  assert.ok(issues.some((i) => i.includes('seo.title names i18n key "Bayern — Stats"')));
});

test('validateSeo: "inline" copy is allowed ONLY on a stub', () => {
  const onStub = [];
  validateSeo("fake.spec.json", { stub: true, seo: { ...SEO_OK, title: "inline", description: "inline" } }, new Set(), onStub);
  assert.deepEqual(onStub, []);

  const onRealPage = [];
  validateSeo("fake.spec.json", { seo: { ...SEO_OK, title: "inline" } }, new Set(SEO_KEYS), onRealPage);
  assert.ok(onRealPage.some((i) => i.includes('may only be "inline"')));
});

test('validateSeo: an "ephemeral" URL must say WHY — a known defect is not a shrug', () => {
  const withoutNote = [];
  validateSeo("fake.spec.json", { seo: { ...SEO_OK, url_permanence: "ephemeral" } }, new Set(SEO_KEYS), withoutNote);
  assert.ok(withoutNote.some((i) => i.includes("url_permanence_note")));

  const withNote = [];
  validateSeo(
    "fake.spec.json",
    { seo: { ...SEO_OK, url_permanence: "ephemeral", url_permanence_note: "destroyed after kickoff (#861)" } },
    new Set(SEO_KEYS),
    withNote,
  );
  assert.deepEqual(withNote, []);
});

test("validateSeo: enums are enforced", () => {
  for (const [field, bad] of [["canonical", "elsewhere"], ["hreflang", "some"], ["url_permanence", "maybe"]]) {
    const issues = [];
    validateSeo("fake.spec.json", { seo: { ...SEO_OK, [field]: bad } }, new Set(SEO_KEYS), issues);
    assert.ok(issues.some((i) => i.includes(`seo.${field} must be one of`)), `expected ${field} to be enum-checked`);
  }
});

test("validateSeo: links.inbound_hub is required so an orphan must be DECLARED, not omitted", () => {
  const issues = [];
  validateSeo("fake.spec.json", { seo: { ...SEO_OK, links: { outbound: [] } } }, new Set(SEO_KEYS), issues);
  assert.ok(issues.some((i) => i.includes("seo.links.inbound_hub is required")));
});

test("validateSpec: stub:true waives non-empty blocks and NOTHING else", () => {
  const stubOk = [];
  validateSpec("fake.spec.json", { page: "x.astro", entity: "home", stub: true, seo: SEO_OK, blocks: [] }, new Set(), new Set(SEO_KEYS), stubOk);
  assert.deepEqual(stubOk, []);

  // …but a stub with no seo block is still refused: a scaffold ships a real URL.
  const stubNoSeo = [];
  validateSpec("fake.spec.json", { page: "x.astro", entity: "home", stub: true, blocks: [] }, new Set(), new Set(), stubNoSeo);
  assert.ok(stubNoSeo.some((i) => i.includes('missing required "seo" block')));

  // …and a NON-stub with empty blocks is still refused.
  const notStub = [];
  validateSpec("fake.spec.json", { page: "x.astro", entity: "home", seo: SEO_OK, blocks: [] }, new Set(), new Set(SEO_KEYS), notStub);
  assert.ok(notStub.some((i) => i.includes('must be a non-empty array')));
});

test("every committed spec declares an seo block that validates against the REAL i18n dict", () => {
  // Not a fixture: the actual shipped specs. A spec can only name a title/description key that
  // really exists, which is what stops a template silently falling back to the key name.
  const { keys } = collectEnI18nKeys();
  for (const rel of ["teams/team.spec.json", "competition/matches/fixture.spec.json", "index.spec.json"]) {
    const spec = JSON.parse(readFileSync(new URL(`../src/specs/${rel}`, import.meta.url), "utf8"));
    const issues = [];
    validateSeo(rel, spec, keys, issues);
    assert.deepEqual(issues, [], `${rel}: ${issues.join(" | ")}`);
  }
});
