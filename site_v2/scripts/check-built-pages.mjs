// The built-pages check: proof, on every build, that the site carries what the warehouse holds
// and that the Matchdays tab keeps its two invariants. `npm run build` runs it after `astro build`
// and the SEO audit, and it is directly runnable:
//
//   node scripts/check-built-pages.mjs [distDir] [dataDir]
//
// 1. Every match the export carries has a page. The emitted match pages equal the fixture payloads
//    times the locales, and when the export's manifest is present (a full export; the committed
//    sample carries none) the payloads written equal the unplayed and the played fixtures the
//    warehouse held when the export ran. A sampled export therefore fails a full build, by design.
// 2. On every fixtures page exactly one round is checked on load, and it is the round the
//    warehouse flagged next whenever one is flagged; every unplayed row is a link. On every page,
//    a row that names its match (`data-fixture`) is a link exactly when that match has a payload,
//    and a build with match payloads has at least one such row. On a full export (the manifest is
//    present) every row of a fixtures page has a match payload, played or not, whatever its status.
// 3. On every Rankings page (at the stats word) every board keeps the board rules: one to five rows,
//    every row a link, the boards the payload served and no others, and no zero on a most-first
//    board (a zero is not a ranking there; on a fewest-first board it is the top). Nothing on the
//    page names its direction, so the directions come from the payload, grouped the way the page
//    groups the boards — `boardGroups`, the function the block renders from.
// 4. On every Team page each "Compared with the league" row (`data-metric`) shows the rank the
//    team payload's featured season serves for that metric, through `ordinal`, the function the
//    block renders it with. A less-is-better metric is already ranked lowest-first by the warehouse,
//    so a page that flips it a second time fails.
// 5. On every Team page, in each deserved points scatter, the difference label and the team's name
//    stay apart: the label on the other side of the team's dot, anchored the other way, or on the
//    name's side at least one line under the name.
// 6. Every image a built page names comes from our own origin. An `<img>` or `<source>` address, an
//    `og:image` or `twitter:image` address and a JSON-LD `image` or `logo` address that names another
//    host is counted by kind (a provider player or coach photo, a provider crest or
//    logo, any other host) and held to `IMAGE_PINS`, a ceiling per kind that only goes down. A pin at
//    0 holds on every build. A pin above 0 holds on a build of the committed sample (no manifest) and
//    is only reported on a full export. The change that removes a kind lowers its pin to 0.
//
// The parsing is regex over the emitted HTML, as audit-seo does it: the shapes are this repo's own
// components, and the pure functions below are unit-tested on string literals.

import { existsSync, readdirSync, readFileSync } from "node:fs";
import { join } from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";
import { readDist } from "./audit-seo.mjs";
import { boardGroups } from "../src/lib/competitionPayload.mjs";
import { word } from "../src/lib/addressWords.mjs";
import { ordinal } from "../src/lib/format.ts";

export const SITE_ROOT = join(fileURLToPath(new URL(".", import.meta.url)), "..");
export const DIST_DIR = join(SITE_ROOT, "dist");
export const DATA_DIR = join(SITE_ROOT, "src", "data");
export const LOCALES = ["de", "en", "fi"];

/** A competition tab's path shape, each locale paired with its own spelling of the address word. */
function tabPath(key, tail) {
  const alts = LOCALES.map((l) => `${l}/[^/]+/${word(l, key)}`).join("|");
  return new RegExp(`^/(?:${alts})/${tail}$`);
}

export const MATCH_PAGE = tabPath("matches", "[^/]+/");
export const FIXTURES_PAGE = tabPath("matches", "");
export const RANKINGS_PAGE = tabPath("stats", "");
export const TEAM_PAGE = new RegExp(`^/(?:${LOCALES.map((l) => `${l}/${word(l, "teams")}`).join("|")})/[^/]+/$`);
export const BOARD_ROWS_MAX = 5;

