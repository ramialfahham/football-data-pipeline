// The font coverage check: every character a built page shows is in the site's font. It reads the
// character map of `src/assets/fonts/InterVariable.woff2`, reads the visible text of every page in
// the built site (text nodes, `alt` and `placeholder`; never scripts or styles), and counts each
// character the font lacks, per page. The counts are compared with
// `tests/fixtures/font_coverage/baseline.json` in both directions: a count that rose is a new gap,
// a count that fell is a pin to lower.
//
//   node scripts/check-font-coverage.mjs [--dist distDir]
//
// validate:ui runs it on the build of the committed data, never the deploy build.

import { readFileSync } from "node:fs";
import { join } from "node:path";
import { brotliDecompressSync } from "node:zlib";
import { pathToFileURL } from "node:url";
import { readDist, SITE_ROOT, DIST_DIR } from "./audit-seo.mjs";

export const FONT = join(SITE_ROOT, "src", "assets", "fonts", "InterVariable.woff2");
export const BASELINE = join(SITE_ROOT, "..", "tests", "fixtures", "font_coverage", "baseline.json");

// WOFF2's known-table list (the WOFF2 specification, section 5.1); the index is the tag's flag value.
const KNOWN_TAGS = [
  "cmap", "head", "hhea", "hmtx", "maxp", "name", "OS/2", "post", "cvt ", "fpgm", "glyf", "loca", "prep",
  "CFF ", "VORG", "EBDT", "EBLC", "gasp", "hdmx", "kern", "LTSH", "PCLT", "VDMX", "vhea", "vmtx", "BASE",
  "GDEF", "GPOS", "GSUB", "EBSC", "JSTF", "MATH", "CBDT", "CBLC", "COLR", "CPAL", "SVG ", "sbix", "acnt",
  "avar", "bdat", "bloc", "bsln", "cvar", "fdsc", "feat", "fmtx", "fvar", "gvar", "hsty", "just", "lcar",
  "mort", "morx", "opbd", "prop", "trak", "Zapf", "Silf", "Glat", "Gloc", "Feat", "Sill",
];

function base128(buf, pos) {
  let value = 0;
  for (let i = 0; i < 5; i++) {
    const b = buf[pos.at++];
    value = value * 128 + (b & 0x7f);
    if (!(b & 0x80)) return value;
  }
  throw new Error("WOFF2: a UIntBase128 longer than five bytes");
}

/** The SFNT tables of a WOFF2 file, decompressed, as a map from tag to bytes. */
export function woff2Tables(buf) {
  if (buf.toString("latin1", 0, 4) !== "wOF2") throw new Error("not a WOFF2 file");
  const numTables = buf.readUInt16BE(12);
  const compressed = buf.readUInt32BE(20);
  const pos = { at: 48 };
  const dir = [];
  for (let i = 0; i < numTables; i++) {
    const flags = buf[pos.at++];
    let tag;
    if ((flags & 0x3f) === 0x3f) {
      tag = buf.toString("latin1", pos.at, pos.at + 4);
      pos.at += 4;
    } else {
      tag = KNOWN_TAGS[flags & 0x3f];
    }
    const version = flags >> 6;
    const orig = base128(buf, pos);
    const transformed = tag === "glyf" || tag === "loca" ? version !== 3 : version !== 0;
    dir.push({ tag, length: transformed ? base128(buf, pos) : orig });
  }
  const data = brotliDecompressSync(buf.subarray(pos.at, pos.at + compressed));
  const out = new Map();
  let at = 0;
  for (const t of dir) {
    out.set(t.tag, data.subarray(at, at + t.length));
    at += t.length;
  }
  return out;
}

