"""The cross-page measured check: every built page and every mock, rendered and measured.

Runs every `design-mocks/gen_*.py` with `--out DIR`, serves those folders and the built site over
HTTP, opens every page in headless Chromium at every viewport and language, measures every element
of `docs/wireframes/block_standard.md` as its "Measured as" column says, and counts the gaps
`COUNT_JS` names. A Pages-table row owns every file its URL matches; a page no row owns is still
rendered, under its own path.

The counts are stored per page, summed over widths and languages, and compared with the baseline
(`design_inventory.BASELINE`) in both directions. `coverage`: a built page no row owns, a
generator that fails, a generator page no row names, and a language a mock lacks; compared on
every run over everything. `rendered`: the gap counts and the element misses, which depend on the
font, so compared only on the platform the baseline names; elsewhere an element miss fails as it
is and the gap counts are printed. `--artifacts` also receives `counts.json`, the measured counts
with examples. Exit 0 clean, 1 on any failure or count off its pin, 2 when the inventory does not
parse or the browser is missing.

    python scripts/check_design_inventory.py --dist site_v2/dist
    python scripts/check_design_inventory.py --no-built --pages competition-overview --viewports 375 --langs fi
    python scripts/check_design_inventory.py --page overview=design-mocks/renders/competition-overview_2026-09-16_01.html

Needs `pip install -r requirements-ui.txt` and, outside the Playwright image,
`python -m playwright install chromium`.
"""

from __future__ import annotations

import argparse
import functools
import json
import os
import subprocess
import sys
import tempfile
import threading
from concurrent.futures import ProcessPoolExecutor
from dataclasses import dataclass
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import design_inventory as di  # noqa: E402

REPO = di.REPO
MOCKS = REPO / "design-mocks"
# The narrowest phones, a phone, the width the menu goes inline, and the width the header's search
# field appears: the narrowest desktop layout. `tests/test_design_inventory.py` ties the last to
# `system.css`.
DEFAULT_VIEWPORTS = (280, 320, 360, 375, 700, 1010)
# Every locale the site publishes. A language the check does not render is a language whose layout
# can break green — the tab bar's rule names EN, DE and FI, so all three are measured.
# `tests/test_design_inventory.py` pins this against the site's own `LOCALES`.
DEFAULT_LANGS = ("en", "de", "fi")

# The design mocks carry English and a marked Finnish width probe in one file, toggled by CSS;
# a language a mock does not carry is counted as a coverage gap.
MOCK_LANGS = ("en", "fi")

COUNTS = ("scroll", "overflow", "split", "overlap", "classes")
MISS = "miss · "
COVERAGE = ("page with no row", "generator fails", "mock page with no row", "language missing")

