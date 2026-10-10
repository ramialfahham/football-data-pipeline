// Regression coverage for how the two build checks are wired. `npm run build` is the only thing
// that runs them, so a build script without them ships an unchecked site while every other test
// stays green.

import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { join } from "node:path";
import { fileURLToPath } from "node:url";

const SITE_ROOT = join(fileURLToPath(new URL(".", import.meta.url)), "..");

test("npm run build runs astro build, then the SEO check, then the built-pages check, each only if the step before passed", () => {
  const { scripts } = JSON.parse(readFileSync(join(SITE_ROOT, "package.json"), "utf8"));
  assert.deepEqual(
    scripts.build.split("&&").map((step) => step.trim()),
    ["astro build", "node scripts/audit-seo.mjs", "node scripts/check-built-pages.mjs"],
  );
});

test("astro.config.mjs runs no check inside astro build", () => {
  const config = readFileSync(join(SITE_ROOT, "astro.config.mjs"), "utf8");
  assert.doesNotMatch(config, /from\s+["']\.\/integrations\//);
});
