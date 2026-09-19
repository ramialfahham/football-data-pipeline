#!/usr/bin/env node
// The SEO build gate's verifier (#844). Runs against the EMITTED `dist/`, never against source:
// a source-level grep proves nothing the moment someone hand-edits Layout.astro, and uniqueness
// does not exist until the set has been generated.
//
// Split so the interesting parts are pure and unit-testable with string literals:
//   parseHead(html)                   -> the head facts, no I/O
//   resolveHref(href, fromPath, opts) -> an app path, or null for external/non-page
//   auditSet(pages, opts)             -> issues[], no I/O
//   readDist(dir)                     -> the ONLY I/O, a generator so the corpus is never all in
//                                        memory at once
//
// SCALE. Pages are ~27-29 KB. Today's corpus is ~15-20k pages (teams + live fixtures) = 420-660 MB
// of HTML; after #845 admits player pages it is far larger. Two passes: pass 1 collects the path
// Set, pass 2 reads/parses/discards. Only REDUCED state is retained (Map<title, firstPath>,
// first-wins) and `html` is never held beyond one iteration.
// NOTE the measured numbers above describe TODAY. Whoever lands #845 re-measures them.

import { readdirSync, readFileSync, statSync, existsSync } from "node:fs";
import { join, relative, sep } from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

export const SITE_ROOT = join(fileURLToPath(new URL(".", import.meta.url)), "..");
export const DIST_DIR = join(SITE_ROOT, "dist");

/** If parsing yields fewer than this many titled pages, the extraction broke — report THAT rather
 * than "everything passed". Same self-check shape as check-page-specs.mjs's MIN_EXPECTED_KEYS,
 * which exists because a silently-zeroed check reads exactly like a clean run. */
export const MIN_EXPECTED_PAGES = 3;

const RE = {
  title: /<title[^>]*>([\s\S]*?)<\/title>/i,
  description: /<meta\s+name="description"\s+content="([^"]*)"/i,
  canonical: /<link\s+rel="canonical"\s+href="([^"]*)"/i,
  robots: /<meta\s+name="robots"\s+content="([^"]*)"/i,
  alternate: /<link\s+rel="alternate"\s+hreflang="([^"]+)"\s+href="([^"]*)"/gi,
  jsonLd: /<script[^>]+type="application\/ld\+json"[^>]*>([\s\S]*?)<\/script>/i,
  h1: /<h1[^>]*>([\s\S]*?)<\/h1>/gi,
  // ANCHORS only. A generic `href="…"` sweep also picks up <link rel="canonical"> and every
  // <link rel="alternate">, which are already checked explicitly above — including them would
  // double-report one broken canonical and muddy what "the internal link graph" means.
  href: /<a\s[^>]*href="([^"]*)"/gi,
  ogTitle: /<meta\s+property="og:title"\s+content="([^"]*)"/i,
  ogUrl: /<meta\s+property="og:url"\s+content="([^"]*)"/i,
};

const strip = (s) => s.replace(/<[^>]*>/g, "").replace(/\s+/g, " ").trim();

/** Decode the entities Astro emits, so comparisons are on the text a reader sees rather than on
 * markup. Deliberately small: this is not an HTML parser.
 *
 * NUMERIC entities matter and were missed on the first pass, which produced a false "og:title
 * differs from <title>" on every real page: Astro escapes `&` as `&#38;` inside an attribute but
 * leaves it as `&#38;` in element text too, and a named-only decoder compares one against the
 * other. The failure looked like a page defect and was a defect in the CHECKER. */