# One evaluation per rendered page: the gaps the baseline pins. `scroll`: the page, or a box in it,
# scrolls sideways. `overflow`: a text node runs past the box it sits in sideways (an ellipsis cut
# included). `split`: a word, a run without spaces, lies on two lines. `overlap`: two text nodes'
# visible lines cross, SVG text included; each line is trimmed by a fifth top and bottom so two
# tight lines that only touch are not counted. `classes`: the class names no inventory selector
# uses. Text that is not displayed, fully transparent or clipped away is not read.
COUNT_JS = r"""
(registered) => {
  const reg = new Set(registered);
  const shownMemo = new Map();
  const shown = (el) => {
    if (!el) return true;
    if (shownMemo.has(el)) return shownMemo.get(el);
    const s = getComputedStyle(el);
    const v = s.display !== 'none' && s.visibility !== 'hidden' && s.visibility !== 'collapse'
      && parseFloat(s.opacity) !== 0 && shown(el.parentElement);
    shownMemo.set(el, v);
    return v;
  };
  const clipMemo = new Map();
  const clipOf = (el) => {
    if (!el || el === document.documentElement) return [-Infinity, -Infinity, Infinity, Infinity];
    if (clipMemo.has(el)) return clipMemo.get(el);
    let c = clipOf(el.parentElement);
    const s = getComputedStyle(el);
    if (s.overflowX !== 'visible' || s.overflowY !== 'visible' || s.clipPath !== 'none') {
      const r = el.getBoundingClientRect();
      c = [Math.max(c[0], r.left), Math.max(c[1], r.top), Math.min(c[2], r.right), Math.min(c[3], r.bottom)];
    }
    clipMemo.set(el, c);
    return c;
  };
  const boxOf = (el) => {
    for (let a = el; a && a !== document.body; a = a.parentElement) {
      const d = getComputedStyle(a).display;
      if (d !== 'contents' && d !== 'inline') return a;
    }
    return document.body;
  };
  const label = (el, txt) => {
    const cls = typeof el.className === 'string' && el.className.trim() ? '.' + el.className.trim().split(/\s+/).join('.') : '';
    return el.tagName.toLowerCase() + cls + (txt ? ' "' + txt.trim().slice(0, 40) + '"' : '');
  };
  const ex = { scroll: [], overflow: [], split: [], overlap: [] };
  let scroll = 0, overflow = 0, split = 0;
  const root = document.documentElement;
  if (root.scrollWidth > root.clientWidth + 1) { scroll++; ex.scroll.push('page ' + root.scrollWidth + '>' + root.clientWidth); }
  for (const el of document.body.querySelectorAll('*')) {
    const s = getComputedStyle(el);
    if ((s.overflowX === 'auto' || s.overflowX === 'scroll') && el.scrollWidth > el.clientWidth + 1 && shown(el)) {
      scroll++; ex.scroll.push(label(el, '') + ' ' + el.scrollWidth + '>' + el.clientWidth);
    }
  }
  const lines = [];
  const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
  let id = 0;
  for (let n = walker.nextNode(); n; n = walker.nextNode()) {
    const txt = n.textContent;
    const p = n.parentElement;
    if (!txt.trim() || !p || p.closest('script,style,noscript,template') || !shown(p)) continue;
    id++;
    const inSvg = !!p.closest('svg');
    let rects;
    if (inSvg) {
      const r = p.getBoundingClientRect();
      rects = r.width > 0 && r.height > 0 ? [r] : [];
    } else {
      const range = document.createRange();
      range.selectNodeContents(n);
      rects = [...range.getClientRects()].filter((r) => r.width > 0.5 && r.height > 0.5);
    }
    const clip = clipOf(p);
    const seen = rects.map((r) => [Math.max(r.left, clip[0]), Math.max(r.top, clip[1]), Math.min(r.right, clip[2]), Math.min(r.bottom, clip[3])])
      .filter((r) => r[2] - r[0] > 1 && r[3] - r[1] > 1);
    if (!seen.length) continue;
    if (!inSvg) {
      const box = boxOf(p).getBoundingClientRect();
      if (rects.some((r) => r.left < box.left - 1 || r.right > box.right + 1)) { overflow++; ex.overflow.push(label(p, txt)); }
      const tops = [];
      for (const r of rects) if (!tops.some((t) => Math.abs(t - r.top) < 2)) tops.push(r.top);
      if (tops.length > 1) {
        const word = /\S+/g;
        for (let m = word.exec(txt); m; m = word.exec(txt)) {
          const wr = document.createRange();
          wr.setStart(n, m.index);
          wr.setEnd(n, m.index + m[0].length);
          const wt = [];
          for (const r of wr.getClientRects()) if (r.width > 0.5 && !wt.some((t) => Math.abs(t - r.top) < 2)) wt.push(r.top);
          if (wt.length > 1) { split++; ex.split.push(label(p, m[0])); }
        }
      }
    }
    for (const r of seen) {
      const h = r[3] - r[1];
      lines.push({ id, l: r[0], r: r[2], t: r[1] + h * 0.2, b: r[3] - h * 0.2, el: p, txt });
    }
  }
  lines.sort((a, b) => a.t - b.t);
  const pairs = new Set();
  for (let i = 0; i < lines.length; i++) {
    const a = lines[i];
    for (let j = i + 1; j < lines.length && lines[j].t < a.b; j++) {
      const b = lines[j];
      if (a.id === b.id || Math.min(a.r, b.r) - Math.max(a.l, b.l) <= 1) continue;
      const key = Math.min(a.id, b.id) + ':' + Math.max(a.id, b.id);
      if (!pairs.has(key)) { pairs.add(key); ex.overlap.push(label(a.el, a.txt) + ' x ' + label(b.el, b.txt)); }
    }
  }
  const classes = new Set();
  for (const el of document.querySelectorAll('[class]')) for (const c of el.classList) if (!reg.has(c)) classes.add(c);
  return { scroll, overflow, split, overlap: pairs.size, classes: [...classes].sort(), ex };
}
"""

