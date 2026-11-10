import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync, existsSync } from "node:fs";
import { join, dirname } from "node:path";
import { fileURLToPath } from "node:url";
import { worldsBest, nationGroups, nationPages, hubView, slotOf, codeOf } from "./playerIndex.mjs";
import { readBuiltPlayers } from "./builtPlayers.mjs";

const p = (over) => ({
  player_id: 1, slug: "a-player-1", name: "A Player", photo: null, position_group: "ATT",
  nation: "Spain", region_key: "UEFA", nation_order: 1, order_in_nation: 1, club: "Club",
  nation_slug: "spain", hub: true, hub_in_position: true, nation_page: false, ...over,
});

test("World's best: one list per position in the page's order, nominees by their served place", () => {
  const data = {
    players: [p({ player_id: 1, position_group: "GK" }), p({ player_id: 2 }), p({ player_id: 3 })],
    worlds_best: [
      { player_id: 1, list: "GK", order: 1 },
      { player_id: 3, list: "ATT", order: 1 },
      { player_id: 2, list: "ATT", order: 2 },
    ],
  };
  const lists = worldsBest(data);
  assert.deepEqual(lists.map((l) => l.group), ["ATT", "GK"]);
  assert.deepEqual(lists[0].rows.map((r) => r.player_id), [3, 2]);
});

test("a row's views follow the served flags", () => {
  assert.equal(hubView(p({})), "both");
  assert.equal(hubView(p({ hub_in_position: false })), "all");
  assert.equal(hubView(p({ hub: false })), "pos");
  assert.equal(hubView(p({ hub: false, hub_in_position: false })), null);
  assert.equal(slotOf("DEF"), 3);
  assert.equal(slotOf(null), 0);
  assert.equal(codeOf("GK"), "G");
});

test("nation groups keep the served order, count every player and hold only shown rows", () => {
  const data = {
    players: [
      p({ player_id: 3, nation: null, nation_slug: null, region_key: null, nation_order: 3 }),
      p({ player_id: 2, nation: "France", nation_slug: "france", nation_order: 2 }),
      p({ player_id: 12, order_in_nation: 2, position_group: "GK", nation_page: true }),
      p({ player_id: 11, nation_page: true }),
      p({ player_id: 13, order_in_nation: 3, hub: false, hub_in_position: false, nation_page: true }),
    ],
  };
  const groups = nationGroups(data);
  assert.deepEqual(groups.map((g) => g.nation), ["Spain", "France", null]);
  const spain = groups[0];
  assert.equal(spain.n, 3);
  assert.equal(spain.slug, "spain");
  assert.deepEqual(spain.rows.map((r) => r.player_id), [11, 12]);
  assert.deepEqual([...spain.perPosition], [[1, 2], [4, 1]]);
  assert.equal(groups[1].slug, null);
});

test("nation pages hold every player of a nation with a page, in the served order", () => {
  const data = {
    players: [
      p({ player_id: 13, order_in_nation: 3, hub: false, nation_page: true }),
      p({ player_id: 11, nation_page: true }),
      p({ player_id: 2, nation: "France", nation_slug: "france", nation_order: 2 }),
    ],
  };
  const pages = nationPages(data, ["a-player-1"]);
  assert.deepEqual(pages.map((x) => x.slug), ["spain"]);
  assert.deepEqual(pages[0].rows.map((r) => r.player_id), [11, 13]);
});

test("a nation page whose slug is a player page's slug, or not letters and hyphens, never builds", () => {
  const clash = { players: [p({ nation_page: true, nation_slug: "spain" })] };
  assert.throws(() => nationPages(clash, ["spain"]), /player page's slug/);
  const digits = { players: [p({ nation_page: true, nation_slug: "spain-1" })] };
  assert.throws(() => nationPages(digits, []), /letters and hyphens/);
});

test("the committed sample: no nation slug is a player slug, every player slug ends in its id or is it", () => {
  const dataDir = join(dirname(fileURLToPath(import.meta.url)), "..", "data");
  const file = join(dataDir, "players_index.json");
  if (!existsSync(file)) return;
  const data = JSON.parse(readFileSync(file, "utf8"));
  const players = [...readBuiltPlayers(dataDir).values()];
  for (const slug of players) assert.match(slug, /(^|-)\d+$/);
  assert.doesNotThrow(() => nationPages(data, players));
});
