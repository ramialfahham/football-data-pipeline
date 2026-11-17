"""The parts page: every form each part in `docs/design/components.yml` takes on the built site today.

Crawls the running Astro dev server over one page of every built page type in the Pages table of
`docs/wireframes/block_standard.md`, at 375px and 1000px, collects every visible instance of every
registered part, and writes one self-contained page: a consistency report (distinct forms per kind;
the same text on one page in more than one style), then each distinct form drawn at both widths in
a frame that carries the site's own CSS, so one form per part can be picked.

    npm run dev --prefix site_v2          (or the Browser pane's `v2`)
    python scripts/parts_page.py --base http://localhost:4321
    cd design-mocks && python -m http.server 8765   ->  http://localhost:8765/parts_page.html
"""

from __future__ import annotations

import argparse
import base64
import html
import json
import mimetypes
import re
import sys
from collections import defaultdict
from html.parser import HTMLParser
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "scripts"))
import check_component_registry as ccr  # noqa: E402
import design_inventory as di  # noqa: E402

BLOCK_STANDARD = REPO / "docs" / "wireframes" / "block_standard.md"
OUT = REPO / "design-mocks" / "parts_page.html"
WIDTHS = (375, 1000)
STYLE_PROPS = (
    "font-size", "font-weight", "font-style", "text-transform", "color", "letter-spacing",
    "padding-top", "padding-right", "padding-bottom", "padding-left", "border-radius",
    "background-color", "border-top-width", "border-bottom-width", "text-align", "text-decoration-line",
    "column-gap", "row-gap", "margin-top", "margin-bottom", "white-space", "line-height", "display",
)
# Classes that follow the data or the state rather than the part's design: a result's letter, the
# winner, the active tab, the unbreakable unit, the fitted form.
STATE_CLASSES = frozenset({"nb", "fit-one", "fit-two", "W", "D", "L", "winner", "on"})
TEXT_PROPS = ("font-size", "font-weight", "font-style", "text-transform", "color", "letter-spacing")
SKELETON_IGNORED_CLASSES = frozenset({"nb", "fit-one", "fit-two"})
SKELETON_DEPTH = 2
TRIM_CHARS = 40000
GENERIC_PARTS = frozenset({"unit.unit", "fitted-block.one"})
CORE_COLOURS = ("ink", "ink-2", "muted", "accent", "pill-ink", "win", "draw", "loss", "line", "surface",
                "sunk", "page")

# A Pages-table row whose URL is a glob gets its page here: a fixed path, or the first link a
# selector finds on another page, so the pick follows whatever the local data holds.
GLOB_PICKS: dict[str, list[tuple[str, str, str | None]]] = {
    "Match page": [("Match page · next match", "/en/bundesliga/matches/", "a.fxrow:not(.played)")],
    "Team page": [("Team page · club", "/en/teams/bayern-munchen/", None),
                  ("Team page · national team", "/en/teams/germany/", None)],
    "Player pages": [],
    "Matches day page": [("Matches day page", "/en/matches/", ".mdstep a.step")],
}

KINDS: list[tuple[str, list[str]]] = [
    ("Page heading", ["page-heading.heading", "entity-header.head", "entity-header.identity"]),
    ("Section heading", ["block.heading", "split.column-head"]),
    ("Explainer", ["block.explainer", "block.tab-explainer"]),
    ("Group heading", ["group-head.head", "group-head.metric-head", "group-head.metric-name", "standings.group-head",
                       "standings.group-name", "masthead.competition"]),
    ("Competition name", ["group-head.name", "competition-row.name", "index-row.name"]),
    ("Team name", ["match-row.name", "table-row.name", "result-row.name", "comparison.team-name",
                   "masthead.team-link", "masthead.team-name", "chart.label"]),
    ("Player name", ["player-row.name"]),
    ("Date", ["date-heading.date", "match-row.kick-off", "match-row.zone", "masthead.kick-off"]),
    ("Score", ["match-row.score", "result-row.score", "masthead.score", "masthead.winner",
               "masthead.team-goals", "masthead.dash", "masthead.result-line"]),
    ("Result badge", ["chip.chip", "chip.count-chip", "form.chips", "form.win",
                      "form.draw", "form.loss"]),
    ("Position / value", ["player-row.position", "player-row.number", "table-row.ordered-by",
                          "fact-row.value", "standings.goal-difference", "standings.wdl",
                          "last-season.trend", "last-season.up", "last-season.down", "last-season.flat",
                          "last-season.now", "last-season.prev", "strip-plot.value",
                          "strip-plot.median-value", "comparison.better-value", "group-head.count",
                          "competition-row.right", "competition-row.numbers", "scatter-plot.table-value"]),
    ("Meta line", ["result-row.meta", "result-row.goal-meta", "result-row.home-away",
                   "result-row.home-away-line", "result-row.player-competition", "result-row.player-line",
                   "board.sub-line", "fact-row.context", "index-row.region", "index-row.meta",
                   "entity-header.meta", "competition-row.context", "competition-row.extra",
                   "masthead.standing", "scatter-plot.table-sub", "strip-plot.median-key"]),
    ("Label", ["fact-row.label", "chart.name", "chart.tick", "chart.note", "chart.legend",
               "metric-switch.label"]),
    ("Tab bar", ["tabs.bar", "tabs.tab", "tabs.tabs"]),
    ("Matchday picker", ["matchday-picker.picker", "matchday-picker.title", "matchday-picker.arrow"]),
    ("Filter", ["filter-bar.bar", "filter-bar.row", "filter-bar.button", "filter-bar.dropdown",
                "metric-switch.track"]),
    ("Stat tile", ["card.card", "card.number", "card.label", "card.text"]),
    ("Table head", ["table.head", "table.head-label", "standings.wdl-head", "deserved-table.shots-head",
                    "board.name", "board.name-cell"]),
    ("Row", ["match-row.sides", "table-row.row", "table-row.narrow-row", "list-row.row", "result-row.row",
             "result-row.meeting", "result-row.goal", "player-row.row", "competition-row.row",
             "fact-row.block", "strip-plot.row"]),
    ("Chevron link", ["heading-link.link", "chevron.chevron", "fold.control", "fold.link",
                      "fold.label", "breadcrumb.link"]),
    ("Crest", ["crest.crest", "crest.small", "competition-row.crest", "group-head.logo"]),
    ("Player photo", ["player-row.photo"]),
    ("Chart mark", ["chart.mark", "chart.other-mark", "chart.team-mark", "chart.bar", "chart.line",
                    "chart.axis", "comparison.better-bar", "strip-plot.band"]),
    ("Site chrome", ["header.brand", "header.brand-iq", "header.search-field", "header.search-button",
                     "header.menu", "header.current", "footer.brand", "footer.meta", "footer.imprint",
                     "breadcrumb.level", "breadcrumb.current", "breadcrumb.separator"]),
]