/** Issues for the match-page count against the payloads written and, when present, the manifest. */
export function checkMatchPageCount({ matchPages, payloadFiles, manifest = null, locales = LOCALES }) {
  const issues = [];
  const expected = payloadFiles * locales.length;
  if (matchPages !== expected) {
    issues.push(
      `match pages: ${matchPages} emitted, ${expected} expected (${payloadFiles} fixture payload(s) x ${locales.length} locales)`,
    );
  }
  if (manifest) {
    const written = manifest.counts?.fixture ?? 0;
    const unplayed = manifest.source_counts?.fixtures_unplayed;
    const played = manifest.source_counts?.fixtures_played;
    // More files than written is the committed sample sitting beside a full export, not a gap.
    if (payloadFiles < written) {
      issues.push(`manifest: ${written} fixture payload(s) written, only ${payloadFiles} on disk`);
    }
    if (unplayed === undefined || played === undefined) {
      issues.push("manifest: no source count of unplayed and played fixtures, so the build cannot prove it carries them all");
    } else if (unplayed + played !== written) {
      issues.push(
        `manifest: the warehouse held ${unplayed} unplayed and ${played} played fixture(s), the export wrote ${written}`,
      );
    }
  }
  return issues;
}

const RE = {
  round: /<div class="md" data-md="[^"]*">/g,
  radio: /<input class="md-in"[^>]*>/g,
  checked: /\schecked(?:=""|\s|>)/,
  nexttag: /class="nexttag"/,
  // Attributes in any order: Astro emits the linked row as <a href="…" class="fxrow">.
  row: /<(a|div)(\s[^>]*)>/g,
  rowClass: /\sclass="fxrow( played)?"/,
  href: /\shref="[^"]+"/,
};

/** Split a fixtures page into its rounds, each the HTML from one `.md` wrapper to the next. */
export function rounds(html) {
  const starts = [...html.matchAll(RE.round)].map((m) => m.index);
  return starts.map((s, i) => html.slice(s, starts[i + 1] ?? html.length));
}

/** Issues on one fixtures page: the checked round and the row links. A played row links to its
 * match page when the build makes one; audit-seo fails a link to a page that is not built. */
export function checkFixturesPage(html, path = "") {
  const issues = [];
  const rs = rounds(html);
  if (rs.length === 0) {
    issues.push(`${path}: no round on the page`);
    return issues;
  }
  const checked = rs.filter((r) => RE.checked.test(r.match(RE.radio)?.[0] ?? ""));
  if (checked.length !== 1) {
    issues.push(`${path}: ${checked.length} round(s) checked on load, expected exactly 1`);
  }
  const flagged = rs.filter((r) => RE.nexttag.test(r));
  if (flagged.length > 1) issues.push(`${path}: ${flagged.length} rounds carry the Next tag`);
  if (flagged.length === 1 && checked.length === 1 && flagged[0] !== checked[0]) {
    issues.push(`${path}: the checked round is not the round flagged next`);
  }
  for (const m of html.matchAll(RE.row)) {
    const [, tag, attrs] = m;
    const cls = attrs.match(RE.rowClass);
    if (!cls) continue;
    const played = Boolean(cls[1]);
    const isLink = tag === "a" && RE.href.test(attrs);
    if (!played && !isLink) issues.push(`${path}: an unplayed row is not a link`);
  }
  return [...new Set(issues)];
}

const ROW_RE = /<(a|div)((?:\s[^>]*)?\sdata-fixture="(\d+)"[^>]*)>/g;

/** The rows on one page that name their match, `data-fixture` in any attribute position. */
export function matchRows(html) {
  return [...html.matchAll(ROW_RE)];
}

/** Issues on one page: a row naming a match with a payload that is not a link, or a row linking to
 *  a match with none. */
export function checkMatchRowLinks(html, built, path = "") {
  const issues = [];
  for (const [, tag, attrs, id] of matchRows(html)) {
    const isLink = tag === "a" && RE.href.test(attrs);
    const has = built.has(Number(id));
    if (has && !isLink) issues.push(`${path}: the row of match ${id} is not a link, though its page is built`);
    if (!has && isLink) issues.push(`${path}: the row of match ${id} links, though it has no page`);
  }
  return issues;
}

/** Issues on one fixtures page of a full export: a row whose match has no payload. The committed
 *  sample carries the payloads of a few played matches only, so main runs this when the export's
 *  manifest is present. */
export function checkFixturesPayloads(html, built, path = "") {
  const issues = [];
  for (const [, , , id] of matchRows(html)) {
    if (!built.has(Number(id))) issues.push(`${path}: the row of match ${id} has no match payload`);
  }
  return issues;
}

