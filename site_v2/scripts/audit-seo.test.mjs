// Regression coverage for audit-seo.mjs (#844). Same principle as check-page-specs.test.mjs: a
// build gate whose own logic is untested can silently lose a check, and a lost check reads exactly
// like a clean run.
//
// Everything here feeds STRING LITERALS to the pure exports. No synthetic dist/ tree is created --
// building one would test the walker and little else, and fixtures in a directory named `test/`
// would be EXECUTED by `node --test`'s default discovery.

import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import {
  parseHead, resolveHref, auditSet, decode, emptyPaths, entityKey, isRootRedirect,
  specRouteRegex, readSpecExpectations, titleWidthPx, TITLE_PX_BUDGET, TITLE_PX_HARD,
  MIN_EXPECTED_PAGES,
} from "./audit-seo.mjs";

const SITE = "https://matchdaypilot.com";
const LOCALES = ["de", "en", "fi"];

/** A minimal well-formed page head, as a parseHead() result. */
function head(over = {}) {
  return {
    title: "T",
    description: "D",
    canonical: `${SITE}/en/teams/x/`,
    robots: "noindex",
    ogTitle: "T",
    ogUrl: `${SITE}/en/teams/x/`,
    alternates: {
      de: "/de/teams/x/",
      en: "/en/teams/x/",
      fi: "/fi/teams/x/",
      "x-default": "/en/teams/x/",
    },
    h1s: ["H"],
    // A self-link: present so the anchor-extraction self-check has something to see, and always a
    // member of the knownPaths sets the tests below pass.
    hrefs: ["/en/teams/x/"],
    jsonLdRaw: null,
    ...over,
  };
}
const OPTS = { site: SITE, locales: LOCALES, indexable: false, knownPaths: null, expectedTypes: {} };

test("parseHead pulls the head facts out of real-shaped markup", () => {
  const html = `<html><head>
    <title>Bayern M&#252;nchen &#38; Co</title>
    <meta name="description" content="Form &#38; stats" />
    <link rel="canonical" href="https://matchdaypilot.com/en/teams/bayern/" />
    <meta name="robots" content="noindex" />
    <link rel="alternate" hreflang="de" href="/de/teams/bayern/" />
    <link rel="alternate" hreflang="x-default" href="/en/teams/bayern/" />
    <script type="application/ld+json">{"@type":"SportsTeam"}</script>
    </head><body><h1>Bayern</h1><a href="/en/x/">x</a></body></html>`;
  const h = parseHead(html);
  assert.equal(h.title, "Bayern München & Co");
  assert.equal(h.description, "Form & stats");
  assert.equal(h.canonical, "https://matchdaypilot.com/en/teams/bayern/");
  assert.equal(h.robots, "noindex");
  assert.equal(h.alternates.de, "/de/teams/bayern/");
  assert.equal(h.alternates["x-default"], "/en/teams/bayern/");
  assert.deepEqual(h.h1s, ["Bayern"]);
  // ANCHORS only — the canonical and the two <link rel="alternate"> hrefs are deliberately NOT in
  // here; they have their own explicit checks, and folding them in would double-report one defect.
  assert.deepEqual(h.hrefs, ["/en/x/"]);
  assert.equal(h.jsonLdRaw, '{"@type":"SportsTeam"}');
});

test("decode handles NUMERIC entities — the bug that made og:title look wrong on every page", () => {
  // Astro escapes `&` as `&#38;`. A named-entity-only decoder compared the decoded <title> against
  // the still-encoded og:title and reported a page defect that was a CHECKER defect.
  assert.equal(decode("A &#38; B"), "A & B");
  assert.equal(decode("A &amp; B"), "A & B");
  assert.equal(decode("&#x2014;"), "—");
});

test("resolveHref: internal forms resolve, external and non-page forms do not", () => {
  const o = { site: SITE };
  assert.equal(resolveHref("/en/teams/x/", "/en/", o), "/en/teams/x/");
  assert.equal(resolveHref(`${SITE}/en/teams/x/`, "/en/", o), "/en/teams/x/");
  assert.equal(resolveHref("teams/x/", "/en/", o), "/en/teams/x/");
  assert.equal(resolveHref("https://example.com/x", "/en/", o), null, "external");
  assert.equal(resolveHref("#top", "/en/", o), null, "fragment");
  assert.equal(resolveHref("mailto:a@b.c", "/en/", o), null, "mailto");
  assert.equal(resolveHref("/logo.svg", "/en/", o), null, "asset, not a page");
  assert.equal(resolveHref("", "/en/", o), null);
});

