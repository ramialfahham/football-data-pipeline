// The match pages this build makes: one per payload in src/data/fixtures. Read once per build and
// shared, so the match route lists its pages from it and every match row decides from it whether
// its page exists. A row links only to a page in this list.

import { readdirSync, readFileSync } from "node:fs";
import { join } from "node:path";

/** fixture id -> the payload's file, slug, competition and whether the match is played. */
export function readBuiltFixtures(dir) {
  const built = new Map();
  for (const file of readdirSync(dir).filter((name) => name.endsWith(".json")).sort()) {
    const { fixture_id, slug, league_code, is_played } = JSON.parse(readFileSync(join(dir, file), "utf8"));
    built.set(Number(fixture_id), { file, slug, league_code, is_played: is_played === true });
  }
  return built;
}

let cached;

export function builtFixtures() {
  cached ??= readBuiltFixtures(join(process.cwd(), "src/data/fixtures"));
  return cached;
}
