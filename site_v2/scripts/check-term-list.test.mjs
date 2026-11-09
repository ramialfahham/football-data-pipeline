// One term list: one meaning has one key in strings.ts, and a component shows a term in the form
// `docs/design/components.yml` gives it. Runs in `npm test`, so a repeat or a wrong form fails the
// build. Parses the files as text: `node --test` cannot import `.ts`.

import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync, readdirSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join, relative } from "node:path";

const HERE = dirname(fileURLToPath(import.meta.url));
const SITE = join(HERE, "..");
const REPO = join(SITE, "..");
const strings = readFileSync(join(SITE, "src/i18n/strings.ts"), "utf8").replace(/\r\n/g, "\n");
const LOCALES = ["EN", "DE", "FI"];

function dict(loc) {
  const block = strings.match(new RegExp(`\\nconst ${loc}: Dict = \\{([\\s\\S]*?)\\n\\};`));
  assert.ok(block, `${loc} dictionary not found in strings.ts`);
  const noComments = block[1].replace(/^\s*\/\/.*$/gm, "");
  return new Map([...noComments.matchAll(/([A-Za-z0-9_]+):\s*"((?:[^"\\]|\\.)*)"/g)].map((m) => [m[1], m[2]]));
}
const dicts = Object.fromEntries(LOCALES.map((l) => [l, dict(l)]));

/** Keys a seed serves: renaming one needs a fresh export, so two may hold the same text. */
function servedKeys() {
  const text = ["round_names.csv", "competition_types.csv"]
    .map((s) => readFileSync(join(REPO, "dbt_project/seeds", s), "utf8")).join("\n");
  return new Set(text.match(/\b(?:round|compType|compFact)[A-Za-z0-9]+\b/g));
}

/** The words the term list retired, per language. A value holding one repeats a listed meaning. */
const RETIRED = {
  EN: [/\bStandings\b/, /\bFixtures\b/i, /\bUpcoming\b/, /\bseason before\b/i, /\bTBD\b/,
    /\bHeaviest\b/, /\bBiggest margin\b/, /\bDefence\b/, /\bMidfield\b/, /\bgoals plus assists\b/],
  DE: [/\bRemis\b/, /\bTorvorlage/, /\bGehaltene Schüsse\b/, /Überblick/, /\bSpielzeiten\b/, /\bletzte[nr]? Saison\b/,
    /\bTeams?\b/, /Teamwerte/, /\bKlubs?\b(?!-)/, /Kommende Spiele/, /Passspiel/, /Torwartspiel/, /Gruppenspieltag/,
    /\bAngriff\b/, /\bAbwehr\b/, /\bMittelfeld\b/, /Torschussdifferenz/],
  FI: [/Torjuntaosuus/, /\bedelliskau/, /Edellinen kausi/, /\bedelli(?:seen kauteen|sellä kaudella)\b/, /\bKokoonpano\b/,
    /\bper ottelu\b/, /per 90 min\b/, /Huippuseurat/, /Parhaat maajoukkueet/, /Tulevat ottelut/, /suorituskyk/i,
    /ranking-listoilla/, /tilasto kerrallaan/, /maalilaukausero/, /32 parhaan joukko/, /\bAvoin\b/],
};

test("every key stands in all three languages", () => {
  for (const loc of ["DE", "FI"]) {
    assert.deepEqual([...dicts[loc].keys()].sort(), [...dicts.EN.keys()].sort(), `${loc} keys differ from EN`);
  }
});

test("a short form has its full form", () => {
  const orphans = [...dicts.EN.keys()].filter((k) => k.endsWith("Short") && !dicts.EN.has(k.slice(0, -5)));
  assert.deepEqual(orphans, []);
});

test("one meaning has one key: no two keys hold the same text in every language", () => {
  const served = servedKeys();
  const seen = new Map();
  const repeats = [];
  for (const key of dicts.EN.keys()) {
    if (served.has(key)) continue;
    const text = LOCALES.map((l) => dicts[l].get(key)).join("\u0000");
    if (seen.has(text)) repeats.push(`${seen.get(text)} = ${key}`);
    else seen.set(text, key);
  }
  assert.deepEqual(repeats, []);
});

test("no text uses a word the term list retired", () => {
  const found = [];
  for (const loc of LOCALES) {
    for (const [key, value] of dicts[loc]) {
      if (RETIRED[loc].some((re) => re.test(value))) found.push(`${loc}.${key}: ${value}`);
    }
  }
  assert.deepEqual(found, []);
});

/** components.yml's files and short forms, read as text: one component per two-space key. */
function registry() {
  const text = readFileSync(join(REPO, "docs/design/components.yml"), "utf8").replace(/\r\n/g, "\n");
  const part = text.slice(text.indexOf("\ncomponents:"), text.indexOf("\nrules:"));
  return part.split(/\n(?= {2}[a-z-]+:\n)/).slice(1).map((c) => ({
    id: c.match(/^ {2}([a-z-]+):/)[1],
    files: [...(c.match(/^ {4}file: (.*)$/m)?.[1] ?? "").matchAll(/site_v2\/[^\s,\]"]+/g)].map((m) => m[0]),
    short: (c.match(/^ {4}short-forms: \[(.*)\]$/m)?.[1] ?? "").split(",").map((s) => s.trim()).filter(Boolean),
  }));
}

function sourceFiles(dir) {
  return readdirSync(dir, { withFileTypes: true }).flatMap((e) => {
    if (e.name === "data") return [];
    if (e.isDirectory()) return sourceFiles(join(dir, e.name));
    return /\.(astro|ts)$/.test(e.name) && e.name !== "strings.ts" ? [join(dir, e.name)] : [];
  });
}

test("the registry's short forms are terms that have one", () => {
  const missing = registry().flatMap((c) => c.short
    .filter((term) => !dicts.EN.has(`${term}Short`)).map((term) => `${c.id}: ${term}`));
  assert.deepEqual(missing, []);
});

test("a component reads a term in the form the registry gives it", () => {
  const comps = registry();
  const terms = [...dicts.EN.keys()].filter((k) => k.endsWith("Short")).map((k) => k.slice(0, -5));
  const wrong = [];
  for (const file of sourceFiles(join(SITE, "src"))) {
    const name = relative(REPO, file).replaceAll("\\", "/");
    const text = readFileSync(file, "utf8");
    const allowed = new Set(comps.filter((c) => c.files.includes(name)).flatMap((c) => c.short));
    for (const term of terms) {
      const readsShort = text.includes(`"${term}Short"`);
      const readsFull = new RegExp(`\\bt\\(lang,[^)]*"${term}"`).test(text);
      if (readsShort && !allowed.has(term)) wrong.push(`${name} reads ${term} short; the registry gives it in full`);
      if (readsFull && allowed.has(term) && !readsShort) wrong.push(`${name} reads ${term} in full; the registry gives it short`);
    }
  }
  assert.deepEqual(wrong, []);
});

test("every key a page asks for by name exists", () => {
  const unknown = sourceFiles(join(SITE, "src")).flatMap((file) =>
    [...readFileSync(file, "utf8").matchAll(/\bt\(lang,\s*"([A-Za-z0-9_]+)"/g)]
      .map((m) => m[1]).filter((k) => !dicts.EN.has(k))
      .map((k) => `${relative(SITE, file).replaceAll("\\", "/")}: ${k}`));
  assert.deepEqual(unknown, []);
});
