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
  MIN_EXPECTED_PAGES, routeSpecificity, specForPath, specTie, isTabOf, sharesHeader,
} from "./audit-seo.mjs";

const SITE = "https://matchdaypilot.com";
const LOCALES = ["de", "en", "fi"];

/** One team page in each language, at that language's address word. */
const TEAM_X = { de: "/de/mannschaften/x/", en: "/en/teams/x/", fi: "/fi/joukkueet/x/" };

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
      de: "/de/mannschaften/x/",
      en: "/en/teams/x/",
      fi: "/fi/joukkueet/x/",
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

test("entityKey strips the locale and maps the address words, so one page in 3 languages shares one key", () => {
  assert.equal(entityKey("/en/teams/x/", LOCALES), "/teams/x/");
  assert.equal(entityKey("/de/mannschaften/x/", LOCALES), "/teams/x/");
  assert.equal(entityKey("/fi/joukkueet/x/", LOCALES), "/teams/x/");
  assert.equal(entityKey("/de/bundesliga/statistiken/", LOCALES), "/bundesliga/stats/");
  assert.equal(entityKey("/fi/bundesliga/ottelut/m/", LOCALES), "/bundesliga/matches/m/");
  assert.equal(entityKey("/de/", LOCALES), entityKey("/en/", LOCALES));
  assert.equal(entityKey("/robots.txt", LOCALES), "/robots.txt");
});

test("hreflang must name the same page in each language and the page itself", () => {
  const known = new Set(["/en/teams/x/", "/de/mannschaften/x/", "/fi/joukkueet/x/", "/de/teams/y/"]);
  const opts = { ...OPTS, knownPaths: known };
  const page = (path, alternates) => ({ path, head: head({ canonical: `${SITE}${path}`, ogUrl: `${SITE}${path}`, hrefs: [path], alternates }) });
  const good = { de: "/de/mannschaften/x/", en: "/en/teams/x/", fi: "/fi/joukkueet/x/", "x-default": "/en/teams/x/" };
  const pages = ["/en/teams/x/", "/de/mannschaften/x/", "/fi/joukkueet/x/"].map((p) => page(p, good));
  const reciprocity = (issues) => issues.filter((i) => /hreflang/.test(i));
  assert.deepEqual(reciprocity(auditSet(pages, opts)), []);

  const other = auditSet([page("/de/mannschaften/x/", { ...good, de: "/de/teams/y/" })], opts);
  assert.ok(other.some((i) => /hreflang "de" points at \/de\/teams\/y\/, a different page/.test(i)), other.join("\n"));
  assert.ok(other.some((i) => /does not point at the page itself/.test(i)), other.join("\n"));

  const wrongLang = auditSet([page("/en/teams/x/", { ...good, fi: "/de/mannschaften/x/" })], opts);
  assert.ok(wrongLang.some((i) => /hreflang "fi" points at \/de\/mannschaften\/x\/, which is not a "fi" page/.test(i)), wrongLang.join("\n"));
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
    path: `${TEAM_X[l]}`,
    head: head({
      title: "Manchester United — Premier League",
      description: `desc ${l}`,
      canonical: `${SITE}${TEAM_X[l]}`,
      ogTitle: "Manchester United — Premier League",
      ogUrl: `${SITE}${TEAM_X[l]}`,
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
    path: `${TEAM_X[l]}`,
    head: head({
      title: `t ${l}`,
      description: d,
      canonical: `${SITE}${TEAM_X[l]}`,
      ogTitle: `t ${l}`,
      ogUrl: `${SITE}${TEAM_X[l]}`,
    }),
  }));
  const issues = auditSet(pages, OPTS);
  assert.equal(issues.length, 1);
  assert.match(issues[0], /description is BYTE-IDENTICAL across en\/fi/);
});