const BOARD_RE = {
  board: /<div class="board">/g,
  name: /<span class="bt"><span class="nm">([^<]*)<\/span>/,
  row: /<(a|div)(\s[^>]*)class="ctab-row"([^>]*)>/g,
  value: /<span class="n num pts">([^<]*)<\/span>/g,
};

/** Split a Rankings page into its boards, each the HTML from one `.board` wrapper to the next. */
export function boards(html) {
  const starts = [...html.matchAll(BOARD_RE.board)].map((m) => m.index);
  return starts.map((s, i) => html.slice(s, starts[i + 1] ?? html.length));
}

/** A rendered value that reads as zero in any locale: "0", "0.0", "0,0", "0%", "0 %". */
export function isZeroValue(text) {
  const digits = text.replace(/[^0-9]/g, "");
  return digits.length > 0 && /^0+$/.test(digits);
}

/** Issues on one Rankings page: the board rules, read from the emitted boards. `expected.ascending`
 *  is the payload's rank order for each board, in the order the page renders them, so the page is
 *  held to the data it was built from. The zero rule needs a direction and the page states none,
 *  so without `expected` only the row rules are checked. */
export function checkRankingsPage(html, path = "", expected = null) {
  const issues = [];
  const bs = boards(html);
  if (bs.length === 0) {
    issues.push(`${path}: no board on the page`);
    return issues;
  }
  const directions = expected?.ascending ?? null;
  if (directions && bs.length !== directions.length) {
    issues.push(`${path}: ${bs.length} board(s) on the page, the payload served ${directions.length}`);
  }
  bs.forEach((b, i) => {
    const name = b.match(BOARD_RE.name)?.[1]?.trim() ?? "(unnamed board)";
    const rows = [...b.matchAll(BOARD_RE.row)];
    if (rows.length === 0 || rows.length > BOARD_ROWS_MAX) {
      issues.push(`${path}: board "${name}" has ${rows.length} row(s), expected 1 to ${BOARD_ROWS_MAX}`);
    }
    for (const [, tag, before, after] of rows) {
      if (tag !== "a" || !RE.href.test(before + after)) issues.push(`${path}: a row of "${name}" is not a link`);
    }
    if (directions?.[i] === false) {
      for (const [, value] of b.matchAll(BOARD_RE.value)) {
        if (isZeroValue(value)) issues.push(`${path}: board "${name}" ranks a zero (${value.trim()}) on a most-first board`);
      }
    }
  });
  return [...new Set(issues)];
}

/** The catalogue's group keys in the catalogue's order, from the exported copy the site renders
 *  from — the same order `GROUP_KEYS_IN_ORDER` gives the block. */
export function groupKeysInOrder(dataDir = DATA_DIR) {
  const file = join(dataDir, "metric_groups.json");
  if (!existsSync(file)) return [];
  return [...JSON.parse(readFileSync(file, "utf8")).groups].sort((a, b) => a.order - b.order).map((g) => g.key);
}

/** A competition payload's boards in the order the Rankings page renders them: the two blocks in
 *  turn, each grouped by `boardGroups` — the function the block itself renders from, so the order
 *  is the page's and not a second guess at it. */
export function renderedBoards(payload, groupKeys) {
  return [payload.team_boards, payload.player_boards]
    .flatMap((list) => boardGroups(list, groupKeys).flatMap((group) => group.boards));
}

/** What each competition's latest payload served for its Rankings page, by slug: `ascending[i]` is
 *  whether the i-th board the page renders ranks ascending. */
export function expectedBoards(dataDir = DATA_DIR) {
  const dir = join(dataDir, "competitions");
  const latest = new Map();
  if (!existsSync(dir)) return latest;
  const keys = groupKeysInOrder(dataDir);
  for (const code of readdirSync(dir)) {
    const seasons = readdirSync(join(dir, code)).filter((f) => f.endsWith(".json")).sort();
    if (!seasons.length) continue;
    const p = JSON.parse(readFileSync(join(dir, code, seasons[seasons.length - 1]), "utf8"));
    if (p.slug) {
      latest.set(p.slug, {
        ascending: renderedBoards(p, keys).map((b) => b.rank_order === "asc"),
        hasFixtures: Boolean(p.fixtures?.length),
      });
    }
  }
  return latest;
}