# One evaluation per rendered page: every element's visible matches, with the measurements its
# assertions need. Runs inside the page; returns plain JSON.
MEASURE_JS = r"""
(spec) => {
  const props = spec.props;
  const fx = document.querySelector('.fx') || document.body;
  const fxs = getComputedStyle(fx);
  const tokens = {};
  for (const t of spec.tokens) tokens[t] = fxs.getPropertyValue('--' + t).trim();
  const visible = (el) => {
    const r = el.getBoundingClientRect();
    return r.width > 1 && r.height > 1;
  };
  const hasText = (el) => {
    for (const n of el.childNodes) if (n.nodeType === 3 && n.textContent.trim()) return true;
    return false;
  };
  const isContent = (el) => visible(el) && (el.tagName === 'svg' || el.tagName === 'IMG' || hasText(el));
  // A box the reader sees as a line of its own: a top border or a background.
  const isBox = (el) => {
    if (!visible(el)) return false;
    const s = getComputedStyle(el);
    if (parseFloat(s.borderTopWidth) > 0 && s.borderTopStyle !== 'none') return true;
    const bg = s.backgroundColor;
    const m = bg.match(/\/\s*([\d.]+)\s*\)$/) || bg.match(/^rgba\([^)]*,\s*([\d.]+)\)$/);
    if (bg !== 'rgba(0, 0, 0, 0)' && bg !== 'transparent' && !(m && parseFloat(m[1]) === 0)) return true;
    return s.backgroundImage !== 'none';
  };
  // Where a sibling's first line starts: the topmost edge a reader sees inside it — a bordered or
  // filled box at its border, or the content box of the nearest block-level box holding a text or
  // an image. A block box's top is exact; an inline text box floats with the line height, so it is
  // not read. A padding on a date heading or a fact row is counted; a label baseline-aligned
  // below its number is not the first line, the number is.
  const blockLevel = (e) => { const d = getComputedStyle(e).display; return d !== 'contents' && !d.startsWith('inline'); };
  const firstLineTop = (el) => {
    const all = [el, ...el.querySelectorAll('*')];
    let top = null;
    for (const e of all) {
      if (e.tagName === 'INPUT' || e.tagName === 'STYLE' || e.tagName === 'SCRIPT') continue;
      let t = null;
      if (isBox(e)) t = e.getBoundingClientRect().top;
      else if (isContent(e)) {
        let a = e;
        while (a !== el && !blockLevel(a)) a = a.parentElement;
        const s = getComputedStyle(a);
        t = a.getBoundingClientRect().top + parseFloat(s.paddingTop) + parseFloat(s.borderTopWidth);
      }
      if (t !== null && (top === null || t < top)) top = t;
    }
    return top;
  };
  const nextEl = (el) => { let s = el.nextElementSibling; while (s && !visible(s)) s = s.nextElementSibling; return s; };
  const prevEl = (el) => { let s = el.previousElementSibling; while (s && !visible(s)) s = s.previousElementSibling; return s; };
  const container = (el) => el.closest('section') || el.closest('.inner') || document.body;
  // Lines of TEXT: an icon beside the text sits at its own top and is not a second line.
  const lines = (el) => {
    const tops = [];
    const walker = document.createTreeWalker(el, NodeFilter.SHOW_TEXT);
    for (let n = walker.nextNode(); n; n = walker.nextNode()) {
      if (!n.textContent.trim()) continue;
      const range = document.createRange();
      range.selectNodeContents(n);
      for (const r of range.getClientRects()) {
        if (r.height <= 0 || r.width <= 0) continue;
        if (!tops.some((t) => Math.abs(t - r.top) < 1)) tops.push(r.top);
      }
    }
    return tops.length;
  };
  // The widest word of the element's text, in its own font.
  const ctx = document.createElement('canvas').getContext('2d');
  const longestWord = (el) => {
    const s = getComputedStyle(el);
    ctx.font = `${s.fontStyle} ${s.fontWeight} ${s.fontSize} ${s.fontFamily}`;
    const words = el.textContent.trim().split(/\s+/).filter(Boolean);
    return words.length ? Math.max(...words.map((w) => ctx.measureText(w).width)) : 0;
  };
  const out = {};
  for (const el of spec.elements) {
    let nodes;
    try { nodes = [...document.querySelectorAll(el.selector)]; } catch (e) { out[el.name] = { error: String(e) }; continue; }
    const inDom = nodes.length;
    nodes = nodes.filter(visible);
    const matches = [];
    for (const n of nodes) {
      const s = getComputedStyle(n);
      const r = n.getBoundingClientRect();
      const m = { style: {}, rect: [r.left, r.top, r.width, r.height] };
      for (const p of props) m.style[p] = s.getPropertyValue(p);
      if (el.kinds.includes('gap(next)')) { const nx = nextEl(n); const t = nx ? firstLineTop(nx) : null; m.gapNext = t === null ? null : t - r.bottom; }
      if (el.kinds.includes('gap(prev)')) { const pv = prevEl(n); m.gapPrev = pv ? r.top - pv.getBoundingClientRect().bottom : null; }
      if (el.kinds.includes('left-edge')) { m.leftEdge = r.left - container(n).getBoundingClientRect().left; }
      if (el.kinds.includes('fits')) { m.fits = [n.scrollWidth, n.clientWidth]; }
      if (el.kinds.includes('one-line')) { m.lines = lines(n); }
      if (el.kinds.includes('whole-words')) { m.words = [longestWord(n), n.clientWidth]; }
      if (el.kinds.includes('fit-marked')) { m.marked = n.classList.contains('fit-one') || n.classList.contains('fit-two'); }
      if (el.kinds.includes('tracks')) {
        const head = n.parentElement ? n.parentElement.querySelector(':scope > .ctab-head') : null;
        m.tracks = [head ? getComputedStyle(head).gridTemplateColumns : null, s.gridTemplateColumns];
      }
      matches.push(m);
    }
    const res = { matches, inDom };
    if (el.kinds.includes('stripe')) {
      const tables = [];
      const seen = new Set();
      for (const n of nodes) {
        const p = n.parentElement;
        if (!p || seen.has(p)) continue;
        seen.add(p);
        const rows = [...p.children].filter((c) => c.matches(el.selector) && visible(c));
        tables.push(rows.map((c) => getComputedStyle(c).backgroundColor));
      }
      res.stripes = tables;
    }
    out[el.name] = res;
  }
  return { tokens, elements: out };
}
"""


