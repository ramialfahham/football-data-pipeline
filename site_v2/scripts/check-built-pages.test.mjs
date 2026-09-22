// Regression coverage for check-built-pages.mjs. A build gate whose own logic is untested can
// silently lose a check, and a lost check reads exactly like a clean run. String literals only, no
// synthetic dist/ tree, for the reasons audit-seo.test.mjs gives.

import { test } from "node:test";
import assert from "node:assert/strict";
import {
  checkFixturesPage, checkMatchPageCount, checkStatsPage, boards, isZeroValue, rounds,
  FIXTURES_PAGE, MATCH_PAGE, STATS_PAGE,
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
  assert.ok(!MATCH_PAGE.test("/en/bundesliga/matches/"));
  assert.ok(FIXTURES_PAGE.test("/fi/bundesliga/fixtures/"));
  assert.ok(!FIXTURES_PAGE.test("/en/bundesliga/"));
  assert.ok(!MATCH_PAGE.test("/en/bundesliga/fixtures/"));
  assert.ok(STATS_PAGE.test("/de/bundesliga/stats/"));
  assert.ok(!STATS_PAGE.test("/de/stats/goals/") && !STATS_PAGE.test("/de/bundesliga/"));
});

// A board as RankingBoard.astro emits it: the head with the name (and the note on an ascending
// board), then the rows — a linked row unless told otherwise.
function board(name, values, { asc = false, inert = false } = {}) {
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
    `${asc ? '<span class="bnote">(fewest first)</span>' : ""}</span><span class="h"></span></div>${rows}</div></div>`
  );
}

test("a rankings page splits into its boards, and a zero reads as zero in every locale", () => {
  assert.equal(boards(board("A", ["1"]) + board("B", ["2"])).length, 2);
  for (const z of ["0", "0.0", "0,0", "0%", "0 %"]) assert.ok(isZeroValue(z), z);
  for (const nz of ["0.5", "10", "1,0", "100%", "–"]) assert.ok(!isZeroValue(nz), nz);
});

test("the board rules: one to five linked rows, no zero on a most-first board, the note only on an ascending one", () => {
  const good = board("Goals per match", ["3.5", "3.0", "2.8", "2.5", "2.5"]) +
    board("Goals against per match", ["0.5", "0.5", "0.8"], { asc: true }) +
    board("Red cards", ["1", "1", "1"]);
  assert.deepEqual(checkStatsPage(good, "p", { boards: 3, ascending: 1 }), []);
  assert.deepEqual(checkStatsPage(good, "p"), [], "without the payload the boards are checked on their own");
  // six rows: the cut failed upstream
  assert.match(checkStatsPage(board("X", ["6", "5", "4", "3", "2", "1"]), "p")[0], /6 row\(s\), expected 1 to 5/);
  // a zero ranked on a most-first board
  assert.match(checkStatsPage(board("Red cards", ["1", "0"]), "p")[0], /ranks a zero \(0\) on a most-first board/);
  // a zero on a fewest-first board is the top row, not an issue
  assert.deepEqual(checkStatsPage(board("Goals against per match", ["0.0", "0.5"], { asc: true }), "p"), []);
  // an inert row
  assert.match(checkStatsPage(board("X", ["1"], { inert: true }), "p")[0], /is not a link/);
  // the page disagrees with the payload it was built from
  const issues = checkStatsPage(good, "p", { boards: 4, ascending: 2 });
  assert.ok(issues.some((i) => /3 board\(s\) on the page, the payload served 4/.test(i)));
  assert.ok(issues.some((i) => /1 board\(s\) say "fewest first", the payload ranks 2 ascending/.test(i)));
  // an empty board wrapper
  assert.match(checkStatsPage(board("X", []), "p")[0], /0 row\(s\)/);
  assert.match(checkStatsPage("<html></html>", "p")[0], /no board on the page/);
});

test("match pages equal payloads times locales, and the manifest ties them to the warehouse", () => {
  assert.deepEqual(checkMatchPageCount({ matchPages: 6, payloadFiles: 2 }), []);
  assert.match(checkMatchPageCount({ matchPages: 5, payloadFiles: 2 })[0], /5 emitted, 6 expected/);
  const manifest = { counts: { fixture: 2 }, source_counts: { fixtures_unplayed: 2 } };
  assert.deepEqual(checkMatchPageCount({ matchPages: 6, payloadFiles: 2, manifest }), []);
  const sampled = { counts: { fixture: 2 }, source_counts: { fixtures_unplayed: 5022 } };
  assert.match(checkMatchPageCount({ matchPages: 6, payloadFiles: 2, manifest: sampled })[0], /held 5022 .* wrote 2/);
  const short = { counts: { fixture: 3 }, source_counts: { fixtures_unplayed: 3 } };
  assert.match(checkMatchPageCount({ matchPages: 6, payloadFiles: 2, manifest: short })[0], /3 fixture payload\(s\) written, only 2 on disk/);
  // the committed sample beside a full export: more files than written is not a gap
  const beside = { counts: { fixture: 2 }, source_counts: { fixtures_unplayed: 2 } };
  assert.deepEqual(checkMatchPageCount({ matchPages: 9, payloadFiles: 3, manifest: beside }), []);
  const blind = { counts: { fixture: 2 }, source_counts: {} };
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

test("every unplayed row is a link and no played row is", () => {
  assert.deepEqual(checkFixturesPage(round(4, { checked: true, rows: ["unplayed", "unplayed", "played"] }), "p"), []);
  // the same rows with class before href, and an unrelated <a> and <div> on the page: no difference
  const swapped = round(4, { checked: true }).replace("<section>",
    '<section><a class="fxrow" href="/en/x/matches/s/"></a><a class="lnk" href="/en/">Home</a><div class="dh">Fri</div>');
  assert.deepEqual(checkFixturesPage(swapped, "p"), []);
  assert.match(checkFixturesPage(round(4, { checked: true, rows: ["unplayed-inert"] }), "p")[0], /an unplayed row is not a link/);
  assert.match(checkFixturesPage(round(4, { checked: true, rows: ["played-linked"] }), "p")[0], /a played row is a link/);
});

test("a page with no round at all is an issue, not a pass", () => {
  assert.match(checkFixturesPage("<html><body></body></html>", "p")[0], /no round on the page/);
});