const TEAM_RE = {
  row: /<div(?=[^>]*\sclass="rs-row[ "])[^>]*>/g,
  panel: /<div(?=[^>]*\sclass="cmp-p")(?=[^>]*\sdata-league="([^"]*)")[^>]*>/g,
  metric: /\sdata-metric="([^"]*)"/,
  rank: /<span class="rs-val">([^<]*)<small>/,
};

/** The league rows on one Team page, each with its metric, the rank it shows, and the league of the
 *  panel it stands in (null outside a panel). A row is the HTML from one `.rs-row` wrapper to the next. */
export function teamRankRows(html) {
  const starts = [...html.matchAll(TEAM_RE.row)];
  const panels = [...html.matchAll(TEAM_RE.panel)];
  return starts.map((m, i) => ({
    metric: m[0].match(TEAM_RE.metric)?.[1] ?? null,
    shown: html.slice(m.index, starts[i + 1]?.index ?? html.length).match(TEAM_RE.rank)?.[1]?.trim() ?? null,
    league: panels.filter((p) => p.index < m.index).pop()?.[1] ?? null,
  }));
}

/** Issues on one Team page: each row's shown rank against `served`, the rank by metric key from the
 *  payload the page was built from. A row in a competition's panel reads `{league}:{metric}`, any
 *  other row the featured season's `{metric}`. */
export function checkTeamPage(html, lang, served, path = "") {
  const issues = [];
  for (const { metric, shown, league } of teamRankRows(html)) {
    const key = league ? `${league}:${metric}` : metric;
    if (!metric) {
      issues.push(`${path}: a league row names no metric with data-metric`);
    } else if (!served?.has(key)) {
      issues.push(`${path}: the league row of ${metric} has no served rank in the team payload`);
    } else if (shown !== ordinal(served.get(key), lang)) {
      issues.push(`${path}: the league row of ${metric} shows ${shown ?? "no rank"}, the payload serves ${ordinal(served.get(key), lang)}`);
    }
  }
  return issues;
}

const SCATTER_RE = {
  chart: /<svg class="dp-chart[ "]/g,
  me: /<circle class="chart-dot chart-me"[^>]*>/,
  note: /<text[^>]*\sdata-role="gap"[^>]*>/,
  name: /<text[^>]*\sdata-role="name"[^>]*>/,
};
const attr = (tag, name) => tag?.match(new RegExp(`\\s${name}="([^"]*)"`))?.[1] ?? null;
const em = (tag, name) => parseFloat(attr(tag, name) ?? "0");
const textMark = (tag) =>
  tag && { x: Number(attr(tag, "x")), dx: em(tag, "dx"), dy: em(tag, "dy"), anchor: attr(tag, "text-anchor") };

/** The deserved points scatters on one Team page, each with the team's dot and its two labels. */
export function scatterCharts(html) {
  const starts = [...html.matchAll(SCATTER_RE.chart)];
  return starts.map((m, i) => {
    const svg = html.slice(m.index, starts[i + 1]?.index ?? html.length);
    return {
      cx: Number(attr(svg.match(SCATTER_RE.me)?.[0], "cx")),
      note: textMark(svg.match(SCATTER_RE.note)?.[0]),
      name: textMark(svg.match(SCATTER_RE.name)?.[0]),
    };
  });
}

/** Issues on one Team page: a scatter whose difference label and name are not kept apart. */
export function checkScatterLabels(html, path = "") {
  const issues = [];
  scatterCharts(html).forEach(({ note, name }, i) => {
    const across = note && name && note.anchor !== name.anchor && note.dx * name.dx < 0;
    const under = note && name && note.anchor === name.anchor && note.x === name.x && note.dx === name.dx && note.dy - name.dy >= 1;
    if (!across && !under) issues.push(`${path}: scatter ${i + 1} puts the difference label beside the team's name`);
  });
  return issues;
}

/** Each team payload's served league ranks, by slug: the featured season's `benchmarks`, rank by
 *  metric key, and every season that carries a strip, rank by `{league_code}:{metric key}`. */
