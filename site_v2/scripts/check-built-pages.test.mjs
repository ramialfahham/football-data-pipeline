// Regression coverage for check-built-pages.mjs. A build gate whose own logic is untested can
// silently lose a check, and a lost check reads exactly like a clean run. String literals only, no
// synthetic dist/ tree, for the reasons audit-seo.test.mjs gives.

import { test } from "node:test";
import assert from "node:assert/strict";
import {
  checkFixturesPage, checkMatchPageCount, rounds, FIXTURES_PAGE, MATCH_PAGE,
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

test("the URL shapes: a match page and a fixtures page, nothing else", () => {
  assert.ok(MATCH_PAGE.test("/en/bundesliga/matches/2026-09-18-a-vs-b/"));
  assert.ok(!MATCH_PAGE.test("/en/bundesliga/matches/"));
  assert.ok(FIXTURES_PAGE.test("/fi/bundesliga/fixtures/"));
  assert.ok(!FIXTURES_PAGE.test("/en/bundesliga/"));
  assert.ok(!MATCH_PAGE.test("/en/bundesliga/fixtures/"));
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
