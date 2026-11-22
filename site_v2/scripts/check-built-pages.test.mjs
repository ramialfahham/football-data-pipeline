// Regression coverage for check-built-pages.mjs. A build gate whose own logic is untested can
// silently lose a check, and a lost check reads exactly like a clean run. String literals, for the
// reasons audit-seo.test.mjs gives, except the one test of main's wiring, on a tree in the OS temp
// folder.

import { test } from "node:test";
import assert from "node:assert/strict";
import { mkdirSync, mkdtempSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import {
  checkFixturesPage, checkFixturesPayloads, checkMatchPageCount, checkMatchRowLinks, checkMatchRowsFound, checkRankingsPage,
  boards, isZeroValue,
  main as mainWithPins, matchRows, renderedBoards, rounds, checkTabPagesFound, FIXTURES_PAGE, MATCH_PAGE, RANKINGS_PAGE,
  checkTeamPage, checkTeamRowsFound, teamRankRows, TEAM_PAGE, checkScatterLabels, scatterCharts,
  checkImageOrigins, countImages, emptyImageCounts, imageKind, imageUrls, IMAGE_PINS, crestPath, checkCrestFiles,
} from "./check-built-pages.mjs";

// The trees the main tests write carry no images; the pins describe the committed sample, so they
// run against pins of 0 and the image rules have their own tests below.
const NO_IMAGES = { playerPhoto: 0, providerImage: 0, foreign: 0 };
const main = (distDir, dataDir, pins = NO_IMAGES) => mainWithPins(distDir, dataDir, pins);

function round(n, { checked = false, next = false, rows = [] } = {}) {
  const rowHtml = rows
    .map((r) =>
      // The attribute order is the one Astro emits (href before class); the check must not care.
      r === "unplayed"
        ? '<a href="/en/x/matches/s/" class="fxrow"><span class="sides"></span></a>'
        : r === "unplayed-inert"
          ? '<div class="fxrow"><span class="sides"></span></div>'
          : r === "played"
            ? '<div class="fxrow played"><span class="sides"></span></div>'
            : '<a href="/en/x/matches/s/" class="fxrow played"><span class="sides"></span></a>',
    )
    .join("");
  return (
    `<div class="md" data-md="${n}"><input class="md-in" type="radio" name="md" id="md-${n}"${checked ? " checked" : ""}>` +
    `<nav class="mdnav"><span class="mdstep"><span class="mdtitle"><b class="num">Matchday ${n}</b>` +
    `${next ? '<span class="nexttag">Next</span>' : ""}</span></span></nav><section>${rowHtml}</section></div>`
  );
}

test("the URL shapes: a match page, a fixtures page and a rankings page, nothing else", () => {
  assert.ok(MATCH_PAGE.test("/en/bundesliga/matches/2026-09-18-a-vs-b/"));
  assert.ok(MATCH_PAGE.test("/de/bundesliga/spiele/2026-09-18-a-vs-b/"));
  assert.ok(!MATCH_PAGE.test("/en/bundesliga/matches/"));
  assert.ok(FIXTURES_PAGE.test("/fi/bundesliga/ottelut/"));
  assert.ok(FIXTURES_PAGE.test("/en/bundesliga/matches/"));
  assert.ok(!FIXTURES_PAGE.test("/en/bundesliga/"));
  assert.ok(!MATCH_PAGE.test("/en/bundesliga/stats/"));
  assert.ok(RANKINGS_PAGE.test("/de/bundesliga/statistiken/"));
  assert.ok(RANKINGS_PAGE.test("/en/bundesliga/stats/"));
  assert.ok(!RANKINGS_PAGE.test("/de/statistiken/") && !RANKINGS_PAGE.test("/de/bundesliga/"));
});

test("each locale is paired with its own word: another language's word is not that tab", () => {
  assert.ok(!FIXTURES_PAGE.test("/de/bundesliga/matches/"));
  assert.ok(!FIXTURES_PAGE.test("/en/bundesliga/spiele/"));
  assert.ok(!RANKINGS_PAGE.test("/fi/bundesliga/stats/"));
  assert.ok(!MATCH_PAGE.test("/fi/bundesliga/spiele/x/"));
  assert.ok(!FIXTURES_PAGE.test("/en/bundesliga/fixtures/") && !RANKINGS_PAGE.test("/en/bundesliga/rankings/"));
});

test("a tab the payloads call for that matched no page is an issue, not a silent pass", () => {
  const expected = new Map([["bundesliga", { ascending: [false], hasFixtures: true }]]);
  assert.equal(checkTabPagesFound({ fixturesPages: 0, rankingsPages: 0, expected }).length, 2);
  assert.deepEqual(checkTabPagesFound({ fixturesPages: 3, rankingsPages: 3, expected }), []);
  const bare = new Map([["x", { ascending: [], hasFixtures: false }]]);
  assert.deepEqual(checkTabPagesFound({ fixturesPages: 0, rankingsPages: 0, expected: bare }), []);
});

// A board as RankingBoard.astro emits it: the head with the name, then the rows — a linked row
// unless told otherwise. The head says nothing about which way the board ranks; that is the
// payload's to say.
function board(name, values, { inert = false } = {}) {
  const rows = values
    .map((v, i) =>
      inert
        ? `<div class="ctab-row"><span class="rk num">${i + 1}</span><span class="n num pts">${v}</span></div>`
        : `<a class="ctab-row" href="/en/teams/t${i}/"><span class="rk num">${i + 1}</span><span class="n num pts">${v}</span></a>`,
    )
    .join("");
  return (
    `<div class="board"><div class="ctab rkt"><div class="ctab-head"><span class="h rk"></span>` +
    `<span class="h nmh"><span class="bt"><span class="nm">${name}</span></span>` +
    `</span><span class="h"></span></div>${rows}</div></div>`
  );
}

test("a rankings page splits into its boards, and a zero reads as zero in every locale", () => {
  assert.equal(boards(board("A", ["1"]) + board("B", ["2"])).length, 2);
  for (const z of ["0", "0.0", "0,0", "0%", "0 %"]) assert.ok(isZeroValue(z), z);
  for (const nz of ["0.5", "10", "1,0", "100%", "–"]) assert.ok(!isZeroValue(nz), nz);
});

test("the board rules: one to five linked rows, and no zero on a board the payload ranks most-first", () => {
  const good = board("Goals per match", ["3.5", "3.0", "2.8", "2.5", "2.5"]) +
    board("Goals against per match", ["0.5", "0.5", "0.8"]) +
    board("Red cards", ["1", "1", "1"]);
  assert.deepEqual(checkRankingsPage(good, "p", { ascending: [false, true, false] }), []);
  assert.deepEqual(checkRankingsPage(good, "p"), [], "without the payload only the row rules are checked");
  // six rows: the cut failed upstream
  assert.match(checkRankingsPage(board("X", ["6", "5", "4", "3", "2", "1"]), "p")[0], /6 row\(s\), expected 1 to 5/);
  // a zero ranked on a most-first board
  assert.match(
    checkRankingsPage(board("Red cards", ["1", "0"]), "p", { ascending: [false] })[0],
    /ranks a zero \(0\) on a most-first board/,
  );
  // a zero on a fewest-first board is the top row, not an issue
  assert.deepEqual(checkRankingsPage(board("Goals against per match", ["0.0", "0.5"]), "p", { ascending: [true] }), []);
  // the direction is read by position: the same zero passes where the payload ranks ascending and
  // fails one place over, so a page that reordered its boards cannot borrow the wrong direction
  const pair = board("Goals against per match", ["0.0", "0.5"]) + board("Red cards", ["1", "1"]);
  assert.deepEqual(checkRankingsPage(pair, "p", { ascending: [true, false] }), []);
  assert.match(checkRankingsPage(pair, "p", { ascending: [false, true] })[0], /ranks a zero \(0\.0\)/);
  // an inert row
  assert.match(checkRankingsPage(board("X", ["1"], { inert: true }), "p")[0], /is not a link/);
  // the page disagrees with the payload it was built from
  assert.match(
    checkRankingsPage(good, "p", { ascending: [false, true, false, false] })[0],
    /3 board\(s\) on the page, the payload served 4/,
  );
  // an empty board wrapper
  assert.match(checkRankingsPage(board("X", []), "p")[0], /0 row\(s\)/);
  assert.match(checkRankingsPage("<html></html>", "p")[0], /no board on the page/);
});

test("the payload's boards are read in the order the page renders them: team block, then player, each by group", () => {
  const b = (metric_key, metric_group, rank_order = "desc") => ({ metric_key, metric_group, rank_order, rows: [{ rank: 1 }] });
  const payload = {
    // served out of group order, and with a board the page drops for having no rows
    team_boards: [b("cards_red", "discipline"), b("goals_against_per_match", "goals", "asc"),
                  { metric_key: "empty", metric_group: "goals", rank_order: "desc", rows: [] }],
    player_boards: [b("saves_player", "goalkeeping"), b("goals_player", "goals")],
  };
  const keys = ["goals", "discipline", "goalkeeping"];
  assert.deepEqual(
    renderedBoards(payload, keys).map((x) => x.metric_key),
    ["goals_against_per_match", "cards_red", "goals_player", "saves_player"],
  );
  // a group the catalogue does not list takes its boards off the page, as the block does
  assert.deepEqual(renderedBoards(payload, ["goals"]).map((x) => x.metric_key), ["goals_against_per_match", "goals_player"]);
});

test("match pages equal payloads times locales, and the manifest ties them to the warehouse", () => {
  assert.deepEqual(checkMatchPageCount({ matchPages: 6, payloadFiles: 2 }), []);
  assert.match(checkMatchPageCount({ matchPages: 5, payloadFiles: 2 })[0], /5 emitted, 6 expected/);
  const manifest = { counts: { fixture: 2 }, source_counts: { fixtures_unplayed: 1, fixtures_played: 1 } };
  assert.deepEqual(checkMatchPageCount({ matchPages: 6, payloadFiles: 2, manifest }), []);
  const sampled = { counts: { fixture: 2 }, source_counts: { fixtures_unplayed: 5022, fixtures_played: 60054 } };
  assert.match(checkMatchPageCount({ matchPages: 6, payloadFiles: 2, manifest: sampled })[0], /held 5022 unplayed and 60054 played .* wrote 2/);
  const short = { counts: { fixture: 3 }, source_counts: { fixtures_unplayed: 2, fixtures_played: 1 } };
  assert.match(checkMatchPageCount({ matchPages: 6, payloadFiles: 2, manifest: short })[0], /3 fixture payload\(s\) written, only 2 on disk/);
  // the committed sample beside a full export: more files than written is not a gap
  const beside = { counts: { fixture: 2 }, source_counts: { fixtures_unplayed: 2, fixtures_played: 0 } };
  assert.deepEqual(checkMatchPageCount({ matchPages: 9, payloadFiles: 3, manifest: beside }), []);
  const blind = { counts: { fixture: 2 }, source_counts: { fixtures_unplayed: 2 } };
  assert.match(checkMatchPageCount({ matchPages: 6, payloadFiles: 2, manifest: blind })[0], /no source count/);
});

test("a fixtures page splits into its rounds", () => {
  assert.equal(rounds(round(1) + round(2) + round(3)).length, 3);
  assert.equal(rounds("<html></html>").length, 0);
});

test("exactly one round is checked and it is the flagged one", () => {
  const good = round(3, { rows: ["played"] }) + round(4, { checked: true, next: true, rows: ["unplayed"] }) + round(5);
  assert.deepEqual(checkFixturesPage(good, "/en/x/fixtures/"), []);
  assert.match(checkFixturesPage(round(3) + round(4, { next: true }), "p")[0], /0 round\(s\) checked/);
  assert.match(checkFixturesPage(round(3, { checked: true }) + round(4, { checked: true }), "p")[0], /2 round\(s\) checked/);
  assert.match(checkFixturesPage(round(3, { checked: true }) + round(4, { next: true }), "p")[0], /not the round flagged next/);
  assert.match(checkFixturesPage(round(3, { next: true }) + round(4, { checked: true, next: true }), "p")[0], /2 rounds carry the Next tag/);
});

test("no flagged round: any single checked round passes (after or before the season)", () => {
  assert.deepEqual(checkFixturesPage(round(33, { rows: ["played"] }) + round(34, { checked: true, rows: ["played"] }), "p"), []);
});

test("every unplayed row is a link, and a played row may link to its page", () => {
  assert.deepEqual(checkFixturesPage(round(4, { checked: true, rows: ["unplayed", "unplayed", "played"] }), "p"), []);
  // the same rows with class before href, and an unrelated <a> and <div> on the page: no difference
  const swapped = round(4, { checked: true }).replace("<section>",
    '<section><a class="fxrow" href="/en/x/matches/s/"></a><a class="lnk" href="/en/">Home</a><div class="dh">Fri</div>');
  assert.deepEqual(checkFixturesPage(swapped, "p"), []);
  assert.match(checkFixturesPage(round(4, { checked: true, rows: ["unplayed-inert"] }), "p")[0], /an unplayed row is not a link/);
  assert.deepEqual(checkFixturesPage(round(4, { checked: true, rows: ["played-linked"] }), "p"), []);
});

test("a row naming its match links exactly when that match has a page", () => {
  const built = new Set([11, 12]);
  const page = '<a href="/en/x/matches/a/" class="fxrow played" data-fixture="11"></a>'
    + '<a class="lrow" data-fixture="12" href="/en/x/matches/b/"></a><div class="lrow" data-fixture="13"></div>';
  assert.deepEqual(checkMatchRowLinks(page, built, "p"), []);
  assert.match(checkMatchRowLinks('<div class="fxrow played" data-fixture="11"></div>', built, "p")[0],
    /match 11 is not a link, though its page is built/);
  assert.match(checkMatchRowLinks('<a class="lrow" href="/en/x/" data-fixture="13"></a>', built, "p")[0],
    /match 13 links, though it has no page/);
  assert.deepEqual(checkMatchRowLinks('<div class="fxrow"></div><a class="lnk" href="/en/">Home</a>', built, "p"), [],
    "a row that names no match is not checked");
});

test("a row is read wherever data-fixture sits among its attributes", () => {
  const built = new Set([11]);
  assert.match(checkMatchRowLinks('<div data-fixture="11" class="lrow"></div>', built, "p")[0],
    /match 11 is not a link, though its page is built/);
  assert.equal(matchRows('<div data-fixture="11"></div><a data-fixture="12" href="/x/"></a><div class="lrow"></div>').length, 2);
});

test("every row of a fixtures page has a match payload, played or not, whatever its status", () => {
  const built = new Set([11, 12]);
  const page = '<a href="/en/x/matches/a/" class="fxrow played" data-fixture="11"></a>'
    + '<a href="/en/x/matches/b/" class="fxrow" data-fixture="12"></a>';
  assert.deepEqual(checkFixturesPayloads(page, built, "p"), []);
  const postponed = '<div class="fxrow" data-fixture="13"><span class="when"><span class="stag">Postponed</span></span></div>';
  assert.match(checkFixturesPayloads(page + postponed, built, "p")[0], /match 13 has no match payload/);
  assert.match(checkFixturesPayloads('<div class="fxrow played" data-fixture="14"></div>', built, "p")[0],
    /match 14 has no match payload/);
});

// A full export's fixtures page: rows of matches 7 and 8 under one checked round, the manifest present.
test("main fails a full export whose fixtures page lists a match with no payload, and passes once it has one", (t) => {
  const root = mkdtempSync(join(tmpdir(), "check-built-pages-"));
  try {
    mkdirSync(join(root, "data", "fixtures"), { recursive: true });
    const manifest = (n) => writeFileSync(join(root, "data", "manifest.json"), JSON.stringify(
      { counts: { fixture: n }, source_counts: { fixtures_unplayed: n - 1, fixtures_played: 1 } }));
    const write = (dir, html) => {
      mkdirSync(join(root, "dist", ...dir), { recursive: true });
      writeFileSync(join(root, "dist", ...dir, "index.html"), html);
    };
    const rows = '<a href="/en/x/matches/m/" class="fxrow played" data-fixture="7"></a>'
      + '<div class="fxrow" data-fixture="8"><span class="when"><span class="stag">Postponed</span></span></div>';
    for (const [lang, word] of [["de", "spiele"], ["en", "matches"], ["fi", "ottelut"]]) {
      write([lang, "x", word], round(1, { checked: true }).replace("<section>", `<section>${rows}`));
      write([lang, "x", word, "m"], "<html></html>");
    }
    writeFileSync(join(root, "data", "fixtures", "7.json"), "{}");
    manifest(1);
    const errors = t.mock.method(console, "error", () => {});
    t.mock.method(console, "log", () => {});
    assert.equal(main(join(root, "dist"), join(root, "data")), 1);
    const said = errors.mock.calls.map((c) => c.arguments[0]).join("\n");
    assert.match(said, /the row of match 8 has no match payload/);
    assert.match(said, /an unplayed row is not a link/);

    writeFileSync(join(root, "data", "fixtures", "8.json"), "{}");
    manifest(2);
    for (const [lang, word] of [["de", "spiele"], ["en", "matches"], ["fi", "ottelut"]]) {
      write([lang, "x", word], round(1, { checked: true }).replace("<section>",
        `<section>${rows.replace('<div class="fxrow" data-fixture="8">', `<a href="/${lang}/x/${word}/n/" class="fxrow" data-fixture="8">`).replace("</span></span></div>", "</span></span></a>")}`));
      write([lang, "x", word, "n"], "<html></html>");
    }
    errors.mock.resetCalls();
    assert.equal(main(join(root, "dist"), join(root, "data")), 0, errors.mock.calls.map((c) => c.arguments[0]).join("\n"));
  } finally {
    rmSync(root, { recursive: true, force: true });
  }
});

test("match payloads with no row naming its match is an issue, not a silent pass", () => {
  assert.match(checkMatchRowsFound({ matchRows: 0, payloadFiles: 2 })[0], /no row named its match/);
  assert.deepEqual(checkMatchRowsFound({ matchRows: 5, payloadFiles: 2 }), []);
  assert.deepEqual(checkMatchRowsFound({ matchRows: 0, payloadFiles: 0 }), []);
});

// The one test on a tree: the floor only reaches the build through main's row count. The tree is
// in the OS temp folder, never under the repo, so `node --test` cannot discover it.
test("main fails a build whose pages name no match, and passes it once a row does", (t) => {
  const root = mkdtempSync(join(tmpdir(), "check-built-pages-"));
  try {
    mkdirSync(join(root, "data", "fixtures"), { recursive: true });
    writeFileSync(join(root, "data", "fixtures", "7.json"), "{}");
    const page = (lang, word, html) => {
      mkdirSync(join(root, "dist", lang, "x", word, "m"), { recursive: true });
      writeFileSync(join(root, "dist", lang, "x", word, "m", "index.html"), html);
    };
    page("de", "spiele", "<html></html>");
    page("fi", "ottelut", "<html></html>");
    page("en", "matches", "<html></html>");
    const errors = t.mock.method(console, "error", () => {});
    t.mock.method(console, "log", () => {});
    assert.equal(main(join(root, "dist"), join(root, "data")), 1);
    assert.ok(errors.mock.calls.some((c) => /no row named its match/.test(c.arguments[0])));
    page("en", "matches", '<a data-fixture="7" href="/en/x/matches/m/" class="lrow"></a>');
    assert.equal(main(join(root, "dist"), join(root, "data")), 0);
  } finally {
    rmSync(root, { recursive: true, force: true });
  }
});

// A "Compared with the league" row as TeamLeagueStrips.astro emits it: the name, the strip, then the
// shown rank with the value under it.
function leagueRow(metric, value, rank, { nonkey = false } = {}) {
  return (
    `<div class="rs-row${nonkey ? " nonkey" : ""}" data-metric="${metric}"><span class="chart-name">x</span>` +
    `<span class="rs-band"><span class="chart-axis"></span><span class="chart-tick">better</span></span>` +
    `<span class="rs-val">${rank}<small>${value}</small></span></div>`
  );
}

test("the Team page shape: a team's page in each locale's word, not the teams index", () => {
  assert.ok(TEAM_PAGE.test("/en/teams/paris-saint-germain-fc/"));
  assert.ok(TEAM_PAGE.test("/de/mannschaften/paris-saint-germain-fc/"));
  assert.ok(!TEAM_PAGE.test("/en/teams/"));
  assert.ok(!TEAM_PAGE.test("/de/teams/paris-saint-germain-fc/"));
  assert.ok(!TEAM_PAGE.test("/en/bundesliga/stats/"));
});

test("a less-is-better row shows the served rank: 1 of 18 is 1st, and a flipped 18th fails", () => {
  const served = new Map([["fouls_per_match", 1]]);
  assert.deepEqual(checkTeamPage(leagueRow("fouls_per_match", "6.1", "1st"), "en", served, "p"), []);
  assert.match(checkTeamPage(leagueRow("fouls_per_match", "6.1", "18th"), "en", served, "p")[0],
    /fouls_per_match shows 18th, the payload serves 1st/);
  assert.deepEqual(checkTeamPage(leagueRow("fouls_per_match", "6,1", "1."), "de", served, "p"), []);
});

test("a more-is-better row shows the served rank too: the highest value is 1st", () => {
  const served = new Map([["goals_per_match", 1], ["passes_per_match", 12]]);
  const page = leagueRow("goals_per_match", "2.9", "1st") + leagueRow("passes_per_match", "410", "12th", { nonkey: true });
  assert.deepEqual(checkTeamPage(page, "en", served, "p"), []);
  assert.match(checkTeamPage(leagueRow("goals_per_match", "2.9", "18th"), "en", served, "p")[0], /shows 18th, the payload serves 1st/);
});

test("a row in a competition's panel shows that competition's served rank", () => {
  const served = new Map([["goals_per_match", 1], ["BL1:goals_per_match", 1], ["UCL:goals_per_match", 6]]);
  const panel = (league, rank) => `<div class="cmp-p" data-cmp="1" data-league="${league}">${leagueRow("goals_per_match", "2.0", rank)}</div>`;
  assert.deepEqual(checkTeamPage(panel("BL1", "1st") + panel("UCL", "6th"), "en", served, "p"), []);
  assert.match(checkTeamPage(panel("UCL", "1st"), "en", served, "p")[0], /shows 1st, the payload serves 6th/);
  assert.match(checkTeamPage(panel("UECL", "1st"), "en", served, "p")[0], /no served rank/);
});

test("a league row with no metric, no served rank or no shown rank is an issue, not a pass", () => {
  const served = new Map([["fouls_per_match", 1]]);
  assert.match(checkTeamPage(leagueRow("fouls_per_match", "6.1", "1st").replace(' data-metric="fouls_per_match"', ""), "en", served, "p")[0],
    /names no metric/);
  assert.match(checkTeamPage(leagueRow("cards_red", "0.1", "1st"), "en", served, "p")[0], /cards_red has no served rank/);
  assert.match(checkTeamPage(leagueRow("fouls_per_match", "6.1", "1st"), "en", undefined, "p")[0], /no served rank/);
  assert.match(checkTeamPage('<div class="rs-row" data-metric="fouls_per_match"></div>', "en", served, "p")[0], /shows no rank/);
  assert.equal(teamRankRows(leagueRow("a", "1", "1st") + '<div class="rs-list"></div>' + leagueRow("b", "2", "2nd")).length, 2);
});

// The Team rule reaches the build only through main: the payload read by slug, the page found by
// TEAM_PAGE and the row count. A tree in the OS temp folder, as above.
test("main fails a Team page with no league row or a flipped served rank, and passes it once the row shows the served one", (t) => {
  const root = mkdtempSync(join(tmpdir(), "check-built-pages-team-"));
  try {
    mkdirSync(join(root, "data", "teams"), { recursive: true });
    const season = { is_featured_season: true, benchmarks: [{ metric_key: "fouls_per_match", rank: 1, team_count: 18 }] };
    writeFileSync(join(root, "data", "teams", "85.json"), JSON.stringify({ slug: "psg", seasons: [season] }));
    const write = (html) => {
      mkdirSync(join(root, "dist", "en", "teams", "psg"), { recursive: true });
      writeFileSync(join(root, "dist", "en", "teams", "psg", "index.html"), html);
    };
    const page = (shown) => write(leagueRow("fouls_per_match", "6.1", shown));
    const errors = t.mock.method(console, "error", () => {});
    t.mock.method(console, "log", () => {});
    write("<html></html>");
    assert.equal(main(join(root, "dist"), join(root, "data")), 1);
    assert.ok(errors.mock.calls.some((c) => /no Team page carried a league row/.test(c.arguments[0])));
    page("18th");
    assert.equal(main(join(root, "dist"), join(root, "data")), 1);
    assert.ok(errors.mock.calls.some((c) => /fouls_per_match shows 18th, the payload serves 1st/.test(c.arguments[0])));
    page("1st");
    assert.equal(main(join(root, "dist"), join(root, "data")), 0);
  } finally {
    rmSync(root, { recursive: true, force: true });
  }
});

test("team payloads with ranks but no Team page or no league row checked is an issue, not a silent pass", () => {
  const expected = new Map([["psg", new Map([["fouls_per_match", 1]])]]);
  assert.equal(checkTeamRowsFound({ teamPages: 0, teamRows: 0, expected }).length, 2);
  assert.match(checkTeamRowsFound({ teamPages: 3, teamRows: 0, expected })[0], /no Team page carried a league row/);
  assert.deepEqual(checkTeamRowsFound({ teamPages: 3, teamRows: 20, expected }), []);
  assert.deepEqual(checkTeamRowsFound({ teamPages: 0, teamRows: 0, expected: new Map() }), []);
});

// A deserved points scatter as TeamDeserved.astro emits it: the team's dot, then the difference
// label, then the name.
function scatter({ cx = 100, note, name }) {
  const text = (cls, role, m) =>
    `<text class="${cls}" data-fix="" data-role="${role}" x="${cx}" y="150" dx="${m.dx}" dy="${m.dy}" text-anchor="${m.anchor}">x</text>`;
  return (
    `<svg class="dp-chart chart-wide" viewBox="0 0 560 330" role="img"><line class="chart-axis" x1="46" x2="46" y1="12" y2="272"></line>` +
    `<circle class="chart-dot chart-me" data-fix="" cx="${cx}" cy="150"></circle>` + text("chart-note", "gap", note) +
    text("chart-label", "name", name) + `</svg>`
  );
}

test("the scatter's difference label sits across the dot from the name, or a line under it; beside it fails", () => {
  const name = { dx: "0.6em", dy: "0.35em", anchor: "start" };
  assert.deepEqual(checkScatterLabels(scatter({ note: { dx: "-0.6em", dy: "0.35em", anchor: "end" }, name }), "p"), []);
  assert.deepEqual(checkScatterLabels(scatter({ note: { dx: "0.6em", dy: "1.85em", anchor: "start" }, name }), "p"), []);
  assert.match(checkScatterLabels(scatter({ note: { dx: "0.6em", dy: "0.8em", anchor: "start" }, name }), "p")[0],
    /p: scatter 1 puts the difference label beside the team's name/);
  assert.equal(checkScatterLabels(scatter({ note: { dx: "0.6em", dy: "-0.6em", anchor: "start" }, name }), "p").length, 1);
  assert.equal(checkScatterLabels(scatter({ note: { dx: "-0.6em", dy: "0.35em", anchor: "start" }, name }), "p").length, 1);
  const two = scatter({ note: { dx: "-0.6em", dy: "0.35em", anchor: "end" }, name }) +
    scatter({ note: { dx: "0.6em", dy: "0.8em", anchor: "start" }, name });
  assert.equal(scatterCharts(two).length, 2);
  assert.match(checkScatterLabels(two, "p")[0], /scatter 2/);
});

test("main fails a Team page whose scatter is missing or puts the label beside the name", (t) => {
  const root = mkdtempSync(join(tmpdir(), "check-built-pages-scatter-"));
  try {
    mkdirSync(join(root, "data", "teams"), { recursive: true });
    const season = {
      is_featured_season: true,
      benchmarks: [{ metric_key: "fouls_per_match", rank: 1, team_count: 18 }],
      deserved_scatter: [{ is_self: true, sotd: 1, points: 20, deserved: 18 }],
    };
    writeFileSync(join(root, "data", "teams", "85.json"), JSON.stringify({ slug: "psg", seasons: [season] }));
    const write = (html) => {
      mkdirSync(join(root, "dist", "en", "teams", "psg"), { recursive: true });
      writeFileSync(join(root, "dist", "en", "teams", "psg", "index.html"), leagueRow("fouls_per_match", "6.1", "1st") + html);
    };
    const name = { dx: "0.6em", dy: "0.35em", anchor: "start" };
    const errors = t.mock.method(console, "error", () => {});
    t.mock.method(console, "log", () => {});
    write("");
    assert.equal(main(join(root, "dist"), join(root, "data")), 1);
    assert.ok(errors.mock.calls.some((c) => /serves the deserved points scatter but no Team page carried one/.test(c.arguments[0])));
    write(scatter({ note: { dx: "0.6em", dy: "0.8em", anchor: "start" }, name }));
    assert.equal(main(join(root, "dist"), join(root, "data")), 1);
    assert.ok(errors.mock.calls.some((c) => /beside the team's name/.test(c.arguments[0])));
    write(scatter({ note: { dx: "-0.6em", dy: "0.35em", anchor: "end" }, name }));
    assert.equal(main(join(root, "dist"), join(root, "data")), 0);
  } finally {
    rmSync(root, { recursive: true, force: true });
  }
});

const PROVIDER = "https://media.api-sports.io/football";

test("an image address is read from src and from every srcset candidate, on img and source, in either quote", () => {
  const html =
    `<img src="${PROVIDER}/teams/1.png" alt="">` +
    `<IMG alt='' SRC='${PROVIDER}/leagues/2.png'>` +
    `<picture><source srcset="/a.webp 1x, https://cdn.example.com/b.webp 2x"><img src="/c.png"></picture>` +
    `<a href="https://media.api-sports.io/football/players/9.png">not an image</a>`;
  assert.deepEqual(imageUrls(html), [
    `${PROVIDER}/teams/1.png`, `${PROVIDER}/leagues/2.png`, "/a.webp", "https://cdn.example.com/b.webp", "/c.png",
  ]);
});

test("the social cards and the JSON-LD image and logo are read as image addresses, in any attribute order", () => {
  const html =
    `<meta content="${PROVIDER}/teams/1.png" property="og:image">` +
    `<meta name="twitter:image" content='${PROVIDER}/players/9.png'>` +
    `<meta property="og:title" content="${PROVIDER}/not-an-image.png">` +
    `<script type="application/ld+json">{"@type":"Person","image":"${PROVIDER}/players/8.png",` +
    `"parent":{"logo":{"@type":"ImageObject","url":"${PROVIDER}/teams/2.png"},"url":"https://matchdaypilot.com/x/"},` +
    `"sameAs":["${PROVIDER}/nope.png"],"photos":[{"image":["/a.png","${PROVIDER}/teams/3.png"]}]}</script>` +
    `<script type="application/ld+json">{"image":"${PROVIDER}/teams/4.png", broken</script>`;
  assert.deepEqual(imageUrls(html), [
    `${PROVIDER}/teams/1.png`, `${PROVIDER}/players/9.png`,
    `${PROVIDER}/players/8.png`, `${PROVIDER}/teams/2.png`, "/a.png", `${PROVIDER}/teams/3.png`,
    `${PROVIDER}/teams/4.png`,
  ]);
});

test("an image is ours, a provider photo, a provider crest or logo, or from another host", () => {
  assert.equal(imageKind("/assets/crest.png"), "ours");
  assert.equal(imageKind("data:image/png;base64,AAAA"), "ours");
  assert.equal(imageKind("https://matchdaypilot.com/crests/1.png"), "ours");
  assert.equal(imageKind(`${PROVIDER}/players/9.png`), "playerPhoto");
  assert.equal(imageKind(`${PROVIDER}/coachs/9.png`), "playerPhoto");
  assert.equal(imageKind(`//media.api-sports.io/football/players/9.png`), "playerPhoto");
  assert.equal(imageKind(`${PROVIDER}/teams/1.png`), "providerImage");
  assert.equal(imageKind(`${PROVIDER}/leagues/1.png`), "providerImage");
  assert.equal(imageKind("https://media-4.api-sports.io/football/teams/1.png"), "providerImage");
  assert.equal(imageKind("https://matchdaypilot.com.evil.example/x.png"), "foreign");
  assert.equal(imageKind("https://cdn.example.com/x.png"), "foreign");
  assert.equal(imageKind("http://[bad"), "foreign");
});

test("images are counted by kind across pages, with the first addresses of each kind", () => {
  const counts = emptyImageCounts();
  countImages(`<img src="${PROVIDER}/teams/1.png"><img src="/ours.png">`, "/en/", counts);
  countImages(`<img src="${PROVIDER}/players/9.png"><img src="https://cdn.example.com/x.png">`, "/de/", counts);
  assert.deepEqual([counts.playerPhoto, counts.providerImage, counts.foreign], [1, 1, 1]);
  assert.deepEqual(counts.examples.playerPhoto, [`/de/ ${PROVIDER}/players/9.png`]);
});

test("the committed pins hold player photos and other hosts at 0", () => {
  assert.equal(IMAGE_PINS.playerPhoto, 0);
  assert.equal(IMAGE_PINS.foreign, 0);
});

test("a pin at 0 fails any image of its kind on every build", () => {
  const counts = emptyImageCounts();
  countImages(`<img src="${PROVIDER}/players/9.png">`, "/en/p/", counts);
  const pins = { playerPhoto: 0, providerImage: 0, foreign: 0 };
  for (const fullBuild of [false, true]) {
    const issues = checkImageOrigins(counts, { fullBuild, pins });
    assert.equal(issues.length, 1);
    assert.match(issues[0], /1 provider player or coach photo image\(s\), pinned at 0 \(first: \/en\/p\/ /);
  }
  assert.deepEqual(checkImageOrigins(emptyImageCounts(), { pins }), []);
});

test("a pin above 0 fails a sample build whose count rose or fell, and is only reported on a full export", () => {
  const pins = { playerPhoto: 0, providerImage: 2, foreign: 0 };
  const built = (n) => countImages(`<img src="${PROVIDER}/teams/1.png">`.repeat(n), "/en/", emptyImageCounts());
  assert.deepEqual(checkImageOrigins(built(2), { pins }), []);
  assert.match(checkImageOrigins(built(3), { pins })[0], /3 provider crest or logo image\(s\), pinned at 2 \(first/);
  assert.match(checkImageOrigins(built(1), { pins })[0], /1 provider crest or logo image\(s\), pinned at 2: lower the providerImage pin/);
  assert.deepEqual(checkImageOrigins(built(900), { pins, fullBuild: true }), []);
});

test("main fails a built page with an image from a foreign host or a provider photo, and passes the pinned sample", (t) => {
  const root = mkdtempSync(join(tmpdir(), "check-built-pages-img-"));
  try {
    mkdirSync(join(root, "data"), { recursive: true });
    mkdirSync(join(root, "dist", "en"), { recursive: true });
    const page = (img) => writeFileSync(join(root, "dist", "en", "index.html"), `<html><body>${img}</body></html>`);
    const pins = { playerPhoto: 0, providerImage: 1, foreign: 0 };
    const errors = t.mock.method(console, "error", () => {});
    t.mock.method(console, "log", () => {});
    page(`<img src="${PROVIDER}/teams/1.png">`);
    assert.equal(main(join(root, "dist"), join(root, "data"), pins), 0, errors.mock.calls.map((c) => c.arguments[0]).join("\n"));
    page(`<img src="${PROVIDER}/teams/1.png"><img src="${PROVIDER}/players/9.png">`);
    assert.equal(main(join(root, "dist"), join(root, "data"), pins), 1);
    assert.ok(errors.mock.calls.some((c) => /provider player or coach photo/.test(c.arguments[0])));
    page(`<img src="${PROVIDER}/teams/1.png"><img src="https://cdn.example.com/x.png">`);
    assert.equal(main(join(root, "dist"), join(root, "data"), pins), 1);
  } finally {
    rmSync(root, { recursive: true, force: true });
  }
});

test("main holds a pin above 0 on a sample build and only reports it on a full export; a pin at 0 holds on both", (t) => {
  const root = mkdtempSync(join(tmpdir(), "check-built-pages-pin-"));
  try {
    mkdirSync(join(root, "data"), { recursive: true });
    mkdirSync(join(root, "dist", "en"), { recursive: true });
    const crests = (n) => writeFileSync(join(root, "dist", "en", "index.html"),
      `<html><body>${`<img src="${PROVIDER}/teams/1.png">`.repeat(n)}</body></html>`);
    const photo = () => writeFileSync(join(root, "dist", "en", "index.html"),
      `<html><body><meta property="og:image" content="${PROVIDER}/players/9.png"></body></html>`);
    const manifest = () => writeFileSync(join(root, "data", "manifest.json"), JSON.stringify(
      { counts: { fixture: 0 }, source_counts: { fixtures_unplayed: 0, fixtures_played: 0 } }));
    const pins = { playerPhoto: 0, providerImage: 2, foreign: 0 };
    const run = () => main(join(root, "dist"), join(root, "data"), pins);
    t.mock.method(console, "error", () => {});
    t.mock.method(console, "log", () => {});
    crests(5);
    assert.equal(run(), 1, "a sample build with a count above its pin fails");
    crests(1);
    assert.equal(run(), 1, "a sample build with a count below its pin fails");
    crests(2);
    assert.equal(run(), 0);
    manifest();
    crests(5);
    assert.equal(run(), 0, "a full export is not failed on a pin above 0");
    photo();
    assert.equal(run(), 1, "a pin at 0 holds on a full export");
  } finally {
    rmSync(root, { recursive: true, force: true });
  }
});

test("a crest path on our own domain is read from a relative address and from our host, never from another", () => {
  assert.equal(crestPath("/crests/teams/1-104.webp"), "/crests/teams/1-104.webp");
  assert.equal(crestPath("/crests/teams/1-104.webp?v=2"), "/crests/teams/1-104.webp");
  assert.equal(crestPath("https://matchdaypilot.com/crests/leagues/9-104.webp"), "/crests/leagues/9-104.webp");
  assert.equal(crestPath("//matchdaypilot.com/crests/leagues/9-104.webp"), "/crests/leagues/9-104.webp");
  assert.equal(crestPath("https://cdn.example.com/crests/teams/1-104.webp"), null);
  assert.equal(crestPath("/assets/crest.png"), null);
  assert.equal(imageKind("/crests/teams/1-104.webp"), "ours");
});

test("the crest paths of a page are collected from img, social cards and JSON-LD", () => {
  const counts = countImages(
    '<img src="/crests/teams/1-104.webp"><meta property="og:image" content="https://matchdaypilot.com/crests/teams/2-104.webp">' +
      '<script type="application/ld+json">{"logo":"https://matchdaypilot.com/crests/leagues/9-104.webp"}</script>',
    "/en/x/", emptyImageCounts(),
  );
  assert.deepEqual([...counts.crestPaths].sort(), ["/crests/leagues/9-104.webp", "/crests/teams/1-104.webp", "/crests/teams/2-104.webp"]);
  assert.equal(counts.providerImage, 0);
});

test("a full export fails on a crest path that is no file under dist, and a sample build only reports it", () => {
  const paths = new Set(["/crests/teams/1-104.webp", "/crests/teams/2-104.webp"]);
  const has = (p) => p === "/crests/teams/1-104.webp";
  const full = checkCrestFiles(paths, { exists: has, fullBuild: true });
  assert.equal(full.missing, 1);
  assert.match(full.issues[0], /1 crest path\(s\) named by the pages are no file under dist\/ \(first: \/crests\/teams\/2-104\.webp\)/);
  assert.deepEqual(checkCrestFiles(paths, { exists: has, fullBuild: false }), { issues: [], missing: 1 });
  assert.deepEqual(checkCrestFiles(paths, { exists: () => true, fullBuild: true }), { issues: [], missing: 0 });
});

test("main checks the crest files against dist: a full export fails without them and passes with them", (t) => {
  const root = mkdtempSync(join(tmpdir(), "check-built-pages-crest-"));
  try {
    mkdirSync(join(root, "data"), { recursive: true });
    mkdirSync(join(root, "dist", "en"), { recursive: true });
    writeFileSync(join(root, "dist", "en", "index.html"), '<html><body><img src="/crests/teams/1-104.webp"></body></html>');
    const manifest = () => writeFileSync(join(root, "data", "manifest.json"), JSON.stringify(
      { counts: { fixture: 0 }, source_counts: { fixtures_unplayed: 0, fixtures_played: 0 } }));
    const errors = t.mock.method(console, "error", () => {});
    t.mock.method(console, "log", () => {});
    assert.equal(main(join(root, "dist"), join(root, "data")), 0, "a sample build only reports it");
    manifest();
    assert.equal(main(join(root, "dist"), join(root, "data")), 1);
    assert.ok(errors.mock.calls.some((c) => /crest sync did not copy them/.test(c.arguments[0])));
    mkdirSync(join(root, "dist", "crests", "teams"), { recursive: true });
    writeFileSync(join(root, "dist", "crests", "teams", "1-104.webp"), "x");
    errors.mock.resetCalls();
    assert.equal(main(join(root, "dist"), join(root, "data")), 0, errors.mock.calls.map((c) => c.arguments[0]).join("\n"));
  } finally {
    rmSync(root, { recursive: true, force: true });
  }
});

test("a page with no round at all is an issue, not a pass", () => {
  assert.match(checkFixturesPage("<html><body></body></html>", "p")[0], /no round on the page/);
});