export function expectedTeamRanks(dataDir = DATA_DIR) {
  const dir = join(dataDir, "teams");
  const ranks = new Map();
  if (!existsSync(dir)) return ranks;
  for (const file of readdirSync(dir).filter((f) => f.endsWith(".json"))) {
    const p = JSON.parse(readFileSync(join(dir, file), "utf8"));
    const season = (p.seasons ?? []).find((s) => s.is_featured_season);
    const served = new Map((season?.benchmarks ?? []).map((b) => [b.metric_key, b.rank]));
    for (const s of p.seasons ?? []) {
      if (s !== season && !(s.league_strip ?? []).length) continue;
      for (const b of s.benchmarks ?? []) served.set(`${s.league_code}:${b.metric_key}`, b.rank);
    }
    ranks.set(p.slug, served);
  }
  return ranks;
}

/** Whether any team payload's featured season serves a deserved points scatter with the team in it:
 *  the scatter rule only runs on the charts SCATTER_RE finds, so a drifted shape would otherwise
 *  check nothing and pass. */
export function servesScatter(dataDir = DATA_DIR) {
  const dir = join(dataDir, "teams");
  if (!existsSync(dir)) return false;
  return readdirSync(dir).filter((f) => f.endsWith(".json")).some((file) => {
    const p = JSON.parse(readFileSync(join(dir, file), "utf8"));
    const season = (p.seasons ?? []).find((s) => s.is_featured_season);
    return (season?.deserved_scatter ?? []).some((d) => d.is_self);
  });
}

/** Issues when the team payloads serve ranks but no Team page or no league row was checked: the
 *  rule only runs on the pages TEAM_PAGE finds and the rows that carry `rs-row`, so a drifted shape
 *  would otherwise check nothing and pass. */
export function checkTeamRowsFound({ teamPages, teamRows, expected }) {
  const issues = [];
  if (expected.size > 0 && teamPages === 0) issues.push("the build carries team payloads but no Team page matched TEAM_PAGE");
  if (teamRows === 0 && [...expected.values()].some((m) => m.size > 0))
    issues.push("a team payload serves league ranks but no Team page carried a league row");
  return issues;
}

/** Issues when a tab the payloads call for matched no built page: the tab checks above only run on
 *  the pages their path shape finds, so a shape that drifts from the address words would otherwise
 *  check nothing and pass. */
export function checkTabPagesFound({ fixturesPages, rankingsPages, expected }) {
  const issues = [];
  const values = [...expected.values()];
  if (fixturesPages === 0 && values.some((v) => v.hasFixtures))
    issues.push("a payload carries fixtures but no Matchdays page matched FIXTURES_PAGE");
  if (rankingsPages === 0 && values.some((v) => v.ascending.length > 0))
    issues.push("a payload carries boards but no Rankings page matched RANKINGS_PAGE");
  return issues;
}

/** An issue when the build carries match payloads but no row on any page named its match: the
 *  row-link check only runs on rows that carry `data-fixture`, so a row that dropped it would
 *  otherwise check nothing and pass. */
export function checkMatchRowsFound({ matchRows, payloadFiles }) {
  return payloadFiles > 0 && matchRows === 0
    ? ["the build carries match payloads but no row named its match with data-fixture"]
    : [];
}

export const OUR_HOSTS = ["matchdaypilot.com", "www.matchdaypilot.com", "football-data-pipeline-gcp.web.app"];
export const PROVIDER_HOST = "api-sports.io";
export const PROVIDER_PERSON_PATHS = ["/football/players/", "/football/coachs/"];
export const IMAGE_PINS = { playerPhoto: 0, providerImage: 59337, foreign: 0 };
export const IMAGE_EXAMPLES = 3;

const IMG_TAG = /<(?:img|source)\b[^>]*>/gi;
const IMG_ATTR = /\s(?:src|srcset)\s*=\s*(?:"([^"]*)"|'([^']*)')/gi;

const META_TAG = /<meta\b[^>]*>/gi;
const META_IMAGE = /\s(?:property|name)\s*=\s*["'](?:og|twitter):image(?::[a-z_]+)?["']/i;
const META_CONTENT = /\scontent\s*=\s*(?:"([^"]*)"|'([^']*)')/i;
const LD_SCRIPT = /<script\b[^>]*application\/ld\+json[^>]*>([\s\S]*?)<\/script>/gi;
const LD_KEYS = new Set(["image", "logo"]);
const LD_STRING = /"(?:image|logo)"\s*:\s*"([^"]*)"/g;

