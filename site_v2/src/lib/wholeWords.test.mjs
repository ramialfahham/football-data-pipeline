// Pins what the build step changes: a hyphen-joined word of the body text is wrapped whole, and
// nothing else moves — the head, attributes, scripts, SVG text and options stay as they are, and the
// text itself keeps its real hyphen.

import { test } from "node:test";
import assert from "node:assert/strict";
import { keepHyphenWords } from "./wholeWords.mjs";

const page = (body, head = "<title>Paris Saint-Germain</title>") => `<!DOCTYPE html><html><head>${head}</head><body>${body}</body></html>`;
const bodyOf = (html) => html.slice(html.indexOf("<body>") + 6, html.indexOf("</body>"));
const textOf = (html) => html.replace(/<[^>]*>/g, "");

test("a hyphen-joined word is wrapped whole, the rest of the text as it is", () => {
  const out = keepHyphenWords(page('<span class="nm">Paris Saint-Germain FC</span>'));
  assert.equal(bodyOf(out), '<span class="nm">Paris <span class="nb">Saint-Germain</span> FC</span>');
});

test("the punctuation that clings to the word stays with it", () => {
  const out = keepHyphenWords(page("<p>Spain-pelaajaan, DFB-Pokal: and Rot-Weiß.</p>"));
  assert.equal(bodyOf(out), '<p><span class="nb">Spain-pelaajaan,</span> <span class="nb">DFB-Pokal:</span> and <span class="nb">Rot-Weiß.</span></p>');
});

test("only a hyphen between two letters joins a word", () => {
  const html = page("<p>2-1 at U-21, a - b, Matchday 9 – 10</p>");
  assert.equal(keepHyphenWords(html), html);
});

test("the head, attributes, scripts, styles, SVG text and options are left as they are", () => {
  const body = '<a href="/en/teams/paris-saint-germain/" title="Saint-Germain">x</a>'
    + "<script>const s = '<b>Saint-Germain</b>';</script><style>.a-b{}</style>"
    + '<svg><text>Saint-Germain</text><svg/></svg><select><option>Saint-Germain</option></select>'
    + "<template><i>Saint-Germain</i></template><textarea>Saint-Germain</textarea>";
  const html = page(body);
  assert.equal(keepHyphenWords(html), html);
});

test("text after a skipped element is kept whole again", () => {
  const out = keepHyphenWords(page("<svg><text>Saint-Germain</text></svg><p>Al-Nassr</p>"));
  assert.equal(bodyOf(out), '<svg><text>Saint-Germain</text></svg><p><span class="nb">Al-Nassr</span></p>');
});

test("the page's text is the same before and after", () => {
  const html = page("<h1>Paris Saint-Germain</h1><p>Keski-Amerikka &amp; Etelä-Amerikka</p><!-- a-b -->");
  assert.equal(textOf(keepHyphenWords(html)), textOf(html));
});

test("a letter that grows when lowercased does not shift where a script ends", () => {
  const out = keepHyphenWords(page(`<p>${"İ".repeat(12)}</p><script>let a = 1;</script><div class="x">Al-Nassr</div>`));
  assert.equal(bodyOf(out), `<p>${"İ".repeat(12)}</p><script>let a = 1;</script><div class="x"><span class="nb">Al-Nassr</span></div>`);
});

test("a word already inside a no-break span is not wrapped again", () => {
  const html = page('<span class="nb">DFB-Pokal <span class="tc-ctx">x</span> Al-Ahli</span><span class="x nb">Rot-Weiß</span><span>Al-Nassr</span>');
  assert.equal(bodyOf(keepHyphenWords(html)), '<span class="nb">DFB-Pokal <span class="tc-ctx">x</span> Al-Ahli</span><span class="x nb">Rot-Weiß</span><span><span class="nb">Al-Nassr</span></span>');
});

test("a span whose other attribute names nb is not a no-break span", () => {
  const html = page('<span data-class="nb">Al-Nassr</span><span title="x nb">Rot-Weiß</span>');
  assert.equal(bodyOf(keepHyphenWords(html)), '<span data-class="nb"><span class="nb">Al-Nassr</span></span><span title="x nb"><span class="nb">Rot-Weiß</span></span>');
});

test("a page without a body is returned as it is", () => {
  assert.equal(keepHyphenWords("User-agent: *"), "User-agent: *");
});
