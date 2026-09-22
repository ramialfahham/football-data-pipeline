// The built-pages check: proof, on every build, that the site carries what the warehouse holds
// and that the Matchdays tab keeps its two invariants. Runs at astro:build:done, after the SEO
// audit, as a child process (integrations/built-pages.mjs), and is directly runnable:
//
//   node scripts/check-built-pages.mjs [distDir] [dataDir]
//
// 1. Every unplayed match has a page. The emitted match pages equal the fixture payloads times
//    the locales, and when the export's manifest is present (a full export; the committed sample
//    carries none) the payloads written equal the unplayed fixtures the warehouse held when the
//    export ran. A sampled export therefore fails a full build, by design.
// 2. On every fixtures page exactly one round is checked on load, and it is the round the
//    warehouse flagged next whenever one is flagged; every unplayed row is a link and no played row
//    is, until the match report page exists.
// 3. On every Rankings page (`/rankings/`) every board keeps the board rules: one to five rows, every
//    row a link, "fewest first" beside a board and only there when it ranks ascending, and no zero
//    on a most-first board (a zero is not a ranking there; on a fewest-first board it is the top).
//
// The parsing is regex over the emitted HTML, as audit-seo does it: the shapes are this repo's own
// components, and the pure functions below are unit-tested on string literals.

import { existsSync, readdirSync, readFileSync } from "node:fs";
import { join } from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";
import { readDist } from "./audit-seo.mjs";

export const SITE_ROOT = join(fileURLToPath(new URL(".", import.meta.url)), "..");
export const DIST_DIR = join(SITE_ROOT, "dist");
export const DATA_DIR = join(SITE_ROOT, "src", "data");
export const LOCALES = ["de", "en", "fi"];

export const MATCH_PAGE = /^\/(de|en|fi)\/[^/]+\/matches\/[^/]+\/$/;
export const FIXTURES_PAGE = /^\/(de|en|fi)\/[^/]+\/fixtures\/$/;
export const RANKINGS_PAGE = /^\/(de|en|fi)\/[^/]+\/rankings\/$/;
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
    const held = manifest.source_counts?.fixtures_unplayed;
    // More files than written is the committed sample sitting beside a full export, not a gap.
    if (payloadFiles < written) {
      issues.push(`manifest: ${written} fixture payload(s) written, only ${payloadFiles} on disk`);
    }
    if (held === undefined) {
      issues.push("manifest: no source count of unplayed fixtures, so the build cannot prove it carries them all");
    } else if (held !== written) {
      issues.push(`manifest: the warehouse held ${held} unplayed fixture(s), the export wrote ${written}`);
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

/** Issues on one fixtures page: the checked round and the row links. */
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
    if (played && isLink) issues.push(`${path}: a played row is a link, but no report page exists`);
  }
  return [...new Set(issues)];
}

const BOARD_RE = {
  board: /<div class="board">/g,
  name: /<span class="bt"><span class="nm">([^<]*)<\/span>/,
  note: /class="bnote"/,
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

/** Issues on one Rankings page: the board rules, read from the emitted boards. `expected` is what
 *  the competition payload served — how many boards, how many of them ascending — so the page is
 *  held to the data it was built from; without it the boards are checked on their own. */
export function checkRankingsPage(html, path = "", expected = null) {
  const issues = [];
  const bs = boards(html);
  if (bs.length === 0) {
    issues.push(`${path}: no board on the page`);
    return issues;
  }
  let ascending = 0;
  for (const b of bs) {
    const name = b.match(BOARD_RE.name)?.[1]?.trim() ?? "(unnamed board)";
    const rows = [...b.matchAll(BOARD_RE.row)];
    if (rows.length === 0 || rows.length > BOARD_ROWS_MAX) {
      issues.push(`${path}: board "${name}" has ${rows.length} row(s), expected 1 to ${BOARD_ROWS_MAX}`);
    }
    for (const [, tag, before, after] of rows) {
      if (tag !== "a" || !RE.href.test(before + after)) issues.push(`${path}: a row of "${name}" is not a link`);
    }
    const asc = BOARD_RE.note.test(b);
    if (asc) ascending += 1;
    else {
      for (const [, value] of b.matchAll(BOARD_RE.value)) {
        if (isZeroValue(value)) issues.push(`${path}: board "${name}" ranks a zero (${value.trim()}) on a most-first board`);
      }
    }
  }
  if (expected) {
    if (bs.length !== expected.boards) issues.push(`${path}: ${bs.length} board(s) on the page, the payload served ${expected.boards}`);
    if (ascending !== expected.ascending) {
      issues.push(`${path}: ${ascending} board(s) say "fewest first", the payload ranks ${expected.ascending} ascending`);
    }
  }
  return [...new Set(issues)];
}

/** What each competition's latest payload served for its Rankings page, by slug: the boards with
 *  rows and how many of them rank ascending. */
export function expectedBoards(dataDir = DATA_DIR) {
  const dir = join(dataDir, "competitions");
  const latest = new Map();
  if (!existsSync(dir)) return latest;
  for (const code of readdirSync(dir)) {
    const seasons = readdirSync(join(dir, code)).filter((f) => f.endsWith(".json")).sort();
    if (!seasons.length) continue;
    const p = JSON.parse(readFileSync(join(dir, code, seasons[seasons.length - 1]), "utf8"));
    const served = [...(p.team_boards ?? []), ...(p.player_boards ?? [])].filter((b) => b.rows?.length);
    if (p.slug) latest.set(p.slug, { boards: served.length, ascending: served.filter((b) => b.rank_order === "asc").length });
  }
  return latest;
}

export function readManifest(dataDir = DATA_DIR) {
  const file = join(dataDir, "manifest.json");
  return existsSync(file) ? JSON.parse(readFileSync(file, "utf8")) : null;
}

export function countPayloads(dataDir = DATA_DIR) {
  const dir = join(dataDir, "fixtures");
  return existsSync(dir) ? readdirSync(dir).filter((f) => f.endsWith(".json")).length : 0;
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
  const expected = expectedBoards(dataDir);
  for (const { path, html } of readDist(distDir)) {
    if (MATCH_PAGE.test(path)) matchPages += 1;
    if (FIXTURES_PAGE.test(path)) {
      fixturesPages += 1;
      issues.push(...checkFixturesPage(html, path));
    }
    if (RANKINGS_PAGE.test(path)) {
      rankingsPages += 1;
      issues.push(...checkRankingsPage(html, path, expected.get(path.split("/")[2]) ?? null));
    }
  }
  const payloadFiles = countPayloads(dataDir);
  const manifest = readManifest(dataDir);
  issues.push(...checkMatchPageCount({ matchPages, payloadFiles, manifest }));
  if (issues.length) {
    console.error(`check-built-pages: ${issues.length} issue(s)`);
    for (const i of issues) console.error(`  - ${i}`);
    return 1;
  }
  console.log(
    `check-built-pages: ${matchPages} match page(s) = ${payloadFiles} payload(s) x ${LOCALES.length}` +
      (manifest ? ` = the warehouse's ${manifest.source_counts?.fixtures_unplayed} unplayed` : " (no manifest: sample build)") +
      `; ${fixturesPages} fixtures page(s) and ${rankingsPages} rankings page(s) checked. OK.`,
  );
  return 0;
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  process.exit(main(process.argv[2] ?? DIST_DIR, process.argv[3] ?? DATA_DIR));
}
