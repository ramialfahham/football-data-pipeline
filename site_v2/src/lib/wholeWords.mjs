// A word joined by a hyphen never breaks at the hyphen: each word of a page's body text with a
// letter, a hyphen and a letter in it is wrapped in the no-break span, so the word moves whole to the
// next line while the text a reader copies, searches or a search engine indexes keeps its real
// hyphen. Only text between tags inside <body> changes. Tags and attributes stay as they are, and so
// does everything inside the elements below: raw text, SVG text (a span is not SVG), a select's
// options (a span is dropped there) and content that is not rendered as it stands.

const RAW = new Set(["script", "style", "textarea", "title"]);
const SKIP = new Set(["svg", "select", "template", "noscript", "math"]);
const JOINED = /[\p{L}\p{M}]-[\p{L}\p{M}]/u;
const TOKEN = /<!--[\s\S]*?-->|<\/?([A-Za-z][\w:-]*)[^>]*>|[^<]+|</g;
const NB = /\sclass\s*=\s*["'](?:[^"']*\s)?nb[\s"']/i;

const keep = (text) => text.replace(/\S+/g, (word) => (JOINED.test(word) ? `<span class="nb">${word}</span>` : word));

/** The page with every hyphen-joined word of its body text kept whole. */
export function keepHyphenWords(html) {
  const open = html.search(/<body[\s>]/i);
  if (open < 0) return html;
  let out = html.slice(0, open);
  let skip = [];
  // Each open span, and whether it is already a no-break span, whose text needs no second one.
  const spans = [];
  TOKEN.lastIndex = open;
  for (let m = TOKEN.exec(html); m; m = TOKEN.exec(html)) {
    const [part, tag] = m;
    if (!tag) {
      out += !skip.length && !spans.includes(true) && part !== "<" && !part.startsWith("<!--") ? keep(part) : part;
      continue;
    }
    out += part;
    const name = tag.toLowerCase();
    const closing = part.startsWith("</");
    if (name === "span") {
      if (closing) spans.pop();
      else if (!part.endsWith("/>")) spans.push(NB.test(part));
    } else if (!closing && RAW.has(name)) {
      const end = new RegExp(`</${name}`, "gi");
      end.lastIndex = TOKEN.lastIndex;
      const found = end.exec(html);
      const stop = found ? found.index : html.length;
      out += html.slice(TOKEN.lastIndex, stop);
      TOKEN.lastIndex = stop;
    } else if (SKIP.has(name) && !part.endsWith("/>")) {
      if (!closing) skip.push(name);
      else if (skip.includes(name)) skip = skip.slice(0, skip.lastIndexOf(name));
    } else if (closing && name === "body") {
      return out + html.slice(TOKEN.lastIndex);
    }
  }
  return out;
}