/** The `image` and `logo` addresses a JSON-LD value names, a string, a list or an object with a `url`. */
function ldAddresses(value, key = null, out = []) {
  if (typeof value === "string") {
    if (LD_KEYS.has(key)) out.push(value);
  } else if (Array.isArray(value)) {
    for (const v of value) ldAddresses(v, key, out);
  } else if (value && typeof value === "object") {
    for (const [k, v] of Object.entries(value)) {
      if (LD_KEYS.has(key) && k === "url") ldAddresses(v, key, out);
      else ldAddresses(v, k, out);
    }
  }
  return out;
}

/** Every image address the page names: image tags (`srcset` candidates split apart), the `og:image`
 *  and `twitter:image` cards and the `image` and `logo` of the JSON-LD blocks. */
export function imageUrls(html) {
  const urls = [];
  for (const [tag] of html.matchAll(META_TAG)) {
    if (!META_IMAGE.test(tag)) continue;
    const m = tag.match(META_CONTENT);
    const url = (m?.[1] ?? m?.[2] ?? "").trim();
    if (url) urls.push(url);
  }
  for (const [, body] of html.matchAll(LD_SCRIPT)) {
    try {
      urls.push(...ldAddresses(JSON.parse(body)));
    } catch {
      urls.push(...[...body.matchAll(LD_STRING)].map((m) => m[1]));
    }
  }
  for (const [tag] of html.matchAll(IMG_TAG)) {
    for (const m of tag.matchAll(IMG_ATTR)) {
      const value = (m[1] ?? m[2]).trim();
      const isSet = /^\s*srcset/i.test(m[0]);
      for (const part of isSet ? value.split(",") : [value]) {
        const url = part.trim().split(/\s+/)[0];
        if (url) urls.push(url);
      }
    }
  }
  return urls;
}

/** What an image address is: `ours` (a path on this site, a data address or our own host),
 *  `playerPhoto` (the provider's player or coach photo path), `providerImage` (any other path on the
 *  provider's host: crests, logos) or `foreign` (any other host). */
export function imageKind(url) {
  const absolute = /^(?:https?:)?\/\//i.test(url);
  if (!absolute) return "ours";
  let host;
  let pathname;
  try {
    ({ hostname: host, pathname } = new URL(url.startsWith("//") ? `https:${url}` : url));
  } catch {
    return "foreign";
  }
  if (OUR_HOSTS.includes(host)) return "ours";
  if (host === PROVIDER_HOST || host.endsWith(`.${PROVIDER_HOST}`)) {
    return PROVIDER_PERSON_PATHS.some((p) => pathname.startsWith(p)) ? "playerPhoto" : "providerImage";
  }
  return "foreign";
}

export const emptyImageCounts = () => ({
  playerPhoto: 0, providerImage: 0, foreign: 0, examples: { playerPhoto: [], providerImage: [], foreign: [] },
});

/** The count of non-ours images by kind on one page, with the addresses of the first few of each. */
export function countImages(html, path = "", into = emptyImageCounts()) {
  for (const url of imageUrls(html)) {
    const kind = imageKind(url);
    if (kind === "ours") continue;
    into[kind] += 1;
    if (into.examples[kind].length < IMAGE_EXAMPLES) into.examples[kind].push(`${path} ${url}`);
  }
  return into;
}

const IMAGE_LABELS = {
  playerPhoto: "provider player or coach photo",
  providerImage: "provider crest or logo",
  foreign: "image from a host that is not ours",
};

/** Issues from the image counts against `pins`, a ceiling per kind that only goes down. A pin at 0
 *  holds on every build. A pin above 0 holds on a sample build only, in both directions (a count that
 *  fell is a pin to lower), and is reported and not failed on a full export, whose counts the sample
 *  does not bound. */
export function checkImageOrigins(counts, { fullBuild = false, pins = IMAGE_PINS } = {}) {
  const issues = [];
  for (const kind of Object.keys(IMAGE_LABELS)) {
    const n = counts[kind];
    const pin = pins[kind];
    if (pin === 0 ? n > 0 : !fullBuild && n !== pin) {
      const seen = counts.examples[kind].length ? ` (first: ${counts.examples[kind].join("; ")})` : "";
      const lower = n < pin ? `: lower the ${kind} pin` : "";
      issues.push(`${n} ${IMAGE_LABELS[kind]} image(s), pinned at ${pin}${lower}${seen}`);
    }
  }
  return issues;
}

