// The team pages this build makes: one per payload the export wrote to src/data/teams, the files
// the team route builds its pages from. A row links to a team only when the team's page is in this
// list.

import { readdirSync, readFileSync, existsSync } from "node:fs";
import { join } from "node:path";

/** The served slug of every team payload in `dataDir`/teams. */
export function readBuiltTeams(dataDir) {
  const dir = join(dataDir, "teams");
  if (!existsSync(dir)) return new Set();
  return new Set(
    readdirSync(dir)
      .filter((name) => name.endsWith(".json"))
      .map((name) => JSON.parse(readFileSync(join(dir, name), "utf8")).slug),
  );
}

let cached;

/** Whether this build makes the page at a served team slug. */
export function hasTeamPage(slug) {
  cached ??= readBuiltTeams(join(process.cwd(), "src/data"));
  return cached.has(slug);
}