COLLECT_JS = r"""
({parts, props, tokens}) => {
  const ids = window.__partsIds || (window.__partsIds = new WeakMap());
  window.__partsNext = window.__partsNext || 1;
  const idOf = (n) => { if (!ids.has(n)) ids.set(n, window.__partsNext++); return ids.get(n); };
  const DEV = /^data-astro-source-/;
  const attrsOf = (el) => [...el.attributes].filter((a) => !DEV.test(a.name)).map((a) => [a.name, a.value]);
  const styleOf = (el, list) => { const cs = getComputedStyle(el); const o = {}; for (const p of list) o[p] = cs.getPropertyValue(p); return o; };
  const visible = (el) => el.checkVisibility({checkVisibilityCSS: true}) && el.getClientRects().length > 0;
  const clean = (root) => {
    for (const n of [root, ...root.querySelectorAll("*")]) for (const a of [...n.attributes]) if (DEV.test(a.name)) n.removeAttribute(a.name);
  };
  const syncInputs = (src, clone) => {
    const a = [...src.querySelectorAll("input")], b = [...clone.querySelectorAll("input")];
    a.forEach((inp, i) => { if (inp.checked) b[i].setAttribute("checked", ""); else b[i].removeAttribute("checked"); });
  };
  const inputHtml = (inp) => { const c = inp.cloneNode(false); clean(c); if (inp.checked) c.setAttribute("checked", ""); else c.removeAttribute("checked"); return c.outerHTML; };
  const htmlOf = (el) => {
    const c = el.cloneNode(true); syncInputs(el, c); clean(c);
    let trimmed = false;
    if (c.outerHTML.length > %TRIM%) {
      for (const n of [...c.querySelectorAll("*")].reverse()) {
        const kids = [...n.children];
        if (kids.length > 6) { kids.slice(6).forEach((k) => k.remove()); trimmed = true; }
      }
    }
    return {html: c.outerHTML, trimmed};
  };
  const chainOf = (el) => {
    const out = [];
    for (let a = el.parentElement; a; a = a.parentElement) {
      out.unshift({tag: a.tagName.toLowerCase(), attrs: attrsOf(a),
                   inputs: [...a.children].filter((k) => k.tagName === "INPUT").map(inputHtml)});
    }
    return out;
  };
  const owner = new Map();
  const instances = [];
  for (const {key, selector} of parts) {
    let found;
    try { found = document.querySelectorAll(selector); } catch (e) { continue; }
    for (const el of found) {
      if (el.closest("astro-dev-toolbar")) continue;
      const id = idOf(el);
      if (!owner.has(el)) owner.set(el, []);
      owner.get(el).push(key);
      if (!visible(el)) { instances.push({key, id, visible: false}); continue; }
      const h = htmlOf(el);
      instances.push({key, id, visible: true, style: styleOf(el, props), html: h.html, trimmed: h.trimmed,
                      chain: chainOf(el)});
    }
  }
  const runs = [];
  const SKIP = "script, style, astro-dev-toolbar, .site-header, .site-footer, nav.trail";
  const GENERIC = new Set(%GENERIC%);
  const blockOf = (el) => { for (let a = el; a; a = a.parentElement) { const d = getComputedStyle(a).display; if (d !== "inline" && d !== "contents") return a; } return document.body; };
  const labelOf = (el) => {
    for (let a = el; a; a = a.parentElement) {
      const keys = owner.get(a);
      if (keys && keys.some((k) => !GENERIC.has(k))) return keys.filter((k) => !GENERIC.has(k)).join(" | ");
    }
    return "unregistered " + el.tagName.toLowerCase() + (el.classList.length ? "." + [...el.classList].join(".") : "");
  };
  let run = null;
  const flush = () => { if (run && run.text.replace(/\s+/g, " ").trim()) runs.push(run); run = null; };
  const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
  for (let t = walker.nextNode(); t; t = walker.nextNode()) {
    const el = t.parentElement;
    if (!el || el.closest(SKIP) || !visible(el)) continue;
    const blank = !t.nodeValue.trim();
    if (!blank) {
      const r = document.createRange(); r.selectNodeContents(t); const box = r.getBoundingClientRect();
      if (box.width <= 1 || box.height <= 1) continue;
    }
    const style = styleOf(el, %TEXT_PROPS%);
    const sk = JSON.stringify(style), block = blockOf(el);
    const bb = block.getBoundingClientRect();
    if (bb.width <= 1 || bb.height <= 1) continue;
    if (run && run.block === block && run.sk === sk) { run.text += t.nodeValue; continue; }
    if (blank) continue;
    flush();
    run = {id: idOf(t), text: t.nodeValue, style, sk, block, part: labelOf(el)};
  }
  flush();
  for (const r of runs) { r.text = r.text.replace(/\s+/g, " ").trim(); delete r.sk; delete r.block; }
  const probe = document.createElement("span"); document.body.appendChild(probe);
  const colours = {};
  for (const name of tokens) { probe.style.color = "var(--" + name + ")"; const v = getComputedStyle(probe).color; probe.style.color = ""; if (v) colours[v] = colours[v] || name; }
  probe.remove();
  return {instances, runs, colours};
}
""".replace("%TRIM%", str(TRIM_CHARS)).replace("%TEXT_PROPS%", json.dumps(TEXT_PROPS)).replace(
    "%GENERIC%", json.dumps(sorted(GENERIC_PARTS)))

