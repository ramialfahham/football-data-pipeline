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
//    and a build with match payloads has at least one such row.
// 3. On every Rankings page (at the stats word) every board keeps the board rules: one to five rows,
//    every row a link, the boards the payload served and no others, and no zero on a most-first
//    board (a zero is not a ranking there; on a fewest-first board it is the top). Nothing on the
//    page names its direction, so the directions come from the payload, grouped the way the page
//    groups the boards — `boardGroups`, the function the block renders from.
//
// The parsing is regex over the emitted HTML, as audit-seo does it: the shapes are this repo's own
// components, and the pure functions below are unit-tested on string literals.

import { existsSync, readdirSync, readFileSync } from "node:fs";
import { join } from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";
import { readDist } from "./audit-seo.mjs";
import { boardGroups } from "../src/lib/competitionPayload.mjs";
import { word } from "../src/lib/addressWords.mjs";

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

export function main(distDir = DIST_DIR, dataDir = DATA_DIR) {
  if (!existsSync(distDir)) {
    console.error(`check-built-pages: no build output at ${distDir}`);
    return 1;
  }
  const issues = [];
  let matchPages = 0;
  let fixturesPages = 0;
  let rankingsPages = 0;
  let rowsChecked = 0;
  const expected = expectedBoards(dataDir);
  const built = payloadIds(dataDir);
  for (const { path, html } of readDist(distDir)) {
    if (MATCH_PAGE.test(path)) matchPages += 1;
    rowsChecked += matchRows(html).length;
    issues.push(...checkMatchRowLinks(html, built, path));
    if (FIXTURES_PAGE.test(path)) {
      fixturesPages += 1;
      issues.push(...checkFixturesPage(html, path));
    }
    if (RANKINGS_PAGE.test(path)) {
      rankingsPages += 1;
      issues.push(...checkRankingsPage(html, path, expected.get(path.split("/")[2]) ?? null));
    }
  }
  const payloadFiles = built.size;
  const manifest = readManifest(dataDir);
  issues.push(...checkMatchPageCount({ matchPages, payloadFiles, manifest }));
  issues.push(...checkTabPagesFound({ fixturesPages, rankingsPages, expected }));
  issues.push(...checkMatchRowsFound({ matchRows: rowsChecked, payloadFiles }));
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
      `; ${fixturesPages} fixtures page(s), ${rankingsPages} rankings page(s) and ${rowsChecked} match row(s) checked. OK.`,
  );
  return 0;
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  process.exit(main(process.argv[2] ?? DIST_DIR, process.argv[3] ?? DATA_DIR));
}
