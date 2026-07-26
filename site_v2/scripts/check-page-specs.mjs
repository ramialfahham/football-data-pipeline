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

/** Shape rules here are the hand-rolled equivalent of site_v2/src/specs/page-spec.schema.json --
 * see check-page-specs.test.mjs for the cross-check that keeps them from silently diverging. */
export function validateSpec(where, spec, martNames, i18nKeys, issues) {
  if (typeof spec.page !== "string" || !spec.page) {
    issues.push(`${where}: missing required string field "page"`);
  }
  if (!ENTITY_VALUES.has(spec.entity)) {
    issues.push(`${where}: "entity" must be one of ${[...ENTITY_VALUES].join(", ")}, got ${JSON.stringify(spec.entity)}`);
  }
  if (!Array.isArray(spec.blocks) || spec.blocks.length === 0) {
    issues.push(`${where}: "blocks" must be a non-empty array`);
    return;
  }
  spec.blocks.forEach((b, i) => {
    const label = b && typeof b.block === "string" ? b.block : `#${i}`;
    if (!b || typeof b.block !== "string" || !b.block) {
      issues.push(`${where}: blocks[${i}]: missing required string field "block"`);
    }
    const marts = Array.isArray(b?.mart) ? b.mart : b?.mart != null ? [b.mart] : [];
    if (marts.length === 0) {
      issues.push(`${where}: blocks[${i}] (${label}): missing required field "mart" (string or array of strings)`);
    }
    for (const mart of marts) {
      if (typeof mart !== "string" || !martNames.has(mart)) {
        issues.push(`${where}: blocks[${i}] (${label}): mart "${mart}" is not a real file under dbt_project/models/5_marts/**`);
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
  const martNames = collectMartNames();

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
    validateSpec(rel(specPath), spec, martNames, i18nKeys, issues);
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