CSS_JS = """
() => [...document.querySelectorAll("style")].filter((s) => !s.closest("astro-dev-toolbar")).map((s) => s.textContent)
"""

TABS_JS = """
() => [...document.querySelectorAll("input.tab-in")].map((i) => {
  const l = document.querySelector('label[for="' + i.id + '"]');
  return {id: i.id, label: l ? l.textContent.replace(/\\s+/g, " ").trim() : i.id};
})
"""

FIDELITY_JS = """
(props) => [...document.querySelectorAll("iframe.parts-frame")].map((f) => {
  const t = window.partsTarget(f);
  if (!t) return {form: f.dataset.form, w: f.dataset.w, style: null};
  const cs = f.contentWindow.getComputedStyle(t); const o = {};
  for (const p of props) o[p] = cs.getPropertyValue(p);
  return {form: f.dataset.form, w: f.dataset.w, style: o};
})
"""


class PagesError(Exception):
    pass


def pages_from_table(text: str, picks: dict = GLOB_PICKS) -> list[dict]:
    """The pages to crawl: every built row of the Pages table, a glob row through `picks`."""
    rows = di._tables(text).get("Pages")
    if not rows:
        raise PagesError("block_standard.md has no Pages table")
    head, body = rows[0], rows[1:]
    col = {name: i for i, name in enumerate(head)}
    out, missing = [], []
    for r in body:
        if r[col["Kind"]] != "built":
            continue
        row, url = r[col["Page"]], di._strip_code(r[col["URL"]])
        if "*" in url:
            if row not in picks:
                missing.append(row)
                continue
            for label, path, link in picks[row]:
                out.append({"row": row, "label": label, "path": path, "link": link})
            continue
        path = "/" + re.sub(r"index\.html$", "", url)
        out.append({"row": row, "label": row, "path": path, "link": None})
    if missing:
        raise PagesError("Pages rows with a glob URL and no pick: " + ", ".join(missing))
    return out


def registry_parts(reg: dict) -> list[dict]:
    """Every part of every component: its key, the registry check's selector and its element name."""
    out = []
    for cid, comp in reg["components"].items():
        for pid, part in comp["parts"].items():
            out.append({"key": "%s.%s" % (cid, pid), "selector": ccr._selector(part),
                        "name": part.get("element") or "%s · %s" % (comp["name"], pid)})
    return out


def kind_of(keys: list[str], kinds: list[tuple[str, list[str]]] = KINDS) -> tuple[dict, list[str]]:
    """(part key -> kind, part keys in no kind); a kind naming a key the registry lacks is an error."""
    known = set(keys)
    placed = {}
    for kind, members in kinds:
        for k in members:
            if k not in known:
                raise KeyError("kind %r names %r, which the registry does not have" % (kind, k))
            placed[k] = kind
    return placed, [k for k in keys if k not in placed]


class _Tree(HTMLParser):
    VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "source",
            "track", "wbr"}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.root = {"tag": "#root", "cls": (), "kids": []}
        self.stack = [self.root]

    def handle_starttag(self, tag, attrs):
        cls = tuple(sorted(c for c in (dict(attrs).get("class") or "").split()
                           if c not in SKELETON_IGNORED_CLASSES))
        node = {"tag": tag, "cls": cls, "kids": []}
        self.stack[-1]["kids"].append(node)
        if tag not in self.VOID:
            self.stack.append(node)

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        if tag not in self.VOID:
            self.stack.pop()

    def handle_endtag(self, tag):
        for i in range(len(self.stack) - 1, 0, -1):
            if self.stack[i]["tag"] == tag:
                del self.stack[i:]
                return


def _sig(node: dict, depth: int) -> str:
    own = node["tag"] + "".join("." + c for c in node["cls"])
    if depth == 0 or node["tag"] == "svg" or not node["kids"]:
        return own
    kids = []
    for k in node["kids"]:
        if k["tag"] == "span" and not k["cls"] and not k["kids"]:
            continue
        s = _sig(k, depth - 1)
        if not kids or kids[-1] != s:
            kids.append(s)
    return own + ("[" + ",".join(kids) + "]" if kids else "")


def skeleton(markup: str, depth: int = SKELETON_DEPTH) -> str:
    """An element's structure without its text: tags and classes `depth` levels down, a run of
    identical children counted once, the content-driven classes (unbreakable unit, fitted form)
    left out."""
    t = _Tree()
    t.feed(markup)
    t.close()
    if not t.root["kids"]:
        return ""
    return _sig(t.root["kids"][0], depth)


