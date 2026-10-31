import { test } from "node:test";
import assert from "node:assert/strict";
import { cut, topClubs, topNationalTeams, clubsByCountry, nationalTeamsByRegion } from "./teamIndex.mjs";

const REGIONS = { UEFA: 1, CONMEBOL: 2, CAF: 6 };

function club(name, region, over = {}) {
  return {
    team_name: name, team_slug: name.toLowerCase(), entity_type: "club", region_key: region,
    region_rank: REGIONS[region], region_label_i18n_key: `confed${region}`, team_country: "X",
    country_region_key: region, country_order: 1, league_code: null, team_order_in_country: 1,
    top_club_rank: null, national_team_rank: null, national_team_region_rank: null, crest: null, ...over,
  };
}

function national(name, region, world, inRegion) {
  return club(name, region, {
    entity_type: "national", team_country: name, country_region_key: null, country_order: null,
    team_order_in_country: null, national_team_rank: world, national_team_region_rank: inRegion,
  });
}

const names = (items) => items.filter((i) => i.kind === "row").map((i) => i.team.team_name);

test("a cut keeps a heading with the first row it heads", () => {
  const items = [{ kind: "head" }, ...[1, 2].map((n) => ({ kind: "row", team: { team_name: `a${n}` } })),
    { kind: "head" }, { kind: "row", team: { team_name: "b1" } }];
  const { visible, rest, n } = cut(items, 2);
  assert.equal(n, 3);
  assert.deepEqual(visible.map((i) => i.kind), ["head", "row", "row"]);
  assert.deepEqual(rest.map((i) => i.kind), ["head", "row"]);
});

test("top clubs: the first region's 10 shown, its 11-20 and each other region's 6 behind the fold", () => {
  // Input order is the export's (by name); the served places decide the list.
  const europe = Array.from({ length: 25 }, (_, i) => club(`E${String(25 - i).padStart(2, "0")}`, "UEFA", { top_club_rank: 25 - i }));
  const southAmerica = Array.from({ length: 8 }, (_, i) => club(`S${i + 1}`, "CONMEBOL", { top_club_rank: i + 1 }));
  const unranked = club("U", "UEFA");
  const { all, regions } = topClubs([...southAmerica, unranked, ...europe]);
  assert.deepEqual(names(all.visible), ["E01", "E02", "E03", "E04", "E05", "E06", "E07", "E08", "E09", "E10"]);
  assert.equal(all.n, 26);
  assert.deepEqual(all.rest.filter((i) => i.kind === "head").map((i) => i.region), ["CONMEBOL"]);
  assert.deepEqual(names(all.rest).slice(-6), ["S1", "S2", "S3", "S4", "S5", "S6"]);
  assert.deepEqual(regions.map((r) => [r.region, r.list.n, r.list.rest.length]), [["UEFA", 10, 0], ["CONMEBOL", 6, 0]]);
});

test("teams sharing a place keep the export's order", () => {
  const { all } = topClubs([club("Alpha", "UEFA", { top_club_rank: 2 }), club("Beta", "UEFA", { top_club_rank: 1 }),
    club("Gamma", "UEFA", { top_club_rank: 2 })]);
  assert.deepEqual(names(all.visible), ["Beta", "Alpha", "Gamma"]);
});

test("top national teams: the world's 20, 10 shown; a region lists all its teams", () => {
  const teams = Array.from({ length: 24 }, (_, i) => national(`N${i + 1}`, i % 2 ? "CAF" : "UEFA", i + 1, Math.floor(i / 2) + 1));
  const { all, regions } = topNationalTeams(teams);
  assert.equal(all.n, 20);
  assert.equal(names(all.visible).length, 10);
  assert.deepEqual(regions.map((r) => [r.region, r.list.n, names(r.list.visible).length]), [["UEFA", 12, 10], ["CAF", 12, 10]]);
});

test("clubs by country: served country order, leagues then Other clubs, 6 shown", () => {
  const teams = [
    club("Zed", "UEFA", { team_country: "Spain", country_order: 1, league_code: null, team_order_in_country: 8 }),
    ...Array.from({ length: 7 }, (_, i) => club(`P${i + 1}`, "UEFA", { team_country: "Spain", country_order: 1, league_code: "PD", team_order_in_country: i + 1 })),
    club("Only", "CAF", { team_country: "Sudan", country_order: 2 }),
  ];
  const [spain, sudan] = clubsByCountry(teams);
  assert.equal(spain.country, "Spain");
  assert.equal(spain.n, 8);
  assert.deepEqual(spain.list.visible.filter((i) => i.kind === "head").map((i) => i.league), ["PD"]);
  assert.deepEqual(spain.list.rest.map((i) => i.kind === "head" ? `head:${i.league}` : i.team.team_name), ["P7", "head:null", "Zed"]);
  assert.deepEqual(sudan.list.visible.map((i) => i.kind), ["row"], "no Other clubs heading without a league before it");
  assert.equal(sudan.region, "CAF");
});

test("countries sharing a place keep the export's order", () => {
  const groups = clubsByCountry([
    club("A", "UEFA", { team_country: "Portugal", country_order: 7 }),
    club("B", "UEFA", { team_country: "Österreich", country_order: 7 }),
    club("C", "UEFA", { team_country: "Spain", country_order: 1 }),
  ]);
  assert.deepEqual(groups.map((g) => g.country), ["Spain", "Portugal", "Österreich"]);
});

test("national teams by region: one group per region in the served region order", () => {
  const groups = nationalTeamsByRegion([national("A", "CAF", 3, 1), national("B", "UEFA", 1, 1), national("C", "UEFA", 2, 2)]);
  assert.deepEqual(groups.map((g) => [g.region, g.n, names(g.list.visible)]), [["UEFA", 2, ["B", "C"]], ["CAF", 1, ["A"]]]);
});
