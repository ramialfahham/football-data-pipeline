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
  checkFixturesPage, checkMatchPageCount, checkMatchRowLinks, checkMatchRowsFound, checkRankingsPage, boards, isZeroValue,
  main, matchRows, renderedBoards, rounds, checkTabPagesFound, FIXTURES_PAGE, MATCH_PAGE, RANKINGS_PAGE,
  checkTeamPage, checkTeamRowsFound, teamRankRows, TEAM_PAGE,
} from "./check-built-pages.mjs";

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
// value with the shown rank under it.
function leagueRow(metric, value, rank, { nonkey = false } = {}) {
  return (
    `<div class="rs-row${nonkey ? " nonkey" : ""}" data-metric="${metric}"><span class="rs-name">x</span>` +
    `<span class="rs-strip"><span class="rs-line"></span><span class="rs-dir">better</span></span>` +
    `<span class="rs-val">${value}<small>${rank}</small></span></div>`
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

test("a page with no round at all is an issue, not a pass", () => {
  assert.match(checkFixturesPage("<html><body></body></html>", "p")[0], /no round on the page/);
});