def child_tokens(markup: str) -> set[str]:
    """The kinds of element inside a part: each descendant's classes as `.class`, an image or icon
    without a class as its tag; the data-driven and state classes left out."""
    t = _Tree()
    t.feed(markup)
    t.close()
    out: set[str] = set()
    stack = list(t.root["kids"][0]["kids"]) if t.root["kids"] else []
    while stack:
        n = stack.pop()
        cls = [c for c in n["cls"] if c not in STATE_CLASSES]
        if cls:
            out.update("." + c for c in cls)
        elif n["tag"] in ("img", "svg"):
            out.add(n["tag"])
        if n["tag"] != "svg":
            stack.extend(n["kids"])
    return out


def part_differences(instances: list[dict]) -> dict:
    """How one part differs between the pages it is on. `children`: each child element present on
    some of those pages and missing on others, as (element, pages with it, pages without it).
    `look`: per width, each style property whose set of values differs from page to page, as
    (width, property, {value: pages}). A difference inside every page alike (a tab's active and
    resting state) is not a difference between pages."""
    tokens: dict[str, set[str]] = defaultdict(set)
    values: dict[tuple, dict[str, set[str]]] = defaultdict(lambda: defaultdict(set))
    for inst in instances:
        if not inst["captures"]:
            continue
        page = inst["page"]
        tokens.setdefault(page, set())
        for w, cap in inst["captures"].items():
            tokens[page] |= child_tokens(cap["html"])
            for prop, v in cap["style"].items():
                values[(w, prop)][page].add(v)
    pages = sorted(tokens)
    children = []
    for tok in sorted(set().union(*tokens.values()) if tokens else ()):
        have = [p for p in pages if tok in tokens[p]]
        if len(have) < len(pages):
            children.append((tok, have, [p for p in pages if p not in have]))
    look = []
    for (w, prop), per_page in sorted(values.items()):
        if len(per_page) < 2 or len({frozenset(v) for v in per_page.values()}) < 2:
            continue
        by_value: dict[str, list[str]] = defaultdict(list)
        for p in sorted(per_page):
            for v in sorted(per_page[p]):
                by_value[v].append(p)
        look.append((w, prop, dict(by_value)))
    return {"pages": pages, "children": children, "look": look}


def form_differences(forms: list[dict]) -> dict:
    """What tells a part's forms apart: each child element some forms have and others lack, and
    each style property with more than one value, per width, as {value: form numbers} (1-based)."""
    children = []
    toks = [set().union(*(child_tokens(c["html"]) for c in f["sample"]["captures"].values())) for f in forms]
    for tok in sorted(set().union(*toks) if toks else ()):
        have = [n for n, t in enumerate(toks, 1) if tok in t]
        if len(have) < len(forms):
            children.append((tok, have))
    look = []
    for w in WIDTHS:
        for prop in STYLE_PROPS:
            by_value: dict[str, list[int]] = defaultdict(list)
            for n, f in enumerate(forms, 1):
                cap = f["sample"]["captures"].get(w)
                if cap:
                    by_value[cap["style"][prop]].append(n)
            if len(by_value) > 1:
                look.append((w, prop, dict(sorted(by_value.items()))))
    return {"children": children, "look": look}


def _style_key(style: dict | None) -> tuple | None:
    return None if style is None else tuple(sorted(style.items()))


def distinct_forms(instances: list[dict]) -> list[dict]:
    """Group a part's instances into forms: the same structure and the same computed style at each
    width. An instance is {page, state, captures: {width: {style, html, chain, trimmed}}}; a form
    keeps its first instance as the one drawn and every page it was seen on."""
    forms: dict[tuple, dict] = {}
    for inst in instances:
        caps = inst["captures"]
        ref = caps.get(max(caps)) if caps else None
        if ref is None:
            continue
        key = (skeleton(ref["html"]),) + tuple(_style_key((caps.get(w) or {}).get("style")) for w in WIDTHS)
        form = forms.get(key)
        if form is None:
            form = forms[key] = {"key": key, "sample": inst, "count": 0, "where": {}}
        form["count"] += 1
        place = inst["page"] + (" · " + inst["state"] if inst.get("state") else "")
        form["where"].setdefault(place, set()).update(caps)
    return sorted(forms.values(), key=lambda f: -f["count"])