test("entityKey strips the locale segment so the same page in 3 languages shares one key", () => {
  assert.equal(entityKey("/en/teams/x/", LOCALES), "/teams/x/");
  assert.equal(entityKey("/de/teams/x/", LOCALES), "/teams/x/");
  assert.equal(entityKey("/robots.txt", LOCALES), "/robots.txt");
});

test("isRootRedirect only matches the generated root stub", () => {
  assert.ok(isRootRedirect("/"));
  assert.ok(isRootRedirect("/index.html"));
  assert.ok(!isRootRedirect("/en/"));
});

test("auditSet: a well-formed set produces no issues", () => {
  const issues = auditSet([{ path: "/en/teams/x/", head: head() }], OPTS);
  assert.deepEqual(issues, []);
});

test("auditSet: THE LIVE DEFECT — byte-identical titles across locales are caught", () => {
  // This is the regression lock for what shipped before #844: title built by concatenating two
  // locale-independent fields, so all three locales emitted the same string.
  const pages = LOCALES.map((l) => ({
    path: `/${l}/teams/x/`,
    head: head({
      title: "Manchester United — Premier League",
      description: `desc ${l}`,
      canonical: `${SITE}/${l}/teams/x/`,
      ogTitle: "Manchester United — Premier League",
      ogUrl: `${SITE}/${l}/teams/x/`,
    }),
  }));
  const issues = auditSet(pages, OPTS);
  assert.equal(issues.length, 1);
  assert.match(issues[0], /title is BYTE-IDENTICAL across de\/en\/fi/);
});

test("auditSet: TWO of three locales sharing a value is caught, not just all three", () => {
  // The weaker "are they ALL identical" form passed a real case: the Finnish fixture description
  // was byte-identical to the English one while German differed, so the check saw variety and said
  // nothing. Regression lock.
  const pages = [
    ["de", "unique de"],
    ["en", "shared"],
    ["fi", "shared"],
  ].map(([l, d]) => ({
    path: `/${l}/teams/x/`,
    head: head({
      title: `t ${l}`,
      description: d,
      canonical: `${SITE}/${l}/teams/x/`,
      ogTitle: `t ${l}`,
      ogUrl: `${SITE}/${l}/teams/x/`,
    }),
  }));
  const issues = auditSet(pages, OPTS);
  assert.equal(issues.length, 1);
  assert.match(issues[0], /description is BYTE-IDENTICAL across en\/fi/);
});

test("auditSet: differing titles across locales pass", () => {
  const pages = LOCALES.map((l) => ({
    path: `/${l}/teams/x/`,
    head: head({
      title: `title ${l}`,
      description: `desc ${l}`,
      canonical: `${SITE}/${l}/teams/x/`,
      ogTitle: `title ${l}`,
      ogUrl: `${SITE}/${l}/teams/x/`,
    }),
  }));
  assert.deepEqual(auditSet(pages, OPTS), []);
});

test("auditSet: canonical must be present, absolute, and point at THIS page", () => {
  const missing = auditSet([{ path: "/en/teams/x/", head: head({ canonical: null }) }], OPTS);
  assert.ok(missing.some((i) => i.includes("no <link rel=canonical>")));

  const relative = auditSet([{ path: "/en/teams/x/", head: head({ canonical: "/en/teams/x/" }) }], OPTS);
  assert.ok(relative.some((i) => i.includes("canonical is not absolute")));

  const elsewhere = auditSet([{ path: "/en/teams/x/", head: head({ canonical: `${SITE}/en/teams/OTHER/` }) }], OPTS);
  assert.ok(elsewhere.some((i) => i.includes("canonical points elsewhere")));
});

test("auditSet: indexability is checked against the OUTPUT in both directions", () => {
  const shouldBeNoindex = auditSet([{ path: "/en/teams/x/", head: head({ robots: null }) }], OPTS);
  assert.ok(shouldBeNoindex.some((i) => i.includes("does not emit robots=noindex")));

  const shouldNotBe = auditSet([{ path: "/en/teams/x/", head: head() }], { ...OPTS, indexable: true });
  assert.ok(shouldNotBe.some((i) => i.includes("still emits robots=noindex")));
});

