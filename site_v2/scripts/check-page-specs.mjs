#!/usr/bin/env node
// Page-spec contract checker (#826). Runs as `prebuild` (site_v2/package.json), so both real build
// paths (ci-site-v2.yml and deploy-site-v2.yml -- both invoke exactly `npm run build`) refuse to
// proceed if a real page has no spec, or its spec names a mart or i18n key that does not exist.
//
// Pure and stateless: reads site_v2/src/pages/**, site_v2/src/specs/**,
// dbt_project/models/5_marts/** (filenames only) and site_v2/src/i18n/strings.ts (text-scanned for
// the EN dict). Writes nothing, holds no lock, produces no artifact -- reruns and interruption are
// no-ops by construction.
//
// site_v2/src/specs/page-spec.schema.json is the authoritative, hand-written documentation of the
// spec shape (with editor autocomplete via each spec's "$schema" field) -- this checker does NOT
// load or interpret that file at runtime; it enforces the same rules by hand (the two real checks
// that matter, mart/i18n existence, are cross-repo-reference lookups no schema library performs
// anyway). check-page-specs.test.mjs cross-checks the schema file's required/enum fields against
// this file's hardcoded equivalents, so the two can't silently drift apart unnoticed.

import { readFileSync, readdirSync, statSync } from "node:fs";
import { join, relative, sep } from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

export const SITE_ROOT = join(fileURLToPath(new URL(".", import.meta.url)), "..");
export const REPO_ROOT = join(SITE_ROOT, "..");
export const PAGES_DIR = join(SITE_ROOT, "src", "pages");
export const SPECS_DIR = join(SITE_ROOT, "src", "specs");
export const MARTS_DIR = join(REPO_ROOT, "dbt_project", "models", "5_marts");
export const STRINGS_FILE = join(SITE_ROOT, "src", "i18n", "strings.ts");
export const SCHEMA_FILE = join(SITE_ROOT, "src", "specs", "page-spec.schema.json");

