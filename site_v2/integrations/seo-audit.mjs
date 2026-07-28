// The Astro integration that runs the SEO audit as part of `astro build` (#844).
//
// WHY AN INTEGRATION AND NOT AN npm `postbuild` SCRIPT — the honest reason, because the plan's
// original one was wrong. The plan argued that `npm ci --ignore-scripts` skips pre/post hooks while
// still running the main script, yielding a complete `dist/` with no checks and exit 0. That npm
// behaviour is real, but NEITHER workflow in this repo passes `--ignore-scripts`, and both invoke
// exactly `npm run build` (never bare `astro build`) — so that bypass is not present here.
//
// The real reason is `astro:build:done`'s payload: it hands over `assets`, a Map keyed by each
// route's PATTERN, so a template's emitted-file count comes for free. That is the page-count driver
// a page spec declares, and a `dist/` walker cannot reconstruct it — once the files are on disk
// there is nothing left tying `/en/teams/foo/` back to `[lang]/teams/[team].astro`.
//
// The checker runs as a CHILD PROCESS: it gets a fresh heap (the audit streams a corpus measured in
// hundreds of MB, and the Astro build already needs --max-old-space-size=8192 at full scale), and it
// stays a plain, directly-runnable, unit-testable script rather than becoming integration-only code.

import { execFileSync } from "node:child_process";
import { fileURLToPath } from "node:url";
import { join } from "node:path";

export default function seoAudit() {
  return {
    name: "seo-audit",
    hooks: {
      "astro:build:done": ({ dir, assets, logger }) => {
        // The page-count driver, free from the hook payload: route pattern -> emitted file count.
        if (assets) {
          const counts = [...assets.entries()]
            .map(([pattern, files]) => `${pattern} -> ${files.length}`)
            .join(", ");
          logger.info(`page-count driver: ${counts}`);
        }

        const script = join(fileURLToPath(new URL(".", import.meta.url)), "..", "scripts", "audit-seo.mjs");
        try {
          // stdio inherit: the audit's own violation list is the error message. Wrapping it would
          // only hide which page failed.
          execFileSync(process.execPath, [script, fileURLToPath(dir)], { stdio: "inherit" });
        } catch {
          // The build has already written dist/ by this point. Throwing is what makes the FAILURE
          // real: `astro build` exits non-zero, so CI and the deploy workflow both stop.
          throw new Error(
            "seo-audit: the built site violates its own page specs (see the list above). " +
              "The gate refuses the build rather than shipping pages whose SEO surface is wrong (#844).",
          );
        }
      },
    },
  };
}
