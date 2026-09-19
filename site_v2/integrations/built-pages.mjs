// The Astro integration that runs the built-pages check as part of `astro build`, after the SEO
// audit: the site carries every unplayed match the warehouse holds, and the Matchdays tab keeps
// its invariants (scripts/check-built-pages.mjs says which). A child process, for the reasons
// integrations/seo-audit.mjs gives: a fresh heap and a script that stays directly runnable.

import { execFileSync } from "node:child_process";
import { fileURLToPath } from "node:url";
import { join } from "node:path";

export default function builtPages() {
  return {
    name: "built-pages",
    hooks: {
      "astro:build:done": ({ dir }) => {
        const script = join(fileURLToPath(new URL(".", import.meta.url)), "..", "scripts", "check-built-pages.mjs");
        try {
          execFileSync(process.execPath, [script, fileURLToPath(dir)], { stdio: "inherit" });
        } catch {
          throw new Error(
            "built-pages: the build does not carry what the warehouse holds, or a fixtures page breaks " +
              "its invariants (see the list above). The gate refuses the build rather than shipping it.",
          );
        }
      },
    },
  };
}