const LAYOUT_IMPORT_RE = /["'](?:\.\.\/)+layouts\/Layout\.astro["']/;
export const ENTITY_VALUES = new Set(["team", "player", "fixture", "competition", "home"]);

// --- the SEO gate's declaration half (#844) -------------------------------------------------
// This file checks that what a spec DECLARES exists. scripts/audit-seo.mjs checks that what the
// build EMITS matches it. Neither is sufficient alone: a declaration nothing verifies is a wish,
// and an output check with nothing to compare against has no expectation to hold the page to.
export const SEO_REQUIRED = [
  "canonical", "hreflang", "title", "description",
  "schema_org", "links", "minimum_data", "page_count_driver", "url_permanence",
];
export const CANONICAL_VALUES = new Set(["self"]);
export const HREFLANG_VALUES = new Set(["all-locales", "none"]);
export const URL_PERMANENCE_VALUES = new Set(["permanent", "ephemeral"]);
/** Allowed in `seo.title`/`seo.description` INSTEAD of an i18n key, and only on a stub: a scaffold
 * holds its handful of strings inline rather than leaving dead keys in all three dictionaries once
 * #367 deletes it. Anything else must be a real EN key, which is what forces a page's title through
 * t() — a concatenated title is locale-independent, and that is exactly how all three locales came
 * to ship byte-identical titles before this gate existed. */
export const INLINE_COPY = "inline";

/** Recursively list files under `dir` whose path passes `matches`. */
function walk(dir, matches, out = []) {
  for (const name of readdirSync(dir)) {
    const full = join(dir, name);
    const stat = statSync(full);
    if (stat.isDirectory()) {
      walk(full, matches, out);
    } else if (matches(name)) {
      out.push(full);
    }
  }
  return out;
}

function toPosix(p) {
  return p.split(sep).join("/");
}

export function rel(p) {
  return toPosix(relative(REPO_ROOT, p));
}

/** Mirror a page's path under src/specs: drop a leading "[lang]/" segment, strip [ ]
 * brackets from every remaining segment, swap .astro -> .spec.json. */
export function specPathFor(pageRelPosix) {
  let segments = pageRelPosix.split("/");
  if (segments[0] === "[lang]") segments = segments.slice(1);
  segments = segments.map((s) => s.replace(/[[\]]/g, ""));
  const last = segments.pop().replace(/\.astro$/, ".spec.json");
  segments.push(last);
  return join(SPECS_DIR, ...segments);
}

export function findRealPages() {
  const astroFiles = walk(PAGES_DIR, (name) => name.endsWith(".astro"));
  const real = [];
  for (const file of astroFiles) {
    const src = readFileSync(file, "utf8");
    if (LAYOUT_IMPORT_RE.test(src)) real.push(file);
  }
  return real;
}

export function collectMartNames() {
  const files = walk(MARTS_DIR, (name) => name.startsWith("mart_") && name.endsWith(".sql"));
  return new Set(files.map((f) => f.slice(f.lastIndexOf(sep) + 1).replace(/\.sql$/, "")));
}

// --- block SOURCE types (CPO ruling 2026-08-03) ----------------------------------------------
// A block's source is `type:name`; an unprefixed value means `mart:`, so every spec written
// before this ruling keeps working untouched.
//
// WHY THIS IS NOT A LOOSENING. The gate's guarantee is "nothing may be declared that does not
// exist", and every type below still resolves to a real thing on disk. What changed is that
// `mart` stopped being the only sayable answer, which it never truly was: the home page's browse
// block reads the COMPETITION REGISTRY, which the zero-file rule deliberately keeps out of the
// model layer (and which check_registry_var_sync.py exists to stop being duplicated), and its
// fixtures hero reads `core.fct_fixture`, the same source the shipped fixture page already uses.
// Before this, describing either honestly was impossible, and the only way to satisfy the checker
// was to copy the registry into a model -- breaking a rule to please a gate.
//
// ADDING A TYPE IS ONE ENTRY HERE. That is deliberate: the CPO's instruction was "a setup that is
// flexible enough to integrate whatever additional content". Note the scope of that flexibility:
// this is the VOCABULARY for naming a source, not the machinery for having one. A news or
// editorial surface would still need ingestion, storage and a page.
export const CORE_DIR = join(REPO_ROOT, "dbt_project", "models", "3_core");
export const SEEDS_DIR = join(REPO_ROOT, "dbt_project", "seeds");
export const REGISTRY_FILE = join(REPO_ROOT, "docs", "competition_registry.yml");

export const DEFAULT_SOURCE_TYPE = "mart";

/** type -> { describe, collect }. `collect` returns the Set of names that type accepts. */
export const SOURCE_TYPES = {
  mart: {
    describe: "a file under dbt_project/models/5_marts/**",
    collect: collectMartNames,
  },
  core: {
    describe: "a file under dbt_project/models/3_core/**",
    collect: () => {
      const files = walk(CORE_DIR, (name) => name.endsWith(".sql"));
      return new Set(files.map((f) => f.slice(f.lastIndexOf(sep) + 1).replace(/\.sql$/, "")));
    },
  },
  seed: {
    describe: "a .csv under dbt_project/seeds/",
    collect: () => {
      const files = walk(SEEDS_DIR, (name) => name.endsWith(".csv"));
      return new Set(files.map((f) => f.slice(f.lastIndexOf(sep) + 1).replace(/\.csv$/, "")));
    },
  },
  registry: {
    describe: "the competition registry (docs/competition_registry.yml)",
    // A single named file rather than a directory listing: the zero-file rule means there is
    // exactly ONE registry, and a second one appearing is a defect, not a new valid source.
    collect: () => new Set(statSyncSafe(REGISTRY_FILE) ? ["competition_registry"] : []),
  },
};

function statSyncSafe(path) {
  try {
    return statSync(path);
  } catch {
    return null;
  }
}

/** Every accepted name, per source type. Read once per run and passed into validateSpec. */
export function collectSourceNames() {
  return Object.fromEntries(
    Object.entries(SOURCE_TYPES).map(([type, def]) => [type, def.collect()]),
  );
}

/** Split `type:name` into its parts, defaulting the type. Returns null for a non-string. */
export function parseSource(value) {
  if (typeof value !== "string") return null;
  const at = value.indexOf(":");
  if (at === -1) return { type: DEFAULT_SOURCE_TYPE, name: value, raw: value };
  return { type: value.slice(0, at), name: value.slice(at + 1), raw: value };
}

/** Pure extraction, unit-testable without touching a real file: every key`: "` occurrence in a
 * flat (no nested objects) dict block. Several real keys are packed onto one line, comma-separated
 * (e.g. `squadGk: "Goalkeepers", squadDef: "Defenders",`) -- this must match every occurrence in
 * the block, not just the first token per line, or the tail keys on a packed line are missed
 * (a real bug caught while building this checker, not a hypothetical). Key names allow hyphens
 * too (`[A-Za-z0-9_-]+`), even though no key uses one today -- narrower would silently mis-parse
 * the day one does. */
export function extractKeysFromEnBlock(blockText) {
  const keys = new Set();
  for (const m of blockText.matchAll(/([A-Za-z0-9_-]+):\s*"/g)) keys.add(m[1]);
  return keys;
}

/** Text-scan strings.ts for the flat EN dict's keys -- it has no nested objects, so extracting the
 * `const EN: Dict = {...};` block's text and running extractKeysFromEnBlock over it is robust
 * without a real TS parser. */
export function collectEnI18nKeys() {
  const src = readFileSync(STRINGS_FILE, "utf8");
  const m = src.match(/\nconst EN: Dict = \{([\s\S]*?)\n\};/);
  if (!m) {
    return { keys: null, error: `could not locate "const EN: Dict = {...};" block in ${rel(STRINGS_FILE)}` };
  }
  const keys = extractKeysFromEnBlock(m[1]);
  // Self-check: a future reformat of strings.ts must not be able to silently zero out this
  // extraction and make every i18n_keys entry look "missing" instead of the real problem.
  const MIN_EXPECTED_KEYS = 50;
  if (keys.size < MIN_EXPECTED_KEYS) {
    return {
      keys: null,
      error: `extracted only ${keys.size} EN keys from ${rel(STRINGS_FILE)} (expected >= ${MIN_EXPECTED_KEYS}) -- the EN-block extraction regex likely broke on a strings.ts reformat, not that the file actually shrank`,
    };
  }
  // SECOND KEY CLASS (#370). A metric's display name is no longer a chrome string; it lives in
  // METRIC_LABELS_EN keyed by the catalogue's own `label_i18n_key`. A spec must still be able to
  // DECLARE that a block renders one, so those keys are collected too and validated the same way.
  // Without this, deleting the three hand-written `heroSot*` chrome strings makes `team.spec.json`'s
  // declaration unresolvable -- which is exactly how this gate caught the change.
  const mm = src.match(/\nconst METRIC_LABELS_EN: MetricLabels = \{([\s\S]*?)\n\};/);
  if (!mm) {
    return { keys: null, error: `could not locate "const METRIC_LABELS_EN: MetricLabels = {...};" block in ${rel(STRINGS_FILE)}` };
  }
  const metricKeys = new Set();
  for (const k of mm[1].matchAll(/"(metrics\.[A-Za-z0-9_]+\.label)":\s*"/g)) metricKeys.add(k[1]);
  // Its own floor, for the same reason as the one above: a quoted-dotted-key reformat must fail
  // loudly rather than make every declared metric label look missing.
  const MIN_EXPECTED_METRIC_KEYS = 15;
  if (metricKeys.size < MIN_EXPECTED_METRIC_KEYS) {
    return {
      keys: null,
      error: `extracted only ${metricKeys.size} metric label keys from ${rel(STRINGS_FILE)} (expected >= ${MIN_EXPECTED_METRIC_KEYS}) -- the METRIC_LABELS_EN extraction regex likely broke, not that the labels vanished`,
    };
  }
  for (const k of metricKeys) keys.add(k);
  return { keys, error: null };
}

export function readSpec(path, issues) {
  let raw;
  try {
    raw = readFileSync(path, "utf8");
  } catch {
    return null; // caller reports "missing spec"
  }
  let spec;
  try {
    spec = JSON.parse(raw);
  } catch (e) {
    issues.push(`${rel(path)}: not valid JSON (${e.message})`);
    return null;
  }
  return spec;
}

/** The SEO block (#844). Pure: takes the spec and the known EN keys, pushes issues.
 *
 * Every page BUILDS with an SEO surface declared, or it does not build — that is the CPO ruling
 * this implements ("SEO optimization has to be ensured during the whole process of building the
 * website"). A reviewer looking at finished pages cannot ensure anything. */
export function validateSeo(where, spec, i18nKeys, issues) {
  const seo = spec.seo;
  if (!seo || typeof seo !== "object" || Array.isArray(seo)) {
    issues.push(`${where}: missing required "seo" block — no page ships without declaring its search surface (#844)`);
    return;
  }
  for (const field of SEO_REQUIRED) {
    if (seo[field] === undefined) issues.push(`${where}: seo.${field} is required`);
  }
  if (seo.canonical !== undefined && !CANONICAL_VALUES.has(seo.canonical)) {
    issues.push(`${where}: seo.canonical must be one of ${[...CANONICAL_VALUES].join(", ")}, got ${JSON.stringify(seo.canonical)}`);
  }
  if (seo.hreflang !== undefined && !HREFLANG_VALUES.has(seo.hreflang)) {
    issues.push(`${where}: seo.hreflang must be one of ${[...HREFLANG_VALUES].join(", ")}, got ${JSON.stringify(seo.hreflang)}`);
  }
  if (seo.url_permanence !== undefined && !URL_PERMANENCE_VALUES.has(seo.url_permanence)) {
    issues.push(`${where}: seo.url_permanence must be one of ${[...URL_PERMANENCE_VALUES].join(", ")}, got ${JSON.stringify(seo.url_permanence)}`);
  }
  // An "ephemeral" URL is allowed — fixture URLs genuinely are one today (#861) — but saying so
  // without saying WHY turns a known defect into a shrug.
  if (seo.url_permanence === "ephemeral" && !seo.url_permanence_note) {
    issues.push(`${where}: seo.url_permanence is "ephemeral" — seo.url_permanence_note must say what breaks and which issue fixes it`);
  }
  for (const field of ["title", "description"]) {
    const value = seo[field];
    if (value === undefined) continue;
    if (typeof value !== "string" || !value) {
      issues.push(`${where}: seo.${field} must be a non-empty string`);
    } else if (value === INLINE_COPY) {
      if (spec.stub !== true) {
        issues.push(`${where}: seo.${field} may only be "${INLINE_COPY}" on a page with "stub": true — a real page's ${field} must be an i18n key, so it goes through t() and actually differs per locale`);
      }
    } else if (!i18nKeys.has(value)) {
      issues.push(`${where}: seo.${field} names i18n key "${value}", which does not exist in the EN dict (site_v2/src/i18n/strings.ts)`);
    }
  }
  const links = seo.links;
  if (links !== undefined) {
    if (!links || typeof links !== "object" || Array.isArray(links)) {
      issues.push(`${where}: seo.links must be an object with "inbound_hub" and "outbound"`);
    } else {
      if (typeof links.inbound_hub !== "string" || !links.inbound_hub) {
        issues.push(`${where}: seo.links.inbound_hub is required (use "none" to declare an orphan explicitly)`);
      }
      if (!Array.isArray(links.outbound)) {
        issues.push(`${where}: seo.links.outbound must be an array (possibly empty)`);
      }
    }
  }
}

/** Shape rules here are the hand-rolled equivalent of site_v2/src/specs/page-spec.schema.json --
 * see check-page-specs.test.mjs for the cross-check that keeps them from silently diverging. */
export function validateSpec(where, spec, sourceNames, i18nKeys, issues) {
  if (typeof spec.page !== "string" || !spec.page) {
    issues.push(`${where}: missing required string field "page"`);
  }
  if (!ENTITY_VALUES.has(spec.entity)) {
    issues.push(`${where}: "entity" must be one of ${[...ENTITY_VALUES].join(", ")}, got ${JSON.stringify(spec.entity)}`);
  }
  validateSeo(where, spec, i18nKeys, issues);

  // `stub: true` waives the non-empty-blocks rule and NOTHING else — a scaffold still ships a URL,
  // so its seo block is validated above exactly like any other page's.
  if (!Array.isArray(spec.blocks)) {
    issues.push(`${where}: "blocks" must be an array`);
    return;
  }
  if (spec.blocks.length === 0 && spec.stub !== true) {
    issues.push(`${where}: "blocks" must be a non-empty array (or declare "stub": true)`);
    return;
  }
  spec.blocks.forEach((b, i) => {
    const label = b && typeof b.block === "string" ? b.block : `#${i}`;
    if (!b || typeof b.block !== "string" || !b.block) {
      issues.push(`${where}: blocks[${i}]: missing required string field "block"`);
    }
    // A source is `type:name`, defaulting to `mart:` when unprefixed — see SOURCE_TYPES.
    const sources = Array.isArray(b?.mart) ? b.mart : b?.mart != null ? [b.mart] : [];
    if (sources.length === 0) {
      issues.push(`${where}: blocks[${i}] (${label}): missing required field "mart" (string or array of strings)`);
    }
    for (const raw of sources) {
      const parsed = parseSource(raw);
      if (parsed === null) {
        issues.push(`${where}: blocks[${i}] (${label}): source ${JSON.stringify(raw)} must be a string`);
        continue;
      }
      const known = SOURCE_TYPES[parsed.type];
      if (!known) {
        issues.push(
          `${where}: blocks[${i}] (${label}): source "${parsed.raw}" names an unknown type ` +
            `"${parsed.type}" (known: ${Object.keys(SOURCE_TYPES).join(", ")})`,
        );
        continue;
      }
      if (!sourceNames[parsed.type]?.has(parsed.name)) {
        issues.push(
          `${where}: blocks[${i}] (${label}): source "${parsed.raw}" is not ${known.describe}`,
        );
      }
    }
    if (b?.i18n_keys !== undefined) {
      if (!Array.isArray(b.i18n_keys)) {
        issues.push(`${where}: blocks[${i}] (${label}): "i18n_keys" must be an array of strings`);
      } else {
        for (const key of b.i18n_keys) {
          if (typeof key !== "string" || !i18nKeys.has(key)) {
            issues.push(`${where}: blocks[${i}] (${label}): i18n key "${key}" does not exist in the EN dict (site_v2/src/i18n/strings.ts)`);
          }
        }
      }
    }
  });
}

export function main() {
  const issues = [];

  const { keys: i18nKeys, error: i18nError } = collectEnI18nKeys();
  if (i18nError) {
    console.error(`check-page-specs: ${i18nError}`);
    process.exit(1);
  }
  const sourceNames = collectSourceNames();

  const realPages = findRealPages();
  if (realPages.length === 0) {
    // Almost certainly the Layout-import detection regex broke (e.g. Layout.astro moved), not
    // that every real page was actually removed -- fail loudly rather than silently "pass" on
    // zero pages checked (scope-auditor flagged this exact silent-regression shape).
    console.error(
      `check-page-specs: found 0 pages importing layouts/Layout.astro under ${rel(PAGES_DIR)}/** -- ` +
        "this almost certainly means the Layout-import detection broke, not that every real page " +
        "was removed. Aborting rather than silently validating nothing.",
    );
    process.exit(1);
  }

  for (const pageFile of realPages) {
    const pageRelPosix = toPosix(relative(PAGES_DIR, pageFile));
    const specPath = specPathFor(pageRelPosix);
    const spec = readSpec(specPath, issues);
    if (spec === null) {
      if (!issues.some((i) => i.startsWith(rel(specPath)))) {
        issues.push(`no spec found for page "${pageRelPosix}" -- expected ${rel(specPath)}`);
      }
      continue;
    }
    validateSpec(rel(specPath), spec, sourceNames, i18nKeys, issues);
  }

  if (issues.length > 0) {
    console.error(`check-page-specs: ${issues.length} page-spec violation(s):\n`);
    for (const issue of issues) console.error(`  - ${issue}`);
    console.error("\nSee docs/content_architecture.md and site_v2/src/specs/page-spec.schema.json.");
    process.exit(1);
  }

  console.log(`check-page-specs: ${realPages.length} page(s) validated against their specs. OK.`);
}

// Only run when executed directly (`node check-page-specs.mjs` / npm's prebuild) -- not when
// imported by check-page-specs.test.mjs. pathToFileURL normalizes Windows/POSIX argv[1] paths to
// the same file:// form as import.meta.url for a reliable comparison on both platforms.
if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  main();
}