def _norm_text(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def same_text_findings(runs: list[dict], min_len: int = 3) -> list[dict]:
    """Every text shown on one page, at one width, in more than one text style. A run is
    {page, width, text, style, part}; text shorter than `min_len` or without a letter is left out.
    Findings repeating at several widths are merged."""
    by = defaultdict(lambda: defaultdict(set))
    for r in runs:
        text = _norm_text(r["text"])
        if len(text) < min_len or not re.search(r"[^\W\d_]", text):
            continue
        style = tuple((p, r["style"].get(p, "")) for p in TEXT_PROPS)
        by[(r["page"], r["width"], text)][style].add(r["part"])
    merged: dict[tuple, dict] = {}
    for (page, width, text), styles in by.items():
        if len(styles) < 2:
            continue
        variants = tuple(sorted((s, tuple(sorted(p))) for s, p in styles.items()))
        f = merged.setdefault((page, text, variants), {"page": page, "text": text, "widths": [],
                                                       "variants": [{"style": dict(s), "parts": list(p)}
                                                                    for s, p in variants]})
        f["widths"].append(width)
    for f in merged.values():
        f["widths"].sort()
    return sorted(merged.values(), key=lambda f: (f["page"], f["text"]))


def fidelity_mismatches(captured: dict, rendered: dict | None) -> list[str]:
    """The properties whose re-rendered value differs from the live page's; no element is one."""
    if rendered is None:
        return ["not rendered"]
    return ["%s %s → %s" % (p, captured[p], rendered.get(p)) for p in captured if rendered.get(p) != captured[p]]


def _inline_urls(css: str, fetch) -> str:
    def repl(m):
        url = m.group(2)
        if not url.startswith("/") or url.startswith("//"):
            return m.group(0)
        data = fetch(url)
        if data is None:
            return m.group(0)
        mime = mimetypes.guess_type(url.split("?")[0])[0] or ("font/woff2" if ".woff2" in url else "application/octet-stream")
        return "url(data:%s;base64,%s)" % (mime, base64.b64encode(data).decode())
    return re.sub(r"""url\((['"]?)([^'")]+)\1\)""", repl, css)


def crawl(base: str, pages: list[dict], parts: list[dict], tokens: list[str]) -> dict:
    from playwright.sync_api import sync_playwright

    sheets: list[str] = []
    sheet_ids: dict[str, int] = {}
    bundles: list[tuple[int, ...]] = []
    url_cache: dict[str, bytes | None] = {}
    inst: dict[tuple, dict] = {}
    runs: list[dict] = []
    crawled: list[dict] = []
    colours: dict[str, str] = {}
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        ctx = browser.new_context(viewport={"width": WIDTHS[0], "height": 900}, color_scheme="light")
        page = ctx.new_page()

        def fetch(url):
            if url not in url_cache:
                r = ctx.request.get(base + url)
                url_cache[url] = r.body() if r.ok else None
            return url_cache[url]

        for spec in pages:
            path = spec["path"]
            if spec["link"]:
                page.set_viewport_size({"width": WIDTHS[-1], "height": 900})
                page.goto(base + path, wait_until="networkidle")
                href = page.eval_on_selector(spec["link"], "a => a.getAttribute('href')")
                path = href
            page.set_viewport_size({"width": WIDTHS[0], "height": 900})
            resp = page.goto(base + path, wait_until="networkidle")
            if not resp or not resp.ok:
                raise SystemExit("%s: %s answered %s" % (spec["label"], path, resp.status if resp else "nothing"))
            page.wait_for_timeout(300)
            bundle = []
            for css in page.evaluate(CSS_JS):
                css = _inline_urls(css, fetch)
                if css not in sheet_ids:
                    sheet_ids[css] = len(sheets)
                    sheets.append(css)
                bundle.append(sheet_ids[css])
            if tuple(bundle) not in bundles:
                bundles.append(tuple(bundle))
            bundle_id = bundles.index(tuple(bundle))
            tabs = page.evaluate(TABS_JS) or [None]
            crawled.append({"label": spec["label"], "row": spec["row"], "path": path,
                            "states": [t["label"] for t in tabs if t]})
            for tab in tabs:
                state = ""
                if tab:
                    page.evaluate("id => { const i = document.getElementById(id); i.checked = true;"
                                  " i.dispatchEvent(new Event('change', {bubbles: true})); }", tab["id"])
                    state = tab["label"]
                for w in WIDTHS:
                    page.set_viewport_size({"width": w, "height": 900})
                    page.wait_for_timeout(250)
                    got = page.evaluate(COLLECT_JS, {"parts": parts, "props": list(STYLE_PROPS), "tokens": tokens})
                    colours.update({k: v for k, v in got["colours"].items() if k not in colours})
                    for i in got["instances"]:
                        rec = inst.setdefault((spec["label"], i["key"], i["id"]), {
                            "page": spec["label"], "key": i["key"], "state": "", "bundle": bundle_id,
                            "captures": {}})
                        if i["visible"] and w not in rec["captures"]:
                            if not rec["captures"]:
                                rec["state"] = state
                            rec["captures"][w] = {k: i[k] for k in ("style", "html", "chain", "trimmed")}
                    for r in got["runs"]:
                        runs.append({"page": spec["label"], "width": w, "id": r["id"], "text": r["text"],
                                     "style": r["style"], "part": r["part"]})
        browser.close()
    seen_runs, unique_runs = set(), []
    for r in runs:
        k = (r["page"], r["width"], r["id"])
        if k not in seen_runs:
            seen_runs.add(k)
            unique_runs.append(r)
    return {"sheets": sheets, "bundles": bundles, "instances": list(inst.values()), "runs": unique_runs,
            "pages": crawled, "colours": colours}


def _attrs(pairs) -> str:
    return "".join(' %s="%s"' % (n, html.escape(v, quote=True)) for n, v in pairs)


def frame_doc(capture: dict) -> tuple[str, int]:
    """The frame's document: the ancestors as shallow clones with their inputs, then the element.
    Returns the markup and how deep the element sits under <body>."""
    chain = capture["chain"]
    html_el, body_el, rest = chain[0], chain[1], chain[2:]
    out = ['<!doctype html><html%s><head><meta charset="utf-8">'
           '<meta name="viewport" content="width=device-width, initial-scale=1"></head>' % _attrs(html_el["attrs"]),
           "<body%s>" % _attrs(body_el["attrs"]), "".join(body_el["inputs"])]
    for a in rest:
        out.append("<%s%s>%s" % (a["tag"], _attrs(a["attrs"]), "".join(a["inputs"])))
    out.append(capture["html"])
    for a in reversed(rest):
        out.append("</%s>" % a["tag"])
    out.append("</body></html>")
    return "".join(out), len(rest)


def _text_line(style: dict, colours: dict) -> str:
    bits = [style["font-size"], "weight " + style["font-weight"], colours.get(style["color"], style["color"])]
    if style["text-transform"] != "none":
        bits.append(style["text-transform"])
    if style["font-style"] != "normal":
        bits.append(style["font-style"])
    if style["letter-spacing"] != "normal":
        bits.append("spacing " + style["letter-spacing"])
    return " · ".join(bits)


def _box_line(style: dict, colours: dict) -> str:
    bits = []
    bg = style["background-color"]
    if bg not in ("rgba(0, 0, 0, 0)", "transparent"):
        bits.append("on " + colours.get(bg, bg))
    pad = " ".join(style[p] for p in ("padding-top", "padding-right", "padding-bottom", "padding-left"))
    if pad != "0px 0px 0px 0px":
        bits.append("padding " + pad)
    if style["border-radius"] != "0px":
        bits.append("radius " + style["border-radius"])
    lines = [style[p] for p in ("border-top-width", "border-bottom-width")]
    if lines != ["0px", "0px"]:
        bits.append("line top %s, bottom %s" % tuple(lines))
    if style["text-decoration-line"] != "none":
        bits.append(style["text-decoration-line"])
    if style["text-align"] not in ("start", "left"):
        bits.append("aligned " + style["text-align"])
    gaps = [style[p] for p in ("column-gap", "row-gap")]
    if gaps != ["normal", "normal"]:
        bits.append("gap %s / %s" % tuple(gaps))
    margins = [style[p] for p in ("margin-top", "margin-bottom")]
    if margins != ["0px", "0px"]:
        bits.append("margin top %s, bottom %s" % tuple(margins))
    return " · ".join(bits)


def _value(prop: str, v: str, colours: dict) -> str:
    return colours.get(v, v) if prop in ("color", "background-color") else v


def _short_places(places: list[str], keep: int = 3) -> str:
    return ", ".join(places[:keep]) + (" +%d more" % (len(places) - keep) if len(places) > keep else "")


PAGE_CSS = """
.parts-page{font:14px/1.45 system-ui,sans-serif;color:#1b1f24;background:#f4f5f7;margin:0;padding:16px}
.parts-page h1{font-size:22px;margin:0 0 4px}.parts-page h2{font-size:18px;margin:32px 0 8px}
.parts-page h3{font-size:15px;margin:24px 0 4px}.parts-page h4{font-size:13px;margin:14px 0 6px;color:#5b6470}
.parts-muted{color:#5b6470}.parts-small{font-size:12px}
.parts-report{max-width:1000px}.parts-scroll{overflow-x:auto}
.parts-table{border-collapse:collapse;margin:6px 0}.parts-table td,.parts-table th{border-bottom:1px solid #e3e6ea;padding:3px 12px 3px 0;text-align:left;vertical-align:top}
.parts-list li{margin:4px 0}.parts-diff{margin:4px 0 8px;padding-left:18px}
.parts-kind{margin-top:48px;border-top:2px solid #1b1f24}
.parts-strip{display:flex;flex-wrap:wrap;gap:16px;align-items:flex-start}
.parts-form{flex:none;max-width:100%;overflow-x:auto}.parts-wide{display:grid;gap:16px}
.parts-label{font-weight:600}.parts-flag{color:#a3261b}
.parts-frame{border:1px solid #c9ced5;display:block;height:60px}
"""

PAGE_JS = r"""
(() => {
  const sheet = (n) => document.getElementById("parts-css-" + n).textContent;
  const bundles = JSON.parse(document.getElementById("parts-bundles").textContent);
  window.partsTarget = (f) => {
    const doc = f.contentDocument; if (!doc || !doc.body) return null;
    let el = doc.body;
    for (let i = 0; i <= Number(f.dataset.depth); i++) {
      el = [...el.children].find((k) => k.tagName !== "INPUT" && k.tagName !== "STYLE");
      if (!el) return null;
    }
    return el;
  };
  const fit = (f) => { const d = f.contentDocument; if (d && d.documentElement) f.style.height = Math.min(1600, d.documentElement.scrollHeight + 2) + "px"; };
  const ready = (f) => { const d = f.contentDocument; return !!d && d.URL === "about:srcdoc" && d.readyState === "complete"; };
  window.partsReady = () => [...document.querySelectorAll("iframe.parts-frame")].every(ready);
  const dress = (f) => {
    const d = f.contentDocument; if (!ready(f) || d.partsDressed) return;
    d.partsDressed = true;
    for (const n of bundles[f.dataset.bundle]) { const s = d.createElement("style"); s.textContent = sheet(n); d.head.appendChild(s); }
    fit(f); setTimeout(() => fit(f), 400);
  };
  for (const f of document.querySelectorAll("iframe.parts-frame")) {
    f.addEventListener("load", () => dress(f));
    dress(f);
  }
  window.partsDressAll = () => document.querySelectorAll("iframe.parts-frame").forEach(dress);
})();
"""


def forms_of(instances: list[dict]) -> dict[str, list[dict]]:
    """Each part's distinct forms, numbered across the page in kind order; every form gets `no`."""
    by_part = defaultdict(list)
    for i in instances:
        by_part[i["key"]].append(i)
    out = {k: distinct_forms(v) for k, v in by_part.items()}
    no = 0
    for _, members in KINDS:
        for k in members:
            for f in out.get(k, []):
                no += 1
                f["no"] = no
    return out


def _diff_html(d: dict, colours: dict) -> str:
    esc = html.escape
    items = ["has %s on %s; not on %s" % (esc(tok), esc(", ".join(have)), esc(", ".join(lack)))
             for tok, have, lack in d["children"]]
    merged: dict[tuple, list[int]] = defaultdict(list)
    for w, prop, by_value in d["look"]:
        merged[(prop, tuple((v, tuple(p)) for v, p in by_value.items()))].append(w)
    for (prop, by_value), ws in merged.items():
        vals = "; ".join("%s on %s" % (esc(_value(prop, v, colours)), esc(", ".join(p))) for v, p in by_value)
        items.append("%s at %s: %s" % (esc(prop), "/".join("%dpx" % w for w in ws), vals))
    return '<ul class="parts-diff parts-small">%s</ul>' % "".join("<li>%s</li>" % i for i in items)


def _nums(ns) -> str:
    return "form " + ", ".join(str(n) for n in ns)


def _between_forms_html(d: dict, colours: dict) -> str:
    esc = html.escape
    nums = _nums
    items = ["%s in %s" % (esc(tok), nums(have)) for tok, have in d["children"]]
    merged: dict[tuple, list[int]] = defaultdict(list)
    for w, prop, by_value in d["look"]:
        merged[(prop, tuple((v, tuple(ns)) for v, ns in by_value.items()))].append(w)
    for (prop, by_value), ws in merged.items():
        vals = "; ".join("%s in %s" % (esc(_value(prop, v, colours)), nums(ns)) for v, ns in by_value)
        items.append("%s at %s: %s" % (esc(prop), "/".join("%dpx" % w for w in ws), vals))
    return '<ul class="parts-diff parts-small">%s</ul>' % "".join("<li>%s</li>" % i for i in items)


def _form_html(f: dict, n: int, w: int, colours: dict, fidelity: dict) -> str:
    esc = html.escape
    inst = f["sample"]
    places = list(f["where"])
    head = '<div class="parts-small"><span class="parts-label">Form %d</span> · %d× · <span title="%s">%s</span></div>' % (
        n, f["count"], esc("; ".join(places)), esc(_short_places(places)))
    cap = inst["captures"].get(w)
    if cap is None:
        return '<div class="parts-form">%s<div class="parts-muted parts-small">not shown at %dpx</div></div>' % (head, w)
    lines = [_text_line(cap["style"], colours), _box_line(cap["style"], colours)]
    notes = list(fidelity.get("%d-%d" % (f["no"], w), []))
    if cap.get("trimmed"):
        notes.append("long list cut to its first 6 items")
    doc, depth = frame_doc(cap)
    return ('<div class="parts-form">%s<div class="parts-muted parts-small">%s</div>%s'
            '<iframe class="parts-frame" loading="lazy" data-form="%d" data-w="%d" data-depth="%d" data-bundle="%d" '
            'width="%d" srcdoc="%s"></iframe></div>') % (
        head, esc(" · ".join(x for x in lines if x)),
        '<div class="parts-flag parts-small">Out of its page: %s</div>' % esc("; ".join(notes)) if notes else "",
        f["no"], w, depth, inst["bundle"], w, html.escape(doc, quote=True))


def render(data: dict, parts: list[dict], unplaced: list[str], forms_by_part: dict,
           fidelity: dict) -> tuple[str, dict]:
    names = {p["key"]: p["name"] for p in parts}
    colours = data["colours"]
    by_part = defaultdict(list)
    for i in data["instances"]:
        by_part[i["key"]].append(i)
    findings = same_text_findings(data["runs"])
    counts = {}
    for kind, members in KINDS:
        counts[kind] = {k: len(forms_by_part.get(k, [])) for k in members}
    esc = html.escape
    o = ['<!doctype html><html lang="en"><head><meta charset="utf-8">'
         '<meta name="viewport" content="width=device-width, initial-scale=1"><title>Parts page</title>'
         "<style>%s</style></head><body class=\"parts-page\">" % PAGE_CSS]
    for n, css in enumerate(data["sheets"]):
        if "</script" in css.lower():
            raise SystemExit("a stylesheet holds </script>; it cannot be carried in the page")
        o.append('<script type="text/plain" id="parts-css-%d">%s</script>' % (n, css))
    o.append('<script type="application/json" id="parts-bundles">%s</script>' % json.dumps(data["bundles"]))
    o.append('<div class="parts-report"><h1>Parts page</h1><p class="parts-muted">Every part in '
             "<code>docs/design/components.yml</code>, in every form it takes on main's pages today, "
             "read from the dev server at 375px and 1000px. Each form is drawn in a frame that carries "
             "the page's own CSS.</p>")
    diffs = {k: part_differences(by_part[k]) for _, members in KINDS for k in members if k in by_part}
    differing = [k for k, d in diffs.items() if d["children"] or d["look"]]
    o.append("<h2>Distinct forms per kind</h2><div class=\"parts-scroll\"><table class=\"parts-table\"><tr><th>Kind</th>"
             "<th>Forms</th><th>Differ by page</th><th>By part</th></tr>")
    for kind, per in counts.items():
        detail = ", ".join("%s %d" % (esc(names[k]), n) for k, n in per.items() if n)
        o.append('<tr><td><a href="#k-%s">%s</a></td><td>%d</td><td>%d</td><td class="parts-muted">%s</td></tr>'
                 % (re.sub(r"\W+", "-", kind.lower()), esc(kind), sum(per.values()),
                    sum(1 for k in per if k in differing), detail))
    o.append("</table></div>")
    o.append("<h2>The same text on one page in more than one style (%d)</h2>" % len(findings))
    o.append('<p class="parts-muted">Visible text of 3+ characters with a letter, compared within one page '
             "and one width; the site header, footer and breadcrumb are left out.</p><ul class=\"parts-list\">")
    for f in findings:
        vs = "; ".join("%s as %s" % (esc(_text_line(v["style"], colours)), esc(" / ".join(v["parts"])))
                       for v in f["variants"])
        o.append("<li><b>%s</b>: “%s” at %s — %s</li>" % (esc(f["page"]), esc(f["text"]),
                                                         ", ".join("%dpx" % w for w in f["widths"]), vs))
    o.append("</ul>")
    o.append("<h2>The same part, different from page to page (%d parts)</h2>" % len(differing))
    o.append('<p class="parts-muted">Child elements a part has on some pages and not on others, and style '
             "values that differ between pages. Each list is repeated under its part below.</p>"
             '<ul class="parts-list">')
    for k in differing:
        o.append('<li><a href="#p-%s">%s</a>%s</li>' % (k, esc(names[k]), _diff_html(diffs[k], colours)))
    o.append("</ul>")
    flagged = sum(1 for v in fidelity.values() if v)
    o.append("<h2>Drawing check</h2><p>%d of %d frames render a style other than the live page's; each is "
             "marked on its form.</p>" % (flagged, len(fidelity)))
    o.append("<h2>Pages read</h2><div class=\"parts-scroll\"><table class=\"parts-table\">")
    for p in data["pages"]:
        o.append("<tr><td>%s</td><td><code>%s</code></td><td class=\"parts-muted\">%s</td></tr>"
                 % (esc(p["label"]), esc(p["path"]), esc(" · ".join(p["states"]) or "")))
    o.append("</table></div>")
    unseen = [k for k in names if not any(i["captures"] for i in by_part.get(k, []))]
    o.append("<h2>Parts with no visible instance at 375px or 1000px (%d)</h2><p class=\"parts-muted\">%s</p>"
             % (len(unseen), esc(", ".join("%s (%s)" % (names[k], k) for k in unseen))))
    o.append("<h2>Not placed in a kind (%d)</h2><p class=\"parts-muted\">%s</p>"
             % (len(unplaced), esc(", ".join("%s: %d forms" % (k, len(forms_by_part.get(k, []))) for k in unplaced))))
    o.append("</div>")
    for kind, members in KINDS:
        o.append('<section class="parts-kind" id="k-%s"><h2>%s — %d forms</h2>'
                 % (re.sub(r"\W+", "-", kind.lower()), esc(kind), sum(counts[kind].values())))
        for k in members:
            forms = forms_by_part.get(k, [])
            if not forms:
                continue
            o.append('<h3 id="p-%s">%s <span class="parts-muted parts-small">%s · %d forms</span></h3>'
                     % (k, esc(names[k]), esc(k), len(forms)))
            if k in diffs and (diffs[k]["children"] or diffs[k]["look"]):
                o.append("<h4>From page to page</h4>" + _diff_html(diffs[k], colours))
            if len(forms) > 1:
                o.append("<h4>Between its forms</h4>" + _between_forms_html(form_differences(forms), colours))
            for w in WIDTHS:
                o.append("<h4>%dpx</h4><div class=\"%s\">" % (w, "parts-strip" if w == WIDTHS[0] else "parts-wide"))
                for n, f in enumerate(forms, 1):
                    o.append(_form_html(f, n, w, colours, fidelity))
                o.append("</div>")
        o.append("</section>")
    o.append("<script>%s</script></body></html>" % PAGE_JS)
    return "".join(o), counts


def check_fidelity(out: Path) -> dict:
    """Open the written page, draw every frame, and compare each target's style with its capture."""
    from playwright.sync_api import sync_playwright

    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        page = browser.new_page(viewport={"width": 1400, "height": 900}, color_scheme="light")
        page.goto(out.resolve().as_uri(), wait_until="load")
        page.evaluate("document.querySelectorAll('iframe.parts-frame').forEach(f => f.loading = 'eager')")
        page.wait_for_function("window.partsReady()", timeout=300000)
        page.evaluate("window.partsDressAll()")
        page.wait_for_timeout(1500)
        got = page.evaluate(FIDELITY_JS, list(STYLE_PROPS))
        browser.close()
    return {"%s-%s" % (g["form"], g["w"]): g["style"] for g in got}


def write_page(out: Path, data: dict, parts: list[dict], unplaced: list[str]) -> tuple[dict, dict]:
    """Render, draw every frame and compare it with its capture, then render again with the
    differences marked. The page reaches `out` only once checked. Returns (counts, drawing check)."""
    forms_by_part = forms_of(data["instances"])
    draft = out.with_name(out.stem + ".unchecked.html")
    page, _ = render(data, parts, unplaced, forms_by_part, {})
    draft.write_text(page, encoding="utf-8")
    rendered = check_fidelity(draft)
    captured = {"%d-%d" % (f["no"], w): f["sample"]["captures"][w]["style"]
                for forms in forms_by_part.values() for f in forms if "no" in f
                for w in WIDTHS if w in f["sample"]["captures"]}
    fidelity = {fid: fidelity_mismatches(captured[fid], rendered.get(fid)) for fid in captured}
    page, counts = render(data, parts, unplaced, forms_by_part, fidelity)
    draft.write_text(page, encoding="utf-8")
    draft.replace(out)
    return counts, fidelity


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--base", default="http://localhost:4321", help="the running dev server")
    ap.add_argument("--out", default=str(OUT))
    args = ap.parse_args(argv)
    base = args.base.rstrip("/")
    reg = ccr.load()
    parts = registry_parts(reg)
    _, unplaced = kind_of([p["key"] for p in parts])
    pages = pages_from_table(BLOCK_STANDARD.read_text(encoding="utf-8"))
    named = [str(c) for c in reg["sets"]["colours"] if not str(c).startswith("#")]
    tokens = [c for c in CORE_COLOURS if c in named] + [c for c in named if c not in CORE_COLOURS]
    data = crawl(base, pages, [{"key": p["key"], "selector": p["selector"]} for p in parts], tokens)
    out = Path(args.out)
    counts, fidelity = write_page(out, data, parts, unplaced)
    print("wrote %s (%d KB)" % (out, out.stat().st_size // 1024))
    for kind, per in counts.items():
        print("  %-18s %d" % (kind, sum(per.values())))
    print("  same text, more than one style: %d" % len(same_text_findings(data["runs"])))
    print("  frames drawn differently from the live page: %d of %d" % (sum(1 for v in fidelity.values() if v), len(fidelity)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