@dataclass
class Failure:
    page: str
    viewport: int
    lang: str
    element: str
    detail: str
    level: str = "FAIL"
    measured: bool = False   # an element miss: counted against the baseline where it is compared

    def line(self) -> str:
        return "%-5s %s · %d · %s · %s · %s" % (self.level, self.page, self.viewport, self.lang, self.element, self.detail)


class _Quiet(SimpleHTTPRequestHandler):
    def log_message(self, *_args):
        pass


def serve(root: Path) -> tuple[ThreadingHTTPServer, str]:
    handler = functools.partial(_Quiet, directory=str(root))
    srv = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv, "http://127.0.0.1:%d/" % srv.server_address[1]


def generators(mocks: Path = MOCKS) -> list[str]:
    """Every mock generator on disk: the check finds them, no list names them."""
    return sorted(p.name for p in mocks.glob("gen_*.py"))


def run_generators(gens: list[str], tmp: Path, mocks: Path = MOCKS) -> tuple[dict[str, Path], dict[str, str]]:
    """Run each generator as `gen.py --out DIR`, DIR its own folder under `tmp`. Returns the folders
    of the ones that ran and {generator: why} for the ones that failed."""
    out: dict[str, Path] = {}
    failed: dict[str, str] = {}
    for gen in gens:
        folder = tmp / Path(gen).stem
        folder.mkdir(parents=True)
        try:
            proc = subprocess.run([sys.executable, gen, "--out", str(folder)], cwd=str(mocks), capture_output=True,
                                  timeout=300)
        except subprocess.TimeoutExpired:
            failed[gen] = "timed out"
            continue
        if proc.returncode != 0:
            tail = proc.stderr.decode("utf-8", "replace").strip().splitlines()[-1:] or ["?"]
            failed[gen] = "exit %d: %s" % (proc.returncode, tail[-1])
            continue
        if not any(folder.glob("*.html")):
            failed[gen] = "wrote no page into --out DIR"
            continue
        out[gen] = folder
    return out, failed


@dataclass
class Plan:
    """What one run renders: (page, language, server root, path under it), the coverage gaps, and
    the failures of the inventory itself (a row that matches nothing)."""
    targets: list[tuple[di.Page, str, str, str]]
    coverage: dict[str, dict[str, int]]
    failures: list[Failure]


def plan(pages: list[di.Page], langs: list[str], dist: Path | None, mock_out: dict[str, Path],
         mock_failed: dict[str, str], every_file: bool) -> Plan:
    """Every built file and every generator page, each owned by the row that names it. A file two
    rows match belongs to the row with the literal URL; two patterns matching one file is an
    inventory failure. With `every_file`, the files no row owns are rendered too, each under its own
    path, and counted as a gap."""
    targets: list[tuple[di.Page, str, str, str]] = []
    coverage: dict[str, dict[str, int]] = {k: {} for k in COVERAGE}
    failures: list[Failure] = []
    if dist is not None:
        owner: dict[Path, tuple[di.Page, str]] = {}
        for p in (p for p in pages if p.kind == "built"):
            for lang in langs:
                hits = resolve_all(p, dist, lang)
                if not hits:
                    failures.append(Failure(p.name, 0, lang, "(page)", "no file matches %s under %s" % (p.url, dist)))
                for f in hits:
                    was = owner.get(f)
                    if was is None or ("*" in was[0].url and "*" not in p.url):
                        owner[f] = (p, lang)
                    elif was[0] is not p and ("*" in p.url) == ("*" in was[0].url):
                        failures.append(Failure(p.name, 0, lang, "(page)", "%s is also matched by %s"
                                                % (f.relative_to(dist).as_posix(), was[0].name)))
        files = sorted(dist.rglob("*.html")) if every_file else sorted(owner)
        for f in files:
            rel = f.relative_to(dist).as_posix()
            if f in owner:
                p, lang = owner[f]
            else:
                lang = rel.split("/")[0] if rel.split("/")[0] in DEFAULT_LANGS else "en"
                if lang not in langs:
                    continue
                coverage["page with no row"][rel] = 1
                p = di.Page(rel, "built", "", rel, "path", ())
            targets.append((p, lang, "dist", rel))
    named = {(p.source, p.url): p for p in pages if p.kind == "mock"}
    for gen in sorted(set(mock_out) | set(mock_failed)):
        if gen in mock_failed:
            coverage["generator fails"][gen] = 1
            continue
        folder = mock_out[gen]
        written = {f.name for f in folder.glob("*.html")}
        for p in (p for p in pages if p.kind == "mock" and p.source == gen and p.url not in written):
            failures.append(Failure(p.name, 0, "-", "(generator)", "%s wrote no %s" % (gen, p.url)))
        for name in sorted(written):
            p = named.get((gen, name))
            if p is None:
                if not every_file:
                    continue
                key = "%s/%s" % (gen, name)
                coverage["mock page with no row"][key] = 1
                toggle = 'for="t-fi"' in (folder / name).read_text(encoding="utf-8", errors="replace")
                p = di.Page(key, "mock", gen, name, "toggle" if toggle else "none", ())
            carried = [lang for lang in MOCK_LANGS if lang == "en" or p.fi == "toggle"]
            missing = len([lang for lang in DEFAULT_LANGS if lang not in carried])
            if missing:
                coverage["language missing"][p.name] = missing
            for lang in langs:
                if lang in carried:
                    targets.append((p, lang, gen, name))
    return Plan(targets, {k: v for k, v in coverage.items() if v}, failures)