export function readManifest(dataDir = DATA_DIR) {
  const file = join(dataDir, "manifest.json");
  return existsSync(file) ? JSON.parse(readFileSync(file, "utf8")) : null;
}

export function countPayloads(dataDir = DATA_DIR) {
  return payloadIds(dataDir).size;
}

/** The fixture ids with a payload, from the payload file names (`{fixture_id}.json`). */
export function payloadIds(dataDir = DATA_DIR) {
  const dir = join(dataDir, "fixtures");
  if (!existsSync(dir)) return new Set();
  return new Set(readdirSync(dir).filter((f) => f.endsWith(".json")).map((f) => Number(f.slice(0, -5))));
}

export function main(distDir = DIST_DIR, dataDir = DATA_DIR, pins = IMAGE_PINS) {
  if (!existsSync(distDir)) {
    console.error(`check-built-pages: no build output at ${distDir}`);
    return 1;
  }
  const issues = [];
  let matchPages = 0;
  let fixturesPages = 0;
  let rankingsPages = 0;
  let rowsChecked = 0;
  let teamPages = 0;
  let teamRows = 0;
  let scatters = 0;
  const expected = expectedBoards(dataDir);
  const teamRanks = expectedTeamRanks(dataDir);
  const built = payloadIds(dataDir);
  const manifest = readManifest(dataDir);
  const images = emptyImageCounts();
  for (const { path, html } of readDist(distDir)) {
    countImages(html, path, images);
    if (MATCH_PAGE.test(path)) matchPages += 1;
    rowsChecked += matchRows(html).length;
    issues.push(...checkMatchRowLinks(html, built, path));
    if (FIXTURES_PAGE.test(path)) {
      fixturesPages += 1;
      issues.push(...checkFixturesPage(html, path));
      if (manifest) issues.push(...checkFixturesPayloads(html, built, path));
    }
    if (RANKINGS_PAGE.test(path)) {
      rankingsPages += 1;
      issues.push(...checkRankingsPage(html, path, expected.get(path.split("/")[2]) ?? null));
    }
    if (TEAM_PAGE.test(path)) {
      const [, lang, , slug] = path.split("/");
      teamPages += 1;
      teamRows += teamRankRows(html).length;
      issues.push(...checkTeamPage(html, lang, teamRanks.get(slug), path));
      scatters += scatterCharts(html).length;
      issues.push(...checkScatterLabels(html, path));
    }
  }
  const payloadFiles = built.size;
  issues.push(...checkMatchPageCount({ matchPages, payloadFiles, manifest }));
  issues.push(...checkTabPagesFound({ fixturesPages, rankingsPages, expected }));
  issues.push(...checkMatchRowsFound({ matchRows: rowsChecked, payloadFiles }));
  issues.push(...checkImageOrigins(images, { fullBuild: Boolean(manifest), pins }));
  issues.push(...checkTeamRowsFound({ teamPages, teamRows, expected: teamRanks }));
  if (teamPages > 0 && scatters === 0 && servesScatter(dataDir))
    issues.push("a team payload serves the deserved points scatter but no Team page carried one");
  if (issues.length) {
    console.error(`check-built-pages: ${issues.length} issue(s)`);
    for (const i of issues) console.error(`  - ${i}`);
    return 1;
  }
  console.log(
    `check-built-pages: ${matchPages} match page(s) = ${payloadFiles} payload(s) x ${LOCALES.length}` +
      (manifest
        ? ` = the warehouse's ${manifest.source_counts?.fixtures_unplayed} unplayed and ${manifest.source_counts?.fixtures_played} played`
        : " (no manifest: sample build)") +
      `; ${fixturesPages} fixtures page(s), ${rankingsPages} rankings page(s), ${rowsChecked} match row(s)` +
      ` and ${teamRows} league row(s) and ${scatters} scatter(s) on ${teamPages} team page(s) checked;` +
      ` ${images.providerImage} provider crest/logo image(s), ${images.playerPhoto} player photo(s), ${images.foreign} other foreign image(s). OK.`,
  );
  return 0;
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  process.exit(main(process.argv[2] ?? DIST_DIR, process.argv[3] ?? DATA_DIR));
}