test("auditSet: hreflang must be complete, and x-default must equal the en alternate", () => {
  const incomplete = auditSet(
    [{ path: "/en/teams/x/", head: head({ alternates: { en: "/en/teams/x/", "x-default": "/en/teams/x/" } }) }],
    OPTS,
  );
  assert.ok(incomplete.some((i) => i.includes('missing hreflang for "de"')));
  assert.ok(incomplete.some((i) => i.includes('missing hreflang for "fi"')));

  const wrongDefault = auditSet(
    [{ path: "/en/teams/x/", head: head({ alternates: { ...head().alternates, "x-default": "/" } }) }],
    OPTS,
  );
  assert.ok(wrongDefault.some((i) => i.includes("x-default")));
});

test("auditSet: an hreflang target the build never emitted is caught", () => {
  const issues = auditSet([{ path: "/en/teams/x/", head: head() }], {
    ...OPTS,
    knownPaths: new Set(["/en/teams/x/", "/de/teams/x/"]), // no /fi/
  });
  assert.ok(issues.some((i) => i.includes("/fi/teams/x/, which the build did not emit")));
});

test("auditSet: dead internal links are caught — Astro validates none of these", () => {
  const issues = auditSet([{ path: "/en/teams/x/", head: head({ hrefs: ["/en/teams/ghost/"] }) }], {
    ...OPTS,
    knownPaths: new Set(["/en/teams/x/", "/de/teams/x/", "/fi/teams/x/"]),
  });
  assert.ok(issues.some((i) => i.includes("dead internal link")));
});

test("auditSet: within a locale, a duplicate title/description/h1 is caught", () => {
  const pages = [
    { path: "/en/teams/a/", head: head({ canonical: `${SITE}/en/teams/a/`, ogUrl: `${SITE}/en/teams/a/`, alternates: {} }) },
    { path: "/en/teams/b/", head: head({ canonical: `${SITE}/en/teams/b/`, ogUrl: `${SITE}/en/teams/b/`, alternates: {} }) },
  ];
  const issues = auditSet(pages, OPTS);
  assert.ok(issues.some((i) => i.includes('title is not unique within "en"')));
  assert.ok(issues.some((i) => i.includes('h1 is not unique within "en"')));
});

test("auditSet: JSON-LD must parse, carry the declared @type, and hold no empty values", () => {
  const opts = { ...OPTS, expectedTypes: { "/teams/x/": "SportsTeam" } };

  const broken = auditSet([{ path: "/en/teams/x/", head: head({ jsonLdRaw: "{not json" }) }], opts);
  assert.ok(broken.some((i) => i.includes("JSON-LD does not parse")));

  const wrongType = auditSet(
    [{ path: "/en/teams/x/", head: head({ jsonLdRaw: '{"@graph":[{"@type":"WebPage"}]}' }) }],
    opts,
  );
  assert.ok(wrongType.some((i) => i.includes('no @type "SportsTeam"')));

  const empty = auditSet(
    [{ path: "/en/teams/x/", head: head({ jsonLdRaw: '{"@graph":[{"@type":"SportsTeam","name":""}]}' }) }],
    opts,
  );
  assert.ok(empty.some((i) => i.includes("empty/placeholder values")));

  const absent = auditSet([{ path: "/en/teams/x/", head: head() }], opts);
  assert.ok(absent.some((i) => i.includes("emits no JSON-LD")));
});

test("auditSet: og tags must agree with the page rather than drift", () => {
  const issues = auditSet([{ path: "/en/teams/x/", head: head({ ogTitle: "something else" }) }], OPTS);
  assert.ok(issues.some((i) => i.includes("og:title differs")));
});

test("auditSet: the root redirect stub is skipped rather than audited as a page", () => {
  assert.deepEqual(auditSet([{ path: "/", head: head({ canonical: `${SITE}/en/`, alternates: {} }) }], OPTS), []);
});

test("specRouteRegex turns a spec's page field into the URLs that template emits", () => {
  const team = specRouteRegex("[lang]/teams/[team].astro");
  assert.ok(team.test("/en/teams/manchester-united/"));
  assert.ok(!team.test("/en/teams/"));
  assert.ok(!team.test("/en/players/x/"));

  const fixture = specRouteRegex("[lang]/[competition]/matches/[fixture].astro");
  assert.ok(fixture.test("/de/brasileirao/matches/2026-07-26-a-vs-b/"));
  assert.ok(!fixture.test("/de/brasileirao/matches/"));

  // trailingSlash: "always" — an index segment collapses to the directory URL.
  const landing = specRouteRegex("[lang]/index.astro");
  assert.ok(landing.test("/fi/"));
  assert.ok(!landing.test("/fi/teams/x/"));
});

