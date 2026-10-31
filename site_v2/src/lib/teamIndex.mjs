// The Teams page's lists, cut from teams_index.json by the served orders. Nothing here ranks: a
// list is the served rows sorted by their served place, and rows sharing a place keep the export's
// order. The region listed first is the first in the served region order.

export const SHOWN = 6;
export const TOP_SHOWN = 10;
export const TOP_ALL = 20;

const byPlace = (key) => (a, b) => a[key] - b[key];

/** Rows that carry `key`, sorted by it; equal places keep their input order. */
export function ranked(rows, key) {
  return rows.filter((r) => r[key] != null).sort(byPlace(key));
}

/** Rows grouped by `key`, the groups in the served region order. */
export function byRegion(rows, key = "region_key") {
  const groups = new Map();
  for (const r of rows) {
    if (r[key] == null) continue;
    if (!groups.has(r[key])) {
      groups.set(r[key], { region: r[key], label: r.region_label_i18n_key, rank: r.region_rank, rows: [] });
    }
    groups.get(r[key]).rows.push(r);
  }
  return [...groups.values()].sort((a, b) => a.rank - b.rank);
}

const row = (team) => ({ kind: "row", team });
const head = (props) => ({ kind: "head", ...props });

/** A list cut at `shown` rows: the items before the cut, the items after it, and the row count.
 *  A heading goes with the first row it heads. */
export function cut(items, shown) {
  let rows = 0;
  let at = items.length;
  for (let i = 0; i < items.length; i++) {
    if (items[i].kind !== "row") continue;
    if (rows === shown) {
      at = i;
      while (at > 0 && items[at - 1].kind === "head") at--;
      break;
    }
    rows++;
  }
  const n = items.filter((i) => i.kind === "row").length;
  return { visible: items.slice(0, at), rest: items.slice(at), n };
}

/** Top clubs. All regions: the first region's top TOP_SHOWN shown, then its places up to TOP_ALL
 *  and each other region's top SHOWN under its name. A region: its own top list. */
export function topClubs(teams) {
  const regions = byRegion(ranked(teams.filter((t) => t.entity_type === "club"), "top_club_rank"));
  if (regions.length === 0) return { all: null, regions: [] };
  const [lead, ...others] = regions;
  const items = [
    ...lead.rows.slice(0, TOP_ALL).map(row),
    ...others.flatMap((g) => [head({ region: g.region, label: g.label }), ...g.rows.slice(0, SHOWN).map(row)]),
  ];
  return {
    all: cut(items, TOP_SHOWN),
    regions: regions.map((g) => ({
      region: g.region,
      list: cut(g.rows.slice(0, g === lead ? TOP_SHOWN : SHOWN).map(row), TOP_SHOWN),
    })),
  };
}

/** Top national teams. All regions: the world's top TOP_ALL, TOP_SHOWN shown. A region: all its
 *  teams, TOP_SHOWN shown. */
export function topNationalTeams(teams) {
  const national = teams.filter((t) => t.entity_type === "national");
  const world = ranked(national, "national_team_rank").slice(0, TOP_ALL);
  if (world.length === 0) return { all: null, regions: [] };
  return {
    all: cut(world.map(row), TOP_SHOWN),
    regions: byRegion(ranked(national, "national_team_region_rank")).map((g) => ({
      region: g.region,
      list: cut(g.rows.map(row), TOP_SHOWN),
    })),
  };
}

/** Clubs by country: one group per country in the served country order (countries sharing a place
 *  in the export's order); inside, the clubs in their served order under their covered league, then the others,
 *  headed "Other clubs" only when a league heading comes before them. */
export function clubsByCountry(teams) {
  const groups = new Map();
  for (const t of teams) {
    if (t.entity_type !== "club") continue;
    const key = t.team_country ?? "";
    if (!groups.has(key)) {
      groups.set(key, { country: t.team_country, order: t.country_order, region: t.country_region_key ?? "", rows: [] });
    }
    groups.get(key).rows.push(t);
  }
  return [...groups.values()]
    .sort(byPlace("order"))
    .map((g) => {
      const items = [];
      let league;
      for (const t of g.rows.sort(byPlace("team_order_in_country"))) {
        if (items.length === 0 ? t.league_code != null : t.league_code !== league) {
          items.push(head({ league: t.league_code ?? null }));
        }
        league = t.league_code;
        items.push(row(t));
      }
      return { country: g.country, region: g.region, n: g.rows.length, list: cut(items, SHOWN) };
    });
}

/** National teams by region: one group per region, in the served region order and places. */
export function nationalTeamsByRegion(teams) {
  return byRegion(ranked(teams.filter((t) => t.entity_type === "national"), "national_team_region_rank"))
    .map((g) => ({ region: g.region, label: g.label, n: g.rows.length, list: cut(g.rows.map(row), SHOWN) }));
}