test("auditSet: differing titles across locales pass", () => {
  const pages = LOCALES.map((l) => ({
    path: `${TEAM_X[l]}`,
    head: head({
      title: `title ${l}`,
      description: `desc ${l}`,
      canonical: `${SITE}${TEAM_X[l]}`,
      ogTitle: `title ${l}`,
      ogUrl: `${SITE}${TEAM_X[l]}`,
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
    knownPaths: new Set([TEAM_X.en, TEAM_X.de]), // no /fi/
  });
  assert.ok(issues.some((i) => i.includes("/fi/joukkueet/x/, which the build did not emit")));
});

test("auditSet: dead internal links are caught — Astro validates none of these", () => {
  const issues = auditSet([{ path: "/en/teams/x/", head: head({ hrefs: ["/en/teams/ghost/"] }) }], {
    ...OPTS,
    knownPaths: new Set(Object.values(TEAM_X)),
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

test("auditSet: an entity page and its tab page share the h1 by design, and only they do", () => {
  const tab = (path, title) =>
    ({ path, head: head({ title, canonical: `${SITE}${path}`, ogUrl: `${SITE}${path}`, alternates: {} }) });
  const shared = auditSet([tab("/en/bundesliga/", "Overview"), tab("/en/bundesliga/matches/", "Fixtures")], OPTS);
  assert.ok(!shared.some((i) => i.includes("h1 is not unique")), shared.join("\n"));
  // the title still has to differ between the two
  const sameTitle = auditSet([tab("/en/bundesliga/", "T"), tab("/en/bundesliga/matches/", "T")], OPTS);
  assert.ok(sameTitle.some((i) => i.includes('title is not unique within "en"')));
  // two segments down is not a tab, and a sibling is not a tab
  const deep = auditSet([tab("/en/bundesliga/", "A"), tab("/en/bundesliga/matches/x/", "B")], OPTS);
  assert.ok(deep.some((i) => i.includes("h1 is not unique")));
  const sibling = auditSet([tab("/en/bundesliga/", "A"), tab("/en/premier-league/", "B")], OPTS);
  assert.ok(sibling.some((i) => i.includes("h1 is not unique")));
  assert.ok(isTabOf("/en/bundesliga/", "/en/bundesliga/matches/") && isTabOf("/en/bundesliga/matches/", "/en/bundesliga/"));
  assert.ok(!isTabOf("/en/teams/a/", "/en/teams/b/"));
  // two tabs of one entity page share its header too, whatever order the pages arrive in
  const twoTabs = [tab("/en/bundesliga/matches/", "Fixtures"), tab("/en/bundesliga/stats/", "Rankings"), tab("/en/bundesliga/", "Overview")];
  assert.ok(!auditSet(twoTabs, OPTS).some((i) => i.includes("h1 is not unique")));
  // but two neighbours whose parent is not their entity page (or has another h1) do not
  const neighbours = [tab("/en/teams/a/", "A"), tab("/en/teams/b/", "B")];
  assert.ok(auditSet(neighbours, OPTS).some((i) => i.includes("h1 is not unique")));
  const h1Of = new Map([["/en/bundesliga/", "Bundesliga"], ["/en/bundesliga/matches/", "Bundesliga"], ["/en/bundesliga/stats/", "Bundesliga"], ["/en/x/", "Home"], ["/en/x/a/", "Same"], ["/en/x/b/", "Same"]]);
  assert.ok(sharesHeader("/en/bundesliga/matches/", "/en/bundesliga/stats/", h1Of));
  assert.ok(!sharesHeader("/en/x/a/", "/en/x/b/", h1Of), "a parent with another h1 makes them neighbours, not tabs");
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
  const team = specRouteRegex("[lang]/[teams]/[team].astro");
  assert.ok(team.test("/en/teams/manchester-united/"));
  assert.ok(team.test("/de/mannschaften/manchester-united/"));
  assert.ok(!team.test("/en/teams/"));
  assert.ok(!team.test("/en/players/x/"));
  assert.ok(!team.test("/en/bundesliga/stats/"), "a word parameter takes only its own word");

  const fixture = specRouteRegex("[lang]/[competition]/[matches]/[fixture].astro");
  assert.ok(fixture.test("/de/brasileirao/spiele/2026-07-26-a-vs-b/"));
  assert.ok(fixture.test("/fi/brasileirao/ottelut/2026-07-26-a-vs-b/"));
  assert.ok(!fixture.test("/de/brasileirao/spiele/"));

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

  const team = specs.find((s) => s.page === "[lang]/[teams]/[team].astro");
  assert.equal(team.schemaOrg, "SportsTeam");
  assert.ok(team.match.test("/en/teams/manchester-united/"));
  assert.ok(team.match.test("/de/mannschaften/manchester-united/"));
  assert.ok(team.match.test("/fi/joukkueet/manchester-united/"));

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
    [{ path: TEAM_X.de, head: head({ title: long, ogTitle: long, canonical: `${SITE}${TEAM_X.de}`, ogUrl: `${SITE}${TEAM_X.de}` }) }],
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
    [{ path: TEAM_X.de, head: head({ title: marginal, ogTitle: marginal, canonical: `${SITE}${TEAM_X.de}`, ogUrl: `${SITE}${TEAM_X.de}` }) }],
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
  // The pairings no longer carry a competition: the title no longer names one. The
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

test("THE COLLISION: a dynamic route's regex also matches its literal sibling's URL", () => {
  // This is the ambiguity, asserted rather than described. Both specs genuinely match
  // /en/competitions/, which is why picking the FIRST match was picking by directory-walk order.
  const hub = specRouteRegex("[lang]/[competition]/index.astro");
  const index = specRouteRegex("[lang]/[competitions]/index.astro");
  assert.ok(hub.test("/en/competitions/"), "the hub pattern matches the index URL — the collision");
  assert.ok(index.test("/en/competitions/"), "the index pattern matches its own URL");
  assert.ok(hub.test("/en/bundesliga/"), "the hub pattern still matches a real competition");
  assert.ok(!index.test("/en/bundesliga/"), "the index pattern does not match a competition");
});

test("routeSpecificity ranks the literal sibling above the dynamic one", () => {
  // The tie-break. Without it the competitions INDEX was judged against the competition HUB's
  // spec and failed for emitting ItemList instead of SportsOrganization — three violations, one
  // per locale, on a page that was correct.
  assert.equal(routeSpecificity("[lang]/[competitions]/index.astro"), 2); // competitions + index
  assert.equal(routeSpecificity("[lang]/[competition]/index.astro"), 1); // index
  assert.ok(
    routeSpecificity("[lang]/[competitions]/index.astro") >
      routeSpecificity("[lang]/[competition]/index.astro"),
    "a literal segment must outrank a dynamic one, or the index inherits the hub's spec",
  );
  // Not a special case for this pair: an address-word parameter counts as a literal everywhere.
  assert.equal(routeSpecificity("[lang]/[competition]/[matches]/[fixture].astro"), 1);
  assert.equal(routeSpecificity("[lang]/[teams]/[team].astro"), 1);
  assert.equal(routeSpecificity("[lang]/[competition]/[stats]/index.astro"), 2);
  assert.equal(routeSpecificity("index.astro"), 1);
});

test("the live three-segment routes never tie: each word parameter takes only its own word", () => {
  const spec = (page) => ({
    page, schemaOrg: page, match: specRouteRegex(page), specificity: routeSpecificity(page),
  });
  const specs = [
    "[lang]/[teams]/[team].astro",
    "[lang]/[players]/[player].astro",
    "[lang]/[competition]/[matches]/index.astro",
    "[lang]/[competition]/[stats]/index.astro",
  ].map(spec);
  const cases = {
    "/de/mannschaften/x/": "[lang]/[teams]/[team].astro",
    "/fi/pelaajat/x/": "[lang]/[players]/[player].astro",
    "/de/bundesliga/spiele/": "[lang]/[competition]/[matches]/index.astro",
    "/fi/bundesliga/tilastot/": "[lang]/[competition]/[stats]/index.astro",
    "/en/bundesliga/stats/": "[lang]/[competition]/[stats]/index.astro",
  };
  for (const [path, page] of Object.entries(cases)) {
    assert.deepEqual(specTie(specs, path), [], path);
    assert.equal(specForPath(specs, path).page, page, path);
  }
  assert.equal(specForPath(specs, "/de/competitions/"), null);
  assert.equal(specForPath([spec("[lang]/[competitions]/index.astro")], "/de/wettbewerbe/").page, "[lang]/[competitions]/index.astro");
});

test("specForPath: the literal route wins the collision, in EITHER array order", () => {
  // The mutation guard. The previous implementation was `specs.find(s => s.match.test(p))`, which
  // returns the first match — so it passed or failed on directory-walk order. Asserting BOTH
  // orders is what makes `find` fail here: it can only ever be right for one of the two.
  const spec = (page, schemaOrg) => ({
    page, schemaOrg, match: specRouteRegex(page), specificity: routeSpecificity(page),
  });
  const hub = spec("[lang]/[competition]/index.astro", "SportsOrganization");
  const index = spec("[lang]/[competitions]/index.astro", "ItemList");

  for (const order of [[hub, index], [index, hub]]) {
    assert.equal(
      specForPath(order, "/en/competitions/").schemaOrg, "ItemList",
      "the competitions index must be judged against its OWN spec, whatever order specs load in",
    );
    assert.equal(
      specForPath(order, "/en/bundesliga/").schemaOrg, "SportsOrganization",
      "a real competition still resolves to the hub spec",
    );
  }
  assert.equal(specForPath([hub, index], "/en/teams/x/"), null, "no spec matches, no verdict");
});

test("specTie: an EQUAL-specificity overlap is reported, not silently resolved", () => {
  // The counterexample that found the hole, kept verbatim as the fixture. Both routes have
  // exactly one literal segment ("foo" / "bar") and both match /en/foo/bar/x/, so the specificity
  // rule cannot separate them and whichever wins would come down to directory-walk order — the
  // very order-dependence specForPath exists to remove. The gate must fail CLOSED here.
  const spec = (page) => ({
    page, schemaOrg: "Thing", match: specRouteRegex(page), specificity: routeSpecificity(page),
  });
  const a = spec("[lang]/foo/[b]/[c].astro");
  const b = spec("[lang]/[a]/bar/[c].astro");
  assert.equal(routeSpecificity(a.page), routeSpecificity(b.page), "the fixture must actually tie");
  assert.ok(a.match.test("/en/foo/bar/x/") && b.match.test("/en/foo/bar/x/"), "both must match");

  const tie = specTie([a, b], "/en/foo/bar/x/");
  assert.equal(tie.length, 2, "an equal-specificity overlap must be reported");
  assert.deepEqual(tie.map((s) => s.page).sort(), [a.page, b.page].sort());

  // And the live spec set does NOT tie — the real collision is settled 2 to 1 by specificity.
  const hub = spec("[lang]/[competition]/index.astro");
  const index = spec("[lang]/[competitions]/index.astro");
  assert.deepEqual(specTie([hub, index], "/en/competitions/"), [], "specificity settles this one");
  assert.deepEqual(specTie([hub, index], "/en/bundesliga/"), [], "only one spec matches at all");
});

test("specTie: a tie at the TOP level is caught even when a less-specific spec also matches", () => {
  // THREE matching specs at specificities [2, 2, 1]. This is the case that pins `Math.max`:
  // with only two matching specs, one per level, `max` and `min` pick different levels but both
  // end up with a single winner, so `winners.length > 1` is false either way and the mutation
  // survives — exactly the hole the two-spec fixture above had.
  //   Math.max -> top = 2, winners = the two specificity-2 specs -> TIE reported (correct)
  //   Math.min -> top = 1, winners = the one specificity-1 spec  -> [] (silently resolved)
  // It is the shape a growing spec set produces as soon as routes nest under a dynamic segment.
  const spec = (page) => ({
    page, schemaOrg: "Thing", match: specRouteRegex(page), specificity: routeSpecificity(page),
  });
  const a = spec("[lang]/foo/bar/[c].astro");   // literals: foo, bar -> 2
  const b = spec("[lang]/foo/[b]/x.astro");     // literals: foo, x   -> 2
  const c = spec("[lang]/[a]/bar/[c].astro");   // literals: bar      -> 1
  const path = "/en/foo/bar/x/";

  assert.deepEqual([a, b, c].map((s) => s.specificity), [2, 2, 1], "the fixture must be [2,2,1]");
  assert.ok([a, b, c].every((s) => s.match.test(path)), "all three must match the same path");

  const tie = specTie([a, b, c], path);
  assert.equal(tie.length, 2, "the TOP-level tie must be reported, not the least-specific match");
  assert.deepEqual(tie.map((s) => s.page).sort(), [a.page, b.page].sort());
  // And the winner is drawn from the tied top level, never from the specificity-1 spec.
  assert.equal(specForPath([a, b, c], path).specificity, 2);
});

test("emptyPaths finds nulls, blanks and placeholders anywhere in a graph", () => {
  assert.deepEqual(emptyPaths({ a: "ok" }), []);
  assert.deepEqual(emptyPaths({ a: null }), ["$.a"]);
  assert.deepEqual(emptyPaths({ a: "   " }), ["$.a"]);
  assert.deepEqual(emptyPaths({ a: "undefined" }), ["$.a"]);
  assert.deepEqual(emptyPaths({ a: [{ b: "TBD" }] }), ["$.a[0].b"]);
});