test("THE LOOP IS CLOSED: expected @type comes from the committed specs, not a hardcoded table", () => {
  // The first version built its expected-type map from a path->type table that never read a spec,
  // so the schema's promise held only by coincidence of consistent authorship. Regression lock:
  // this asserts the real specs are the source, so a new entity spec cannot drift silently.
  const specs = readSpecExpectations();
  assert.ok(specs.length >= 3, `expected at least the 3 committed specs, got ${specs.length}`);

  const team = specs.find((s) => s.page === "[lang]/teams/[team].astro");
  assert.equal(team.schemaOrg, "SportsTeam");
  assert.ok(team.match.test("/en/teams/manchester-united/"));

  const fixture = specs.find((s) => s.page.includes("matches"));
  assert.equal(fixture.schemaOrg, "SportsEvent");

  // Every committed spec declares a schema_org, so none can silently escape the @type check.
  for (const s of specs) assert.ok(s.schemaOrg, `${s.page} declares no seo.schema_org`);
});

test("SELF-CHECK: a broken parser reports ITSELF rather than passing everything", () => {
  // The failure this guards: someone changes the markup, every regex stops matching, parseHead
  // returns all-nulls, and every per-page check quietly finds nothing to complain about. Without
  // this floor the gate would print "OK" while checking nothing.
  const blindTitle = Array.from({ length: 5 }, (_, i) => ({ path: `/en/teams/${i}/`, head: head({ title: null }) }));
  const issues = auditSet(blindTitle, OPTS);
  assert.equal(issues.length, 1);
  assert.match(issues[0], /only 0 of 5 pages yielded a <title>/);
  assert.ok(MIN_EXPECTED_PAGES >= 1);

  // The floor must cover EVERY extraction a check depends on, not just <title>. The dead-link and
  // og-agreement checks are written `if (value) {…}`, so a silently-empty extraction there would
  // make them find nothing and the gate would fail OPEN — the one direction it must never fail.
  const blindHrefs = Array.from({ length: 5 }, (_, i) => ({ path: `/en/teams/${i}/`, head: head({ hrefs: [] }) }));
  assert.match(auditSet(blindHrefs, OPTS)[0], /only 0 of 5 pages yielded an <a href>/);

  const blindOg = Array.from({ length: 5 }, (_, i) => ({ path: `/en/teams/${i}/`, head: head({ ogTitle: null }) }));
  assert.match(auditSet(blindOg, OPTS)[0], /only 0 of 5 pages yielded an og:title/);

  assert.match(auditSet([], OPTS)[0], /parsed 0 pages/);
});

test("titleWidthPx measures WIDTH, not characters — the whole point of the check", () => {
  // Two strings of identical length occupying very different space. A character count cannot tell
  // these apart, which is why the German and Finnish overruns had to be found by hand.
  const wide = "WWWWWWWWWW";
  const narrow = "iiiiiiiiii";
  assert.equal(wide.length, narrow.length);
  assert.ok(titleWidthPx(wide) > titleWidthPx(narrow) * 2, "wide capitals must cost far more than narrow letters");
  assert.ok(titleWidthPx("") === 0);
});

test("auditSet: a title past the HARD width limit is caught", () => {
  const long =
    "Borussia Mönchengladbach gegen Eintracht Frankfurt: Form, Statistiken, Kader & Spiele | Bundesliga";
  assert.ok(titleWidthPx(long) > TITLE_PX_HARD, "fixture for this test must exceed the hard limit, not just the budget");
  const issues = auditSet(
    [{ path: "/de/teams/x/", head: head({ title: long, ogTitle: long, canonical: `${SITE}/de/teams/x/`, ogUrl: `${SITE}/de/teams/x/` }) }],
    OPTS,
  );
  assert.ok(issues.some((i) => i.includes("hard limit")), issues.join(" | "));
});

