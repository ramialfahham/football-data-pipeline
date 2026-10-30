// The player pages this build makes: the players the Home and competition boards link to, which is
// the set the player route emits from the same two sources. A row links to a player only when the
// player's page is in this list, by the served slug.

import { readdirSync, readFileSync, existsSync } from "node:fs";
import { join } from "node:path";

/** player id -> the served slug, from landing.json's Top players and every competition payload's
 *  player boards. */
export function readBuiltPlayers(dataDir) {
  const built = new Map();
  const take = (row) => {
    if (row?.slug && row.player_id != null && !built.has(Number(row.player_id))) built.set(Number(row.player_id), row.slug);
  };
  const landing = join(dataDir, "landing.json");
  if (existsSync(landing)) {
    for (const board of JSON.parse(readFileSync(landing, "utf8")).top_players ?? []) for (const row of board.rows) take(row);
  }
  const comps = join(dataDir, "competitions");
  if (existsSync(comps)) {
    for (const code of readdirSync(comps)) {
      for (const file of readdirSync(join(comps, code)).filter((name) => name.endsWith(".json"))) {
        const payload = JSON.parse(readFileSync(join(comps, code, file), "utf8"));
        for (const board of payload.player_boards ?? []) for (const row of board.rows) take(row);
      }
    }
  }
  return built;
}

let cached;

export function builtPlayers() {
  cached ??= readBuiltPlayers(join(process.cwd(), "src/data"));
  return cached;
}