ADDRESS_WORDS = REPO / "site_v2" / "src" / "i18n" / "address_words.json"
_TOP_WORDS = ("competitions", "matches", "teams", "players")
_TAB_WORDS = ("matches", "stats")


@functools.lru_cache(maxsize=1)
def address_words() -> dict[str, dict[str, str]]:
    return json.loads(ADDRESS_WORDS.read_text(encoding="utf-8"))


def translate_path(rest: str, from_lang: str, to_lang: str) -> str:
    """The path after the locale in another language, by position, as `translatePath` in
    `site_v2/src/lib/addressWords.mjs` does it: the first segment is a top word or a competition
    slug, the second a tab word only after a slug, every other segment a name (`*` included)."""
    words = address_words()
    segs = rest.split("/")

    def swap(i: int, keys: tuple[str, ...]) -> bool:
        for key in keys:
            if words[key][from_lang] == segs[i]:
                segs[i] = words[key][to_lang]
                return True
        return False

    if segs and segs[0] and not swap(0, _TOP_WORDS) and len(segs) > 1 and segs[1]:
        swap(1, _TAB_WORDS)
    return "/".join(segs)


def resolve_all(page: di.Page, dist: Path, lang: str) -> list[Path]:
    url = page.url
    if lang != "en" and url.startswith("en/"):
        url = "%s/%s" % (lang, translate_path(url[len("en/"):], "en", lang))
    return sorted(dist.glob(url))


def resolve_built(page: di.Page, dist: Path, lang: str) -> Path | None:
    hits = resolve_all(page, dist, lang)
    return hits[0] if hits else None


def measure_page(pw_page, inv: di.Inventory, spec: dict, page: di.Page, viewport: int, lang: str,
                 failures: list[Failure]) -> int:
    """Measure one rendered page; append failures; return the number of visible inventory matches."""
    data = pw_page.evaluate(MEASURE_JS, spec)
    tokens = data["tokens"]
    total = 0
    seen: set[str] = set()
    for el in inv.elements:
        res = data["elements"].get(el.name, {})
        level = "FAIL" if el.status == "ruled" else "WARN"
        if "error" in res:
            failures.append(Failure(page.name, viewport, lang, el.name, "selector error: %s" % res["error"], level))
            continue
        matches = res.get("matches", [])
        if matches:
            seen.add(el.name)
            total += len(matches)
        for a in el.assertions:
            if a.kind in ("hover", "press") or not di.applies(a, viewport):
                continue
            # The mark is set by the site's script, which only a built page loads.
            if a.kind == "fit-marked" and page.kind != "built":
                continue
            if a.kind == "visible":
                if res.get("inDom", 0):
                    msg = di.compare(a, len(matches), tokens)
                    if msg:
                        failures.append(Failure(page.name, viewport, lang, el.name, msg, level))
                continue
            if a.kind == "stripe":
                for t_i, rows in enumerate(res.get("stripes", []), start=1):
                    msg = di.compare(a, rows, tokens)
                    if msg:
                        failures.append(Failure(page.name, viewport, lang, "%s [table %d]" % (el.name, t_i), msg, level))
                continue
            for m_i, m in enumerate(matches, start=1):
                if a.kind in di.PROPS:
                    measured = m["style"].get(a.kind)
                elif a.kind == "gap(next)":
                    measured = m.get("gapNext")
                elif a.kind == "gap(prev)":
                    measured = m.get("gapPrev")
                elif a.kind == "left-edge":
                    measured = m.get("leftEdge")
                elif a.kind == "fits":
                    measured = m.get("fits")
                elif a.kind == "one-line":
                    measured = m.get("lines")
                elif a.kind == "whole-words":
                    measured = m.get("words")
                elif a.kind == "fit-marked":
                    measured = m.get("marked")
                elif a.kind == "tracks":
                    measured = m.get("tracks")
                elif a.kind == "min-box":
                    measured = (m["rect"][2], m["rect"][3])
                else:
                    measured = None
                msg = di.compare(a, measured, tokens)
                if msg:
                    failures.append(Failure(page.name, viewport, lang, "%s [%s #%d]" % (el.name, el.selector, m_i), msg, level))
                    break
        pointer = [a for a in el.assertions if a.kind in ("hover", "press") and di.applies(a, viewport)]
        if pointer and matches:
            handle = None
            for h in pw_page.query_selector_all(el.selector):
                if h.bounding_box():
                    handle = h
                    break
            if handle is None:
                continue
            handle.evaluate("e => e.scrollIntoView({block: 'center'})")
            for a in pointer:
                if a.kind == "hover":
                    handle.hover()
                    measured = handle.evaluate("(e, p) => getComputedStyle(e).getPropertyValue(p)", a.prop)
                else:
                    handle.hover()
                    pw_page.mouse.down()
                    measured = handle.evaluate("(e, p) => getComputedStyle(e).getPropertyValue(p)", a.prop)
                    pw_page.mouse.move(0, 0)
                    pw_page.mouse.up()
                msg = di.compare(a, measured, tokens)
                if msg:
                    failures.append(Failure(page.name, viewport, lang, "%s [%s #1]" % (el.name, el.selector), msg, level))
            pw_page.mouse.move(0, 0)
    for name in page.expected_at(viewport):
        if name not in seen:
            failures.append(Failure(page.name, viewport, lang, name, "expected on this page · measured 0 matches"))
    if total == 0:
        failures.append(Failure(page.name, viewport, lang, "(page)", "expected inventory elements · measured 0 — is the URL right?"))
    return total


