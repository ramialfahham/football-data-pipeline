// The Players page's lists and the nation pages, cut from players_index.json by the served orders
// and flags. Nothing here ranks: a list is the served rows in their served place, and which rows the
// Players page shows and which nations have a page are the warehouse's flags.

/** The positions in the page's order: the filter slot, the position code the row's word uses and
 *  the plural the lists and the filter use. */
export const POSITIONS = [
  { group: "ATT", slot: 1, code: "F", label: "squadFwd" },
  { group: "MID", slot: 2, code: "M", label: "squadMid" },
  { group: "DEF", slot: 3, code: "D", label: "squadDef" },
  { group: "GK", slot: 4, code: "G", label: "squadGk" },
];
const BY_GROUP = new Map(POSITIONS.map((p) => [p.group, p]));

/** The filter slot of a position, 0 for a player with none. */
export const slotOf = (group) => BY_GROUP.get(group)?.slot ?? 0;
/** The position code a row's word is read by, or null. */
export const codeOf = (group) => BY_GROUP.get(group)?.code ?? null;

const NATION_SLUG = /^[a-z]+(-[a-z]+)*$/;

const byServed = (a, b) => a.nation_order - b.nation_order || a.order_in_nation - b.order_in_nation;

/** World's best: one list per position in the page's order, its nominees in their served place;
 *  a position without a nominee is absent. */
export function worldsBest(data) {
  const byId = new Map(data.players.map((p) => [p.player_id, p]));
  return POSITIONS.map((p) => ({
    ...p,
    rows: data.worlds_best
      .filter((w) => w.list === p.group)
      .sort((a, b) => a.order - b.order)
      .map((w) => byId.get(w.player_id))
      .filter(Boolean),
  })).filter((l) => l.rows.length > 0);
}

/** Which views of the Players page show a row: "all" with no position chosen, "pos" with its
 *  position chosen, "both", or null when neither. */
export function hubView(player) {
  if (player.hub && player.hub_in_position) return "both";
  if (player.hub) return "all";
  if (player.hub_in_position) return "pos";
  return null;
}

/** Players by nation: one group per nation in the served order, the players with no nation last.
 *  A group holds the rows the Players page shows in any view, its count of all its players, its
 *  count per position, and its page's slug when it has one. */
export function nationGroups(data) {
  const groups = new Map();
  for (const p of [...data.players].sort(byServed)) {
    const key = p.nation ?? "";
    if (!groups.has(key)) {
      groups.set(key, {
        nation: p.nation, region: p.region_key, slug: p.nation_page ? p.nation_slug : null,
        n: 0, perPosition: new Map(), rows: [],
      });
    }
    const g = groups.get(key);
    g.n += 1;
    const slot = slotOf(p.position_group);
    if (slot) g.perPosition.set(slot, (g.perPosition.get(slot) ?? 0) + 1);
    if (hubView(p)) g.rows.push(p);
  }
  return [...groups.values()];
}

/** The nation pages: one per nation the warehouse gives a page, its players in the served order.
 *  Throws when a slug is not letters and hyphens or is a player page's slug, so a clash with a
 *  player page can never build. */
export function nationPages(data, playerSlugs) {
  const pages = new Map();
  for (const p of [...data.players].sort(byServed)) {
    if (!p.nation_page) continue;
    if (!pages.has(p.nation_slug)) pages.set(p.nation_slug, { slug: p.nation_slug, nation: p.nation, region: p.region_key, rows: [] });
    pages.get(p.nation_slug).rows.push(p);
  }
  const taken = new Set(playerSlugs);
  for (const slug of pages.keys()) {
    if (!NATION_SLUG.test(slug ?? "")) throw new Error(`nation page slug "${slug}" is not letters and hyphens`);
    if (taken.has(slug)) throw new Error(`nation page slug "${slug}" is a player page's slug`);
  }
  return [...pages.values()];
}