export function decode(s) {
  return s
    .replace(/&#(\d+);/g, (_, d) => String.fromCodePoint(Number(d)))
    .replace(/&#x([0-9a-f]+);/gi, (_, h) => String.fromCodePoint(parseInt(h, 16)))
    .replace(/&amp;/g, "&")
    .replace(/&lt;/g, "<")
    .replace(/&gt;/g, ">")
    .replace(/&quot;/g, '"')
    .replace(/&#39;/g, "'");
}

/** Astro's i18n `prefixDefaultLocale` generates a root redirect stub at `/`. It is not a content
 * page: it carries its own canonical to the default locale, has no locale segment of its own, and
 * is excluded from the sitemap. Auditing it as a page produces noise about a "wrong" canonical that
 * is in fact correct for a redirect. */
export function isRootRedirect(path) {
  return path === "/" || path === "/index.html";
}

/** Pure: pull every head fact this gate cares about out of one page's HTML. */
export function parseHead(html) {
  const one = (re) => {
    const m = html.match(re);
    return m ? decode(strip(m[1])) : null;
  };
  const alternates = {};
  for (const m of html.matchAll(RE.alternate)) alternates[m[1]] = decode(m[2]);
  const h1s = [...html.matchAll(RE.h1)].map((m) => decode(strip(m[1])));
  const hrefs = [...html.matchAll(RE.href)].map((m) => decode(m[1]));
  const ld = html.match(RE.jsonLd);
  return {
    title: one(RE.title),
    description: one(RE.description),
    canonical: one(RE.canonical),
    robots: one(RE.robots),
    ogTitle: one(RE.ogTitle),
    ogUrl: one(RE.ogUrl),
    alternates,
    h1s,
    hrefs,
    jsonLdRaw: ld ? ld[1].trim() : null,
  };
}

/** Pure: turn an href found on the page at `fromPath` into the app path it targets, or null when it
 * is not a same-site page reference (external, mailto, #fragment, or an asset). */
export function resolveHref(href, fromPath, { site, base = "/" } = {}) {
  if (!href || href.startsWith("#") || /^(mailto:|tel:|javascript:|data:)/i.test(href)) return null;
  let path = href;
  if (/^https?:\/\//i.test(href)) {
    if (!site) return null;
    let u;
    try {
      u = new URL(href);
    } catch {
      return null;
    }
    if (u.origin !== new URL(site).origin) return null; // genuinely external
    path = u.pathname;
  } else if (!href.startsWith("/")) {
    // Relative to the current directory.
    const dir = fromPath.endsWith("/") ? fromPath : fromPath.slice(0, fromPath.lastIndexOf("/") + 1);
    path = new URL(href, `http://x${dir}`).pathname;
  }
  // Assets are not pages; the gate checks the internal PAGE graph.
  if (/\.[a-z0-9]{2,5}$/i.test(path) && !path.endsWith(".html")) return null;
  if (base !== "/" && path.startsWith(base)) path = path.slice(base.length - 1);
  return path;
}

/** Rough rendered width of a title in the SERP font, in px.
 *
 * A CHARACTER COUNT IS THE WRONG UNIT and this gate used to have no length check at all — the 69
 * and 65 character overruns on the German and Finnish fixture titles were found by hand, which does
 * not scale to 3,250 entities x 3 locales. Google truncates on rendered width (~600px at Arial
 * 20px), so "Wolverhampton Wanderers" and "Ajax Amsterdam III" of equal length occupy very
 * different space, and nearly every club and competition name here OPENS with a wide capital.
 *
 * Approximate on purpose: a real measurement needs a browser, and being roughly right in the right
 * unit beats being exactly right in the wrong one. */
const W_NARROW = new Set([..."iljItf.,;:'!|()[]{}·"]);
const W_WIDE = new Set([..."mwMW@%"]);
/** Where Google actually truncates, roughly. Used for reporting. */
export const TITLE_PX_BUDGET = 600;
/** Where the gate FAILS. Deliberately above the budget, and that is calibration, not slack:
 *
 *  - the estimator above is approximate, so failing at exactly 600 would fire on measurement noise;
 *  - a MARGINAL overrun is not fixable. A fixture title is two proper nouns plus a competition, all
 *    load-bearing, and "Wolverhampton Wanderers gegen Manchester United | Premier League" is a real
 *    pairing at ~624px. Nothing can be cut. What truncates is the tail of the competition name,
 *    which is the least-bad thing to lose;
 *  - a LARGE overrun means the TEMPLATE is wrong, which is fixable and should stop the build.
 *
 * So the gate fires on the fixable case and stays quiet on the one nobody can act on. */
export const TITLE_PX_HARD = 660;
export const TITLE_FONT_PX = 20;

export function titleWidthPx(text, fontPx = TITLE_FONT_PX) {
  let em = 0;
  for (const ch of text) {
    if (ch === " ") em += 0.28;
    else if (W_NARROW.has(ch)) em += 0.28;
    else if (W_WIDE.has(ch)) em += 0.85;
    // \p{Lu}, not A-Z. An ASCII range drops Ö/Ä/Ü/Å into the narrow generic bucket and understates
    // them — in a site whose own live locales are German and Finnish, where those letters are
    // native.
    else if (/\p{Lu}/u.test(ch)) em += 0.68;
    else em += 0.5;
  }
  return Math.round(em * fontPx);
}

/** Turn a spec's `page` field into a regex matching the URLs that template emits.
 *
 * THIS IS WHAT CLOSES THE LOOP. The first version built its expected-`@type` map from a hardcoded
 * path->type table that never read a spec, so the schema file's promise ("the audit parses the
 * emitted @graph and fails if the type is absent") was only true by coincidence of consistent
 * authorship: the next entity spec, or a typo in an existing one, would have drifted silently.
 * A gate whose own declaration and verification halves are not connected is the exact defect this
 * PR exists to eliminate.
 *
 * `[lang]/teams/[team].astro` -> /^\/[^/]+\/teams\/[^/]+\/$/
 */
/**
 * How SPECIFIC a route is: the number of LITERAL segments in it.
 *
 * `specRouteRegex` turns every `[param]` into `[^/]+`, which is right for matching but makes a
 * dynamic route swallow its literal siblings: `[lang]/[competition]/index.astro` compiles to
 * `^/[^/]+/[^/]+/$` and therefore matches `/en/competitions/` — the competitions INDEX — as
 * happily as it matches `/en/bundesliga/`. Two specs then claim one URL and the audit judged it
 * against whichever `walkJson` happened to yield first, demanding the hub's `SportsOrganization`
 * of a page that correctly emits `ItemList`.
 *
 * Astro itself has never been ambiguous here — a static route always beats a dynamic one — so
 * this restores the router's own precedence rather than inventing a rule. Counting literal
 * segments is enough for that: `[lang]/competitions/index` scores 2 (`competitions`, `index`)
 * against `[lang]/[competition]/index`'s 1 (`index`).
 *
 * ⚠ Deliberately NOT an exemption for this one page. Every future top-level dynamic route would
 * collide with every literal sibling the same way.
 */
export function routeSpecificity(pageField) {
  return pageField
    .replace(/\.astro$/, "")
    .split("/")
    .filter((seg) => seg && !/^\[.+\]$/.test(seg)).length;
}

/**
 * The spec that governs an emitted path: of every spec whose route matches, the MOST SPECIFIC.
 *
 * Pure and exported so the tie-break is testable. It used to be `specs.find(s => s.match.test(p))`
 * inline in main(), which returned whichever spec `walkJson` yielded first — i.e. the answer
 * depended on directory-walk order, and on a collision it silently judged one page against
 * another's spec. Ties keep the first match, which is only reachable if two specs declare routes
 * of equal specificity that match the same URL — a spec-authoring bug, not something to paper over.
 */
export function specForPath(specs, path) {
  const matches = specs.filter((s) => s.match.test(path));
  if (matches.length === 0) return null;
  const top = Math.max(...matches.map((s) => s.specificity));
  return matches.find((s) => s.specificity === top);
}

/**
 * The specs that TIE for a path: two or more claiming it at equal specificity. Empty otherwise.
 *
 * The tie-break above cannot resolve this one — both routes are equally specific, so whichever
 * wins is decided by directory-walk order, which is exactly the order-dependence `specForPath`
 * exists to remove. It is a spec-AUTHORING bug (two specs declaring overlapping routes), and this
 * gate must fail CLOSED on it rather than guess: the same doctrine `MIN_EXPECTED_PAGES` states a
 * few dozen lines down, that a broken check reports itself instead of passing everything.
 *
 * Reachable, not hypothetical: `[lang]/foo/[b]/[c]` and `[lang]/[a]/bar/[c]` both score 1 and both
 * match `/en/foo/bar/x/`. Nothing today ties — the only live collision is
 * `[lang]/[competition]/index` against `[lang]/competitions/index`, which the specificity rule
 * settles 2 to 1 — so this reports a defect that does not exist yet and would otherwise arrive
 * silently.
 */
export function specTie(specs, path) {
  const matches = specs.filter((s) => s.match.test(path));
  if (matches.length < 2) return [];
  const top = Math.max(...matches.map((s) => s.specificity));
  const winners = matches.filter((s) => s.specificity === top);
  return winners.length > 1 ? winners : [];
}

export function specRouteRegex(pageField) {
  const withoutExt = pageField.replace(/\.astro$/, "");
  const escaped = withoutExt
    .split("/")
    .map((seg) => (/^\[.+\]$/.test(seg) ? "[^/]+" : seg.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")))
    .join("/");
  // trailingSlash: "always" -- an index segment collapses to the directory URL.
  const body = escaped.replace(/\/index$/, "");
  return new RegExp(`^/${body}/$`);
}

/** The path with its locale segment removed — the "same entity, other language" key. */
export function entityKey(path, locales) {
  const parts = path.split("/").filter(Boolean);
  if (locales.includes(parts[0])) return "/" + parts.slice(1).join("/") + "/";
  return path;
}

/** True when one path is the other plus exactly one segment: an entity page and one of its tabs. */
export function isTabOf(a, b) {
  const [short, long] = a.length <= b.length ? [a, b] : [b, a];
  if (!long.startsWith(short)) return false;
  const rest = long.slice(short.length).split("/").filter(Boolean);
  return rest.length === 1;
}

/**
 * Pure: audit the whole generated set.
 *
 * `pages` is an array of { path, head } where `head` is a parseHead() result. Everything here is a
 * comparison over reduced state; no page HTML is retained.
 */
export function auditSet(pages, opts) {
  const { site, locales, indexable, knownPaths, expectedTypes = {}, base = "/" } = opts;
  const issues = [];
  const add = (path, msg) => issues.push(`${path}: ${msg}`);

  if (pages.length === 0) {
    return [`audit-seo: parsed 0 pages — the dist walk or the head extraction broke, not that the site is empty`];
  }
  // SELF-CHECK, per extraction that a check depends on. The first version tested only <title>,
  // while claiming file-wide that "a broken regex reports itself instead of passing everything".
  // That was not true of the extractions whose checks are written `if (value) {…}`: if the anchor
  // or og regexes stopped matching, `hrefs` would be empty and `ogTitle` null on every page, and
  // the dead-link and og-agreement checks would silently find nothing to complain about — failing
  // OPEN, which is the one direction a gate must never fail.
  const contentPages = pages.filter((p) => !isRootRedirect(p.path));
  const floor = Math.min(MIN_EXPECTED_PAGES, contentPages.length);
  for (const [what, n] of [
    ["a <title>", contentPages.filter((p) => p.head.title).length],
    ["an <a href>", contentPages.filter((p) => p.head.hrefs.length).length],
    ["an og:title", contentPages.filter((p) => p.head.ogTitle).length],
  ]) {
    if (n < floor) {
      return [
        `audit-seo: only ${n} of ${contentPages.length} pages yielded ${what} (expected >= ${floor}) — the ` +
          `head-extraction regexes almost certainly broke on a markup change, rather than every page losing it. ` +
          `Reporting the BROKEN CHECK rather than passing a corpus nothing was actually verified against.`,
      ];
    }
  }

  // first-wins maps, keyed per locale — the only state that scales with the corpus
  const seen = { title: new Map(), description: new Map(), h1: new Map() };
  const byEntity = new Map();

  for (const { path, head } of pages) {
    if (isRootRedirect(path)) continue;
    const expectedCanonical = new URL(path, site).href;

    // 1. Canonical: present, absolute, and pointing at THIS page.
    if (!head.canonical) add(path, "no <link rel=canonical>");
    else if (!/^https?:\/\//i.test(head.canonical)) add(path, `canonical is not absolute: ${head.canonical}`);
    else if (head.canonical !== expectedCanonical)
      add(path, `canonical points elsewhere: ${head.canonical} (expected ${expectedCanonical})`);

    // 2. Indexability must match the ONE switch, checked in the OUTPUT.
    const hasNoindex = (head.robots ?? "").includes("noindex");
    if (indexable && hasNoindex) add(path, "INDEXABLE is true but the page still emits robots=noindex");
    if (!indexable && !hasNoindex) add(path, "INDEXABLE is false but the page does not emit robots=noindex");

    const loc = entityKey(path, locales);
    const isLocalised = loc !== path;

    if (isLocalised) {
      // 3. hreflang: complete, reciprocal, and every target actually exists in the build.
      for (const l of locales) {
        if (!head.alternates[l]) add(path, `missing hreflang for "${l}"`);
      }
      if (!head.alternates["x-default"]) add(path, "missing hreflang x-default");
      for (const [l, href] of Object.entries(head.alternates)) {
        const target = resolveHref(href, path, { site, base });
        if (target && knownPaths && !knownPaths.has(target))
          add(path, `hreflang "${l}" points at ${target}, which the build did not emit`);
      }
      // 4. x-default must be the en URL, never the root redirect stub.
      const xd = head.alternates["x-default"];
      if (xd && head.alternates.en && xd !== head.alternates.en)
        add(path, `x-default (${xd}) should equal the en alternate (${head.alternates.en})`);

      // 5. Uniqueness WITHIN a locale. Across locales is impossible for the <h1> by construction
      //    (it renders the entity name), so it is asserted per locale and the cross-locale case is
      //    handled by check 6 instead.
      const l = path.split("/").filter(Boolean)[0];
      for (const [field, value] of [["title", head.title], ["description", head.description], ["h1", head.h1s[0]]]) {
        if (!value) continue;
        const k = `${l} ${value}`;
        const first = seen[field].get(k);
        // The one h1 that may repeat: an entity page and its tab pages share one header by design
        // (the competition page's Overview and Matchdays); the title carries the tab for search.
        if (first && first !== path && !(field === "h1" && isTabOf(first, path)))
          add(path, `${field} is not unique within "${l}" — same as ${first}: ${JSON.stringify(value)}`);
        else if (!first) seen[field].set(k, path);
      }

      // Collect for check 6.
      if (!byEntity.has(loc)) byEntity.set(loc, []);
      byEntity.get(loc).push({ path, locale: l, title: head.title, description: head.description });
    }

    // 7. JSON-LD parses, has the declared @type, and carries no empty values.
    const expected = expectedTypes[loc] ?? expectedTypes[entityKey(path, locales)];
    if (head.jsonLdRaw) {
      let data;
      try {
        data = JSON.parse(head.jsonLdRaw);
      } catch (e) {
        add(path, `JSON-LD does not parse: ${e.message}`);
      }
      if (data) {
        const nodes = data["@graph"] ?? [data];
        const types = nodes.map((n) => n["@type"]);
        if (expected && !types.includes(expected))
          add(path, `JSON-LD has no @type "${expected}" (declared in the page spec); found ${JSON.stringify(types)}`);
        const empties = emptyPaths(data);
        if (empties.length) add(path, `JSON-LD carries empty/placeholder values at: ${empties.join(", ")}`);
      }
    } else if (expected) {
      add(path, `page spec declares schema_org "${expected}" but the page emits no JSON-LD`);
    }

    // 8. Every internal href resolves to a page the build actually emitted. Astro validates none.
    if (knownPaths) {
      for (const raw of head.hrefs) {
        const target = resolveHref(raw, path, { site, base });
        if (target && !knownPaths.has(target)) add(path, `dead internal link: ${raw} -> ${target}`);
      }
    }

    // 9. Title must survive to the SERP. Not cosmetic: an overlong title is both truncated AND more
    //    likely to be rewritten wholesale, at which point we no longer control what shows at all.
    if (head.title) {
      const px = titleWidthPx(head.title);
      if (px > TITLE_PX_HARD)
        add(path, `title is ~${px}px wide, past the ${TITLE_PX_HARD}px hard limit (SERP budget ~${TITLE_PX_BUDGET}px) — the TEMPLATE is too long, not just this entity's name: ${JSON.stringify(head.title)}`);
    }

    // 10. OG must agree with the page rather than drift from it.
    if (head.ogTitle && head.title && head.ogTitle !== head.title)
      add(path, `og:title differs from <title>`);
    if (head.ogUrl && head.canonical && head.ogUrl !== head.canonical)
      add(path, `og:url differs from the canonical`);
  }

  // 6. THE CHECK THAT WOULD HAVE CAUGHT THE LIVE DEFECT. Full cross-locale string uniqueness is
  //    unsatisfiable (the <h1> is the entity name in every language), but the DESCRIPTIVE portion
  //    must differ — otherwise all three locales ship a byte-identical title, which is what shipped
  //    before #844.
  for (const [loc, variants] of byEntity) {
    if (variants.length < 2) continue;
    for (const field of ["title", "description"]) {
      // ANY group of locales sharing a value is a duplicate, not just an all-identical set. The
      // weaker "are they ALL the same" form passed a real case: the Finnish fixture description was
      // byte-identical to the English one while German differed, so 2-of-3 collided and the check
      // saw variety and said nothing.
      const groups = new Map();
      for (const v of variants) {
        if (!v[field]) continue;
        if (!groups.has(v[field])) groups.set(v[field], []);
        groups.get(v[field]).push(v.locale);
      }
      for (const [value, langs] of groups) {
        if (langs.length > 1)
          issues.push(
            `${loc}: ${field} is BYTE-IDENTICAL across ${langs.join("/")} — the localised template is ` +
              `not reaching the output: ${JSON.stringify(value)}`,
          );
      }
    }
  }

  return issues;
}

/** Property paths whose value is null, "", or an obvious placeholder. */
export function emptyPaths(node, trail = "$", out = []) {
  if (node === null || node === undefined) {
    out.push(trail);
  } else if (Array.isArray(node)) {
    node.forEach((v, i) => emptyPaths(v, `${trail}[${i}]`, out));
  } else if (typeof node === "object") {
    for (const [k, v] of Object.entries(node)) emptyPaths(v, `${trail}.${k}`, out);
  } else if (typeof node === "string" && (node.trim() === "" || /^(undefined|null|TBD|TODO)$/i.test(node.trim()))) {
    out.push(trail);
  }
  return out;
}

/** The ONLY I/O. A generator, so the corpus is streamed rather than materialised. */
export function* readDist(dir, root = dir) {
  for (const name of readdirSync(dir)) {
    const full = join(dir, name);
    if (statSync(full).isDirectory()) {
      yield* readDist(full, root);
    } else if (name.endsWith(".html")) {
      const rel = "/" + relative(root, full).split(sep).join("/");
      // dist/en/teams/x/index.html is served at /en/teams/x/ (trailingSlash: "always").
      const path = rel.endsWith("/index.html") ? rel.slice(0, -"index.html".length) : rel;
      yield { path, html: readFileSync(full, "utf8") };
    }
  }
}

/** Read every page spec and pair its declared `schema_org` with a regex for the URLs it emits. */
export function readSpecExpectations(specsDir = join(SITE_ROOT, "src", "specs")) {
  const out = [];
  for (const file of walkJson(specsDir)) {
    if (!file.endsWith(".spec.json")) continue;
    const spec = JSON.parse(readFileSync(file, "utf8"));
    if (!spec.page || !spec.seo) continue;
    out.push({
      page: spec.page,
      schemaOrg: spec.seo.schema_org,
      match: specRouteRegex(spec.page),
      specificity: routeSpecificity(spec.page),
    });
  }
  return out;
}

function* walkJson(dir) {
  for (const name of readdirSync(dir)) {
    const full = join(dir, name);
    if (statSync(full).isDirectory()) yield* walkJson(full);
    else if (name.endsWith(".json")) yield full;
  }
}

export async function main(distDir = DIST_DIR) {
  if (!existsSync(distDir)) {
    console.error(`audit-seo: no build output at ${distDir}`);
    return 1;
  }
  // A real import, not a text-scrape. The first version regex-parsed this file's SOURCE, which
  // coupled correctness to its formatting and could disagree with Layout.astro and robots.txt.ts —
  // the two consumers that do import it. Being async costs nothing: the CLI guard below awaits.
  const { INDEXABLE, STUB_PAGES } = await import(
    pathToFileURL(join(SITE_ROOT, "src", "config", "indexability.mjs")).href
  );
  const site = "https://matchdaypilot.com";
  const locales = ["de", "en", "fi"];

  // Pass 1: the path set, so dead-link detection can be exact.
  const knownPaths = new Set();
  for (const { path } of readDist(distDir)) knownPaths.add(path);

  // Pass 2: parse and reduce. `html` is never retained.
  const pages = [];
  for (const { path, html } of readDist(distDir)) pages.push({ path, head: parseHead(html) });

  // Expected @type comes FROM THE SPECS, so a page's declaration is what it is verified against.
  // "none" means the spec says this page carries no entity node (the scaffold).
  const specs = readSpecExpectations();
  const expectedTypes = {};
  const specTies = [];
  for (const p of knownPaths) {
    // FAIL CLOSED on an unresolvable spec set: two specs claiming one URL at equal specificity
    // would otherwise be settled by directory-walk order, which is the defect specForPath removes.
    const tie = specTie(specs, p);
    if (tie.length) specTies.push(`${p}: claimed by ${tie.map((s) => s.page).join(" and ")}`);
    const spec = specForPath(specs, p);
    if (spec && spec.schemaOrg && spec.schemaOrg !== "none") {
      expectedTypes[entityKey(p, locales)] = spec.schemaOrg;
    }
  }
  if (specs.length === 0) {
    console.error("audit-seo: read 0 page specs — the spec walk broke; refusing to 'pass' with nothing to verify against");
    return 1;
  }

  const issues = auditSet(pages, { site, locales, indexable: INDEXABLE, knownPaths, expectedTypes });

  // Reported as issues, not thrown: they belong in the same list as every other build defect, and
  // a duplicate per locale is information (it says the overlap is route-shaped, not entity-shaped).
  for (const t of specTies)
    issues.push(`AMBIGUOUS PAGE SPECS — ${t}. Two specs claim one URL at equal route specificity, so which one judges it depends on directory-walk order. Narrow one of the routes.`);

  // Whole-build assertions that are not per-page.
  const robots = join(distDir, "robots.txt");
  if (!existsSync(robots)) issues.push("no robots.txt was emitted");
  else {
    const txt = readFileSync(robots, "utf8");
    if (!INDEXABLE && !/^Disallow:\s*\/\s*$/m.test(txt)) issues.push("INDEXABLE is false but robots.txt does not Disallow: /");
    if (INDEXABLE && /^Disallow:\s*\/\s*$/m.test(txt)) issues.push("INDEXABLE is true but robots.txt still Disallows everything");
  }
  if (!existsSync(join(distDir, "sitemap-index.xml")))
    issues.push("no sitemap-index.xml — @astrojs/sitemap emits sitemap-index.xml + sitemap-N.xml, never sitemap.xml");
  if (INDEXABLE && STUB_PAGES.length)
    issues.push(`INDEXABLE is true while STUB_PAGES is non-empty (${STUB_PAGES.join(", ")}) — a stub is a thin page`);

  // The 600-660px zone is ACCEPTED truncation, not a failure — but silence about it is how "a
  // handful of genuine edge cases" quietly becomes half the corpus and nobody notices until they
  // read Search Console by hand. TITLE_PX_BUDGET was documented as "used for reporting" and had no
  // runtime effect at all. Counted and always printed.
  const truncating = pages
    .filter((p) => p.head.title && !isRootRedirect(p.path))
    .map((p) => titleWidthPx(p.head.title))
    .filter((px) => px > TITLE_PX_BUDGET).length;
  if (truncating) {
    console.log(
      `audit-seo: ${truncating} of ${pages.length} page(s) have titles over the ~${TITLE_PX_BUDGET}px ` +
        `SERP budget (under the ${TITLE_PX_HARD}px hard limit, so accepted). Google will truncate these.`,
    );
  }

  if (issues.length) {
    console.error(`audit-seo: ${issues.length} violation(s) in ${pages.length} built page(s):\n`);
    for (const i of issues) console.error(`  - ${i}`);
    return 1;
  }
  console.log(`audit-seo: ${pages.length} built page(s) checked. OK.`);
  return 0;
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  main(process.argv[2] ? process.argv[2] : DIST_DIR).then((code) => process.exit(code));
}
