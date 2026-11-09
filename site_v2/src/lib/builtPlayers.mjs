// The player pages this build makes: player_pages.json, which the export writes beside the payloads
// from the warehouse's flag. The player route emits exactly these. A row links to a player only when
// the player's page is in this list.

import { readFileSync, existsSync } from "node:fs";
import { join } from "node:path";

/** player id -> the served slug. */
export function readBuiltPlayers(dataDir) {
  const path = join(dataDir, "player_pages.json");
  if (!existsSync(path)) return new Map();
  const pages = JSON.parse(readFileSync(path, "utf8")).pages;
  return new Map(Object.entries(pages).map(([id, slug]) => [Number(id), slug]));
}

let cached;

export function builtPlayers() {
  cached ??= readBuiltPlayers(join(process.cwd(), "src/data"));
  return cached;
}

let slugs;

/** Whether this build makes the page at a served slug. */
export function hasPlayerPage(slug) {
  slugs ??= new Set(builtPlayers().values());
  return slugs.has(slug);
}