/** Every code point a `cmap` table maps, from its format 4 and format 12 subtables. */
export function cmapCodePoints(cmap) {
  const out = new Set();
  const n = cmap.readUInt16BE(2);
  for (let i = 0; i < n; i++) {
    const s = cmap.readUInt32BE(4 + 8 * i + 4);
    const format = cmap.readUInt16BE(s);
    if (format === 4) {
      const segs = cmap.readUInt16BE(s + 6) / 2;
      for (let g = 0; g < segs; g++) {
        const end = cmap.readUInt16BE(s + 14 + 2 * g);
        const start = cmap.readUInt16BE(s + 16 + 2 * segs + 2 * g);
        if (start !== 0xffff) for (let c = start; c <= end; c++) out.add(c);
      }
    } else if (format === 12) {
      const groups = cmap.readUInt32BE(s + 12);
      for (let g = 0; g < groups; g++) {
        const start = cmap.readUInt32BE(s + 16 + 12 * g);
        const end = cmap.readUInt32BE(s + 20 + 12 * g);
        for (let c = start; c <= end; c++) out.add(c);
      }
    }
  }
  return out;
}

const NAMED = { amp: "&", lt: "<", gt: ">", quot: '"', apos: "'", nbsp: " " };

function decode(text) {
  return text.replace(/&(#x[0-9a-f]+|#\d+|[a-z]+);/gi, (m, e) =>
    e[0] === "#"
      ? String.fromCodePoint(e[1] === "x" || e[1] === "X" ? parseInt(e.slice(2), 16) : parseInt(e.slice(1), 10))
      : NAMED[e.toLowerCase()] ?? m);
}

/** The text a page shows: its text nodes and its `alt` and `placeholder` values. */
export function visibleText(html) {
  const body = html
    .replace(/<!--[\s\S]*?-->/g, "")
    .replace(/<(script|style|template)\b[\s\S]*?<\/\1>/gi, "");
  const parts = [];
  for (const m of body.matchAll(/<[a-z][^>]*>/gi)) {
    for (const a of m[0].matchAll(/\s(?:alt|placeholder)\s*=\s*(?:"([^"]*)"|'([^']*)')/gi)) parts.push(a[1] ?? a[2]);
  }
  parts.push(body.replace(/<[^>]*>/g, " "));
  return decode(parts.join(" "));
}

const label = (cp) => "U+" + cp.toString(16).toUpperCase().padStart(4, "0");

/** Each character `codePoints` lacks, per page: page path -> character label -> how often it shows. */
export function missing(pages, codePoints) {
  const out = {};
  for (const { path, html } of pages) {
    for (const ch of visibleText(html)) {
      const cp = ch.codePointAt(0);
      if (cp === 0x09 || cp === 0x0a || cp === 0x0d || codePoints.has(cp)) continue;
      const byChar = (out[path] ??= {});
      byChar[label(cp)] = (byChar[label(cp)] ?? 0) + 1;
    }
  }
  return out;
}

/** One line per page and character whose count differs from its pin. */
export function compare(found, pinned) {
  const lines = [];
  for (const page of [...new Set([...Object.keys(found), ...Object.keys(pinned)])].sort()) {
    const now = found[page] ?? {};
    const was = pinned[page] ?? {};
    for (const key of [...new Set([...Object.keys(now), ...Object.keys(was)])].sort()) {
      const n = now[key] ?? 0;
      const w = was[key] ?? 0;
      if (n > w) lines.push(`count rose · ${page} · ${key} · ${n}, baseline ${w}`);
      else if (n < w) lines.push(`count fell · ${page} · ${key} · ${n}, baseline ${w}: lower the baseline`);
    }
  }
  return lines;
}

export function main(argv = process.argv.slice(2)) {
  const i = argv.indexOf("--dist");
  const dist = i >= 0 ? argv[i + 1] : DIST_DIR;
  const codePoints = cmapCodePoints(woff2Tables(readFileSync(FONT)).get("cmap"));
  const found = missing(readDist(dist), codePoints);
  const pinned = JSON.parse(readFileSync(BASELINE, "utf8"));
  const chars = new Set();
  for (const [page, byChar] of Object.entries(found)) {
    for (const [key, n] of Object.entries(byChar)) {
      chars.add(key);
      console.log(`missing · ${page} · ${key} · ${n}`);
    }
  }
  const lines = compare(found, pinned);
  for (const l of lines) console.error(l);
  console.log(`check-font-coverage: ${codePoints.size} characters in the font; ${chars.size} missing on ` +
    `${Object.keys(found).length} pages. ${lines.length ? "FAIL" : "OK"}.`);
  return lines.length ? 1 : 0;
}

if (import.meta.url === pathToFileURL(process.argv[1]).href) process.exit(main());