def compare_rendered(rendered: dict[str, dict[str, int]], pinned: dict, full_run: bool,
                     platform: str) -> tuple[str, list[str]]:
    """(why the counts are not compared, or "") and the counts off their pins. Only a run over
    everything the inventory lists, on the platform the baseline names, is compared."""
    if not full_run:
        return "a narrower run than the baseline's", []
    if platform != pinned["platform"]:
        return "the baseline is measured on %s, this run on %s" % (pinned["platform"], platform), []
    nonzero = {name: {k: n for k, n in c.items() if n} for name, c in rendered.items()}
    return "", di.compare_counts(nonzero, pinned["pages"])


def compare_coverage(coverage: dict[str, dict[str, int]], pinned: dict[str, dict[str, int]],
                     full_run: bool) -> list[str]:
    """The coverage gaps off their pins. They do not depend on the font, so every run over
    everything compares them, on any platform."""
    return di.compare_counts(coverage, pinned) if full_run else []


def render_width(job: dict) -> dict:
    """One viewport, in its own process: open every target, measure its elements, count its gaps."""
    from playwright.sync_api import sync_playwright  # noqa: PLC0415

    viewport, inv, spec, artifacts = job["viewport"], job["inv"], job["spec"], job["artifacts"]
    failures: list[Failure] = []
    counted: dict[str, dict] = {}
    covered: dict[str, set[str]] = {}
    renders = shots = 0
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        ctx = browser.new_context(viewport={"width": viewport, "height": 900}, device_scale_factor=1,
                                  reduced_motion="reduce")
        pw_page = ctx.new_page()
        for p, lang, root, path in job["targets"]:
            pw_page.goto(job["bases"][root] + path, wait_until="load")
            if p.kind == "mock" and lang == "fi":
                label = pw_page.query_selector('label[for="t-fi"]')
                if label is None:
                    failures.append(Failure(p.name, viewport, lang, "(page)", "no FI toggle on the page"))
                    continue
                label.click()
                if not pw_page.is_checked("#t-fi"):
                    failures.append(Failure(p.name, viewport, lang, "(page)", "the FI toggle did not switch"))
                    continue
            before = len(failures)
            measure_page(pw_page, inv, spec, p, viewport, lang, failures)
            renders += 1
            covered.setdefault(lang, set()).add(p.name)
            missed = [f for f in failures[before:] if f.level == "FAIL"]
            for f in missed:
                f.measured = True
            if artifacts and missed and shots < 20:
                pw_page.screenshot(path=str(Path(artifacts) / ("%s_%d_%s.png" % (p.name.replace("/", "_"), viewport, lang))),
                                   full_page=True)
                shots += 1
            # The pointer checks scroll the page, and a sticky header then lies over the content.
            pw_page.evaluate("window.scrollTo(0, 0); document.fonts.ready.then(() => new Promise((r) => requestAnimationFrame(() => r())))")
            found = pw_page.evaluate(COUNT_JS, job["registered"])
            page_counts = counted.setdefault(p.name, {"classes": set(), "examples": {}})
            page_counts["classes"].update(found["classes"])
            for k in COUNTS[:-1]:
                page_counts[k] = page_counts.get(k, 0) + found[k]
                shown = page_counts["examples"].setdefault(k, [])
                shown += ["%d %s %s" % (viewport, lang, e) for e in found["ex"][k][:20 - len(shown)]]
        ctx.close()
        browser.close()
    return {"failures": failures, "counted": counted, "covered": covered, "renders": renders}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--inventory", default=str(di.DOC))
    ap.add_argument("--dist", default=str(REPO / "site_v2" / "dist"))
    ap.add_argument("--mocks", default=str(MOCKS))
    ap.add_argument("--pages", help="comma-separated page names to run (default: all)")
    ap.add_argument("--viewports", help="widths (default: %s)" % ",".join(str(v) for v in DEFAULT_VIEWPORTS))
    ap.add_argument("--baseline", default=str(di.BASELINE))
    ap.add_argument("--langs", default=",".join(DEFAULT_LANGS))
    ap.add_argument("--no-built", action="store_true")
    ap.add_argument("--no-mocks", action="store_true")
    ap.add_argument("--page", action="append", default=[], metavar="NAME=FILE.html",
                    help="an ad-hoc page to measure (EN only), e.g. a render of record")
    ap.add_argument("--artifacts", help="folder for full-page screenshots of failing pages")
    args = ap.parse_args(argv)

    try:
        inv = di.load(Path(args.inventory))
    except di.InventoryError as exc:
        print("INVENTORY ERROR: %s" % exc, file=sys.stderr)
        return 2
    try:
        from playwright.sync_api import Error as PlaywrightError, sync_playwright
    except ImportError:
        print("playwright is not installed: pip install -r requirements-ui.txt", file=sys.stderr)
        return 2

    wanted = set(args.pages.split(",")) if args.pages else None
    pages = [p for p in inv.pages if (wanted is None or p.name in wanted)
             and not (args.no_built and p.kind == "built") and not (args.no_mocks and p.kind == "mock")]
    adhoc = []
    for spec in args.page:
        name, _, file = spec.partition("=")
        if not name or not file:
            ap.error("--page needs NAME=FILE.html")
        adhoc.append((name, Path(file).resolve()))
    if wanted:
        missing = wanted - {p.name for p in inv.pages}
        if missing:
            ap.error("unknown page(s): %s" % ", ".join(sorted(missing)))
    viewports = [int(v) for v in args.viewports.split(",")] if args.viewports else list(DEFAULT_VIEWPORTS)
    langs = args.langs.split(",")
    # The baseline pins a run over every page, width and language; a narrower run prints its counts
    # and compares none.
    full_run = not (wanted or adhoc or args.no_built or args.no_mocks or args.viewports
                    or args.langs != ",".join(DEFAULT_LANGS))
    registered = sorted(di.class_tokens(inv.elements))
    spec = {
        "props": list(di.PROPS),
        "tokens": list(di.TOKENS),
        "elements": [{"name": e.name, "selector": e.selector, "kinds": [a.kind for a in e.assertions]} for e in inv.elements],
    }
    artifacts = Path(args.artifacts) if args.artifacts else None
    if artifacts:
        artifacts.mkdir(parents=True, exist_ok=True)
    try:
        with sync_playwright() as pw:
            pw.chromium.launch().close()
    except PlaywrightError as exc:
        print("cannot launch Chromium: %s" % str(exc).splitlines()[0], file=sys.stderr)
        return 2

    mocks = Path(args.mocks)
    counted: dict[str, dict] = {}
    covered: dict[str, set[str]] = {}   # language -> the pages actually rendered in it
    renders = 0
    servers: list[ThreadingHTTPServer] = []
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        gens = [] if args.no_mocks else generators(mocks)
        if wanted:
            gens = [g for g in gens if any(p.kind == "mock" and p.source == g for p in pages)]
        mock_out, mock_failed = run_generators(gens, tmp, mocks)
        dist = None if args.no_built else Path(args.dist)
        failures: list[Failure] = []
        if dist is not None and not dist.is_dir():
            failures.append(Failure("(site)", 0, "-", "(page)", "no built site at %s (astro build first, or --no-built)" % dist))
            dist = None
        run = plan(pages, langs, dist, mock_out, mock_failed, every_file=not wanted)
        failures += run.failures
        targets = list(run.targets)
        bases: dict[str, str] = {}
        try:
            for root, folder in [("dist", dist)] + sorted(mock_out.items()):
                if folder is not None:
                    srv, bases[root] = serve(folder)
                    servers.append(srv)
            # an ad-hoc page is served from its own folder, so a stylesheet beside it resolves
            for name, file in adhoc:
                root = "page:%s" % file.parent
                if root not in bases:
                    srv, bases[root] = serve(file.parent)
                    servers.append(srv)
                targets.append((di.Page(name, "mock", "", file.name, "none", ()), "en", root, file.name))
            jobs = [{"viewport": v, "targets": targets, "bases": bases, "inv": inv, "spec": spec,
                     "registered": registered, "artifacts": str(artifacts) if artifacts else None} for v in viewports]
            if len(jobs) == 1:
                results = [render_width(jobs[0])]
            else:
                with ProcessPoolExecutor(max_workers=min(len(jobs), os.cpu_count() or 1)) as pool:
                    results = list(pool.map(render_width, jobs))
        finally:
            for srv in servers:
                srv.shutdown()

    for res in results:
        failures += res["failures"]
        renders += res["renders"]
        for lang, names in res["covered"].items():
            covered.setdefault(lang, set()).update(names)
        for name, c in res["counted"].items():
            into = counted.setdefault(name, {"classes": set(), "examples": {}})
            into["classes"].update(c["classes"])
            for k in COUNTS[:-1]:
                into[k] = into.get(k, 0) + c.get(k, 0)
                shown = into["examples"].setdefault(k, [])
                shown += c["examples"].get(k, [])[:20 - len(shown)]
    rendered = {name: {k: (len(c["classes"]) if k == "classes" else c.get(k, 0)) for k in COUNTS}
                for name, c in counted.items()}
    for f in failures:
        if f.measured:
            key = MISS + f.element.split(" [")[0]
            rendered.setdefault(f.page, {})[key] = rendered.get(f.page, {}).get(key, 0) + 1
            shown = counted.setdefault(f.page, {"classes": set(), "examples": {}})["examples"].setdefault(key, [])
            if len(shown) < 20:
                shown.append("%d %s %s" % (f.viewport, f.lang, f.detail))
    for name in sorted(rendered):
        print("COUNT %s · %s" % (name, " · ".join("%s %d" % (k, n) for k, n in rendered[name].items())))
    for group in sorted(run.coverage):
        print("COVERAGE %s: %d (%s)" % (group, sum(run.coverage[group].values()),
                                         ", ".join(sorted(run.coverage[group]))[:300]))
    baseline = di.load_baseline(Path(args.baseline))
    note, off = compare_rendered(rendered, baseline["rendered"], full_run, sys.platform)
    if not note:
        # The pins decide: a miss the baseline holds is a known gap, not a failure.
        failures = [f for f in failures if not f.measured]
    off += compare_coverage(run.coverage, baseline["coverage"], full_run)
    for gen, why in sorted(mock_failed.items()):
        failures.append(Failure(gen, 0, "-", "(generator)", why, "INFO"))
    for line in off:
        failures.append(Failure("(counts)", 0, "-", "(baseline)", line))
        for page, c in counted.items():
            for metric, examples in c["examples"].items():
                if line.split(" · ", 1)[1].startswith("%s · %s · " % (page, metric)):
                    failures += [Failure(page, 0, "-", metric, "e.g. " + e, "INFO") for e in examples[:5]]
    if artifacts is not None:
        (artifacts / "counts.json").write_text(json.dumps(
            {"platform": sys.platform, "pages": {name: {k: n for k, n in c.items() if n} for name, c in rendered.items()},
             "coverage": run.coverage,
             "classes": {name: sorted(c["classes"]) for name, c in counted.items()},
             "examples": {name: c["examples"] for name, c in counted.items()}}, indent=1, ensure_ascii=False), encoding="utf-8")
    for f in failures:
        print(f.line())
    hard = [f for f in failures if f.level == "FAIL"]
    # A gate that overstates its own coverage is the defect this check exists to catch, so the
    # language count never stands for pages it did not reach. Read from the renders that actually
    # happened, not from what was asked for: the mocks carry no German, and an ad-hoc page is
    # English only, and both would otherwise hide inside "N languages".
    # Count every language ASKED FOR, not only those that rendered something: a language that
    # reached no page at all is the loudest version of this problem and would otherwise vanish
    # from the tally instead of showing as 0.
    per_lang = [(lang, len(covered.get(lang, ()))) for lang in langs]
    reached = max((n for _lang, n in per_lang), default=0)
    caveat = ""
    if any(n < reached for _lang, n in per_lang):
        caveat = " (pages per language: %s)" % ", ".join("%s %d" % (lang, n) for lang, n in per_lang)
    print("%d pages · %d viewports · %d languages%s · %d renders · %d failures · %d warnings"
          % (len(rendered), len(viewports), len(langs), caveat, renders, len(hard),
             sum(1 for f in failures if f.level == "WARN")))
    print("gap counts: %d pages counted at %s px · %s" % (
        renders, ",".join(str(v) for v in viewports),
        ("rendered counts not compared: %s · " % note if note else "") + "%d off the baseline" % len(off)))
    if artifacts and hard:
        (artifacts / "failures.json").write_text(json.dumps([f.__dict__ for f in failures], indent=1), encoding="utf-8")
    return 1 if hard else 0


if __name__ == "__main__":
    sys.exit(main())
