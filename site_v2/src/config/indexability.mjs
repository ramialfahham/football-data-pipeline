// The ONE switch that decides whether this site is crawlable (#844).
//
// `.mjs`, not `.ts`, on purpose: `scripts/audit-seo.mjs` and `integrations/seo-audit.mjs` run as
// plain node, and node cannot `import` a `.ts` file without a loader flag. Four consumers read this
// single value -- astro.config.mjs, Layout.astro, src/pages/robots.txt.ts and the audit -- so the
// site cannot end up half-indexable.
//
// THE ASSERTION RUNS AGAINST `dist/`, NOT AGAINST THIS FILE. A source-level check proves nothing
// once someone hand-edits Layout.astro; the audit reads the emitted HTML and fails the build if the
// output disagrees with the value below.

/**
 * `false` while the site is a build-phase preview: every page emits `noindex` and robots.txt says
 * `Disallow: /`.
 *
 * Flipping this to `true` is the go-live act (#377), and it is deliberately gated on things that
 * are NOT true yet:
 *   - the imprint/operator question (#799) -- a publication blocker, not a build one;
 *   - slugs assigned once and frozen (#852/#843) -- today a slug is re-derived every build, so an
 *     indexed URL could move under a reader;
 *   - the minimum-data gate (#845) -- what earns a page at all;
 *   - fixture URL permanence (#861) -- fixture URLs are destroyed weeks after kickoff.
 *
 * `STUB_PAGES` must be EMPTY before this can be `true`: a stub is a page whose spec waives the
 * blocks requirement, and shipping one to the index is a thin page by definition.
 */
export const INDEXABLE = false;

/**
 * Page-spec `page` values allowed to declare `stub: true` -- a page that ships (so it needs a
 * canonical, hreflang and a unique title, all of which are TRUE facts about a URL that exists) but
 * has no content blocks yet.
 *
 * This is also the STUB EXPIRY TRIGGER. It is keyed to `INDEXABLE`, not to #377, because #377 has
 * no machine-readable signal and this does: the audit refuses to pass with `INDEXABLE === true`
 * while this array is non-empty.
 *
 * ⚠ NO LONGER EMPTY. It was empty from #367 (the landing page graduated to a real page with its
 * next-matches block) until the competition hub scaffold below, and emptying it again is a
 * precondition of go-live — not go-live itself; the other gates on `INDEXABLE` above are all still
 * open. Adding an entry here is how a scaffold ships honestly; it should not stay for long,
 * because that is what re-blocks #377.
 *
 * `[lang]/[competition]/index.astro` — the competition hub, added because the navigation rule in
 * `site_architecture.md` §3 makes a section heading link to what the section is about, so Next
 * matches' competition heading needs a destination. The route, its canonical, its hreflang set and
 * its locale-distinct title are all true today; only the CONTENT is missing, and **#47** owns it.
 * Every competition in `mart_competition_index` gets one, so this array grows no entries as the
 * registry grows — the page count does, the stub list does not.
 */
export const STUB_PAGES = ["[lang]/[competition]/index.astro"];

/**
 * Emitted paths kept OUT of the sitemap even when indexable.
 *
 * `/` is a permanent redirect class -- Astro's i18n `prefixDefaultLocale` generates a root redirect
 * stub, so `/index.html` is not a content page and must never be a sitemap entry or the `x-default`
 * target. `x-default` points at the `en` URL instead: it is a real page that renders, whereas `/`
 * is a client-side language redirect that a crawler cannot follow (site_architecture.md section 3
 * designs it for humans without a locale match, which is a different job).
 */
export const SITEMAP_EXCLUDE = [/^\/$/, /^\/index\.html$/];