test("auditSet: a title merely over the ~600px budget does NOT fail the build", () => {
  // The tolerance is deliberate — see TITLE_PX_HARD's comment. A marginal overrun on a real fixture
  // is unfixable (two proper nouns plus a competition, nothing to cut), so failing on it would stop
  // the build for a reason nobody can act on. This locks that the tolerance exists ON PURPOSE, so
  // nobody later "tightens" it back to 600 and starts failing nightly builds on long club names.
  const marginal = "Wolverhampton Wanderers gegen Manchester United | Premier League";
  const px = titleWidthPx(marginal);
  assert.ok(px > TITLE_PX_BUDGET && px <= TITLE_PX_HARD, `expected a marginal overrun, got ~${px}px`);
  const issues = auditSet(
    [{ path: "/de/teams/x/", head: head({ title: marginal, ogTitle: marginal, canonical: `${SITE}/de/teams/x/`, ogUrl: `${SITE}/de/teams/x/` }) }],
    OPTS,
  );
  assert.deepEqual(issues, []);
});

test("the REAL shipped templates fit the budget for a long club name", () => {
  // Reads strings.ts rather than hardcoding copies. The first version of this test embedded the
  // template strings, so when the templates were rewritten it carried on asserting dead strings and
  // would have passed while the live ones blew the budget — a guard that cannot fire.
  const src = readFileSync(new URL("../src/i18n/strings.ts", import.meta.url), "utf8");
  const templates = [...src.matchAll(/seoTeamTitle:\s*"([^"]*)"/g)].map((m) => m[1]);
  assert.equal(templates.length, 3, "expected one seoTeamTitle per locale");

  // The longest club name likely to appear; the budget must survive it, not just "Ajax".
  const LONG = "Borussia Mönchengladbach";
  for (const tpl of templates) {
    const rendered = tpl.replace("{team}", LONG).replace("{brand}", "Matchday Pilot");
    const px = titleWidthPx(rendered);
    assert.ok(px <= TITLE_PX_BUDGET, `~${px}px, over the ${TITLE_PX_BUDGET}px budget: ${rendered}`);
  }
});

test("the REAL fixture templates fit two long names inside the BUDGET, not just the hard cap", () => {
  const src = readFileSync(new URL("../src/i18n/strings.ts", import.meta.url), "utf8");
  const templates = [...src.matchAll(/seoFixtureTitle:\s*"([^"]*)"/g)].map((m) => m[1]);
  assert.equal(templates.length, 3, "expected one seoFixtureTitle per locale");

  // REALISTIC worst cases: two long names that actually meet. The first version of this test paired
  // two German clubs with "Brasileirão Série A" — a fixture that cannot exist — and failed on 661px,
  // which would have sent me shortening a template that was never too long. A guard that fails on
  // impossible data is as useless as one that never fires.
  //
  // The pairings no longer carry a competition: the title stopped naming one on 2026-08-03. The
  // widest real pairing in the whole upcoming set is the German cup tie below, measured across all
  // 26 competitions rather than picked by eye.
  const pairings = [
    ["SG Sonnenhof Grossaspach", "Borussia Mönchengladbach"],
    ["Wolverhampton Wanderers", "Manchester United"],
    ["Atletico-MG", "Palmeiras"],
  ];
  let worst = 0;
  for (const tpl of templates) {
    for (const [home, away] of pairings) {
      const rendered = tpl.replace("{home}", home).replace("{away}", away);
      worst = Math.max(worst, titleWidthPx(rendered));
    }
  }
  // The accepted-overrun note this test used to carry is GONE, because the overrun is gone. The old
  // shape ended with the competition and sat over the ~600px budget by design; the current shape
  // ends with a one-word descriptor and fits inside it. Asserting the BUDGET, not the hard cap, is
  // the point: passing the 660px cap was never the goal, it was the last line of defence.
  assert.ok(
    worst <= TITLE_PX_BUDGET,
    `worst realistic fixture title is ~${worst}px, over the ${TITLE_PX_BUDGET}px budget`,
  );
});

test("emptyPaths finds nulls, blanks and placeholders anywhere in a graph", () => {
  assert.deepEqual(emptyPaths({ a: "ok" }), []);
  assert.deepEqual(emptyPaths({ a: null }), ["$.a"]);
  assert.deepEqual(emptyPaths({ a: "   " }), ["$.a"]);
  assert.deepEqual(emptyPaths({ a: "undefined" }), ["$.a"]);
  assert.deepEqual(emptyPaths({ a: [{ b: "TBD" }] }), ["$.a[0].b"]);
});
