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

A baseline file may name the `viewports` and `langs` it was measured over (every one when it names
none); a run over exactly those is compared with it, any other narrower run is not.
`baseline_quick.json` is the pin set of the merge request run.

    python scripts/check_design_inventory.py --dist site_v2/dist
    python scripts/check_design_inventory.py --dist site_v2/dist --viewports 280,1010 --langs en,de --baseline tests/fixtures/design_inventory/baseline_quick.json
    python scripts/check_design_inventory.py --no-built --pages competition-overview --viewports 375 --langs fi
    python scripts/check_design_inventory.py --page overview=design-mocks/renders/competition-overview_2026-09-16_01.html

Needs `pip install -r requirements-ui.txt` and, outside the Playwright image,
`python -m playwright install chromium`.
"""

from __future__ import annotations

import argparse
import dataclasses
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

import yaml

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import design_inventory as di  # noqa: E402

REPO = di.REPO
MOCKS = REPO / "design-mocks"
REGISTRY = REPO / "docs" / "design" / "components.yml"
# The narrowest phones, a phone, a small tablet, a tablet and the narrowest desktop layout.
# `tests/test_design_inventory.py` ties the width the header's search field appears at, read from
# `system.css`, to this list.
DEFAULT_VIEWPORTS = (280, 320, 360, 375, 520, 700, 1010)
# Widths of `DEFAULT_VIEWPORTS` a full run measures on the built site only: no mock draws a
# breakpoint there, and a mock's gap counts are pinned over the other widths.
BUILT_ONLY_VIEWPORTS = (520,)
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

# One evaluation per rendered page and tab: the gaps the baseline pins, each counted once across the
# page's tabs (a text node, a scrolling box or an overlapping pair already counted in an earlier tab is
# not counted again). `scroll`: the page, or a box in it, scrolls sideways. `overflow`: a text node runs past the box it sits in sideways (an ellipsis cut
# included). `split`: a word, a run without spaces, lies on two lines. `overlap`: two text nodes'
# visible lines cross, SVG text included; each line is trimmed by a fifth top and bottom so two
# tight lines that only touch are not counted. `classes`: the class names no inventory selector
# uses and the component registry does not list. Text that is not displayed, fully transparent or clipped away is not read.
COUNT_JS = r"""
(arg) => {
  const reg = new Set(arg.registered);
  const hyphenParts = arg.hyphens.join(',');
  const lineOf = (el) => {
    let a = el;
    while (a && a !== document.body && /^(inline|contents|inline-block|inline-flex)$/.test(getComputedStyle(a).display)) a = a.parentElement;
    const s = getComputedStyle(a || document.body);
    return (a || document.body).getBoundingClientRect().width - parseFloat(s.paddingLeft) - parseFloat(s.paddingRight);
  };
  const hyphenBreak = (n, p, start, word) => {
    if (!hyphenParts || !p.closest(hyphenParts)) return false;
    let prev = null;
    for (let i = 0; i < word.length; i++) {
      const cr = document.createRange();
      cr.setStart(n, start + i);
      cr.setEnd(n, start + i + 1);
      const r = [...cr.getClientRects()].find((x) => x.width > 0.5);
      if (!r) continue;
      if (prev && Math.abs(r.top - prev.r.top) >= 2 && !/[-‐‑]/.test(word[prev.i])) return false;
      prev = { i, r };
    }
    const probe = document.createElement('span');
    probe.style.cssText = 'position:absolute;visibility:hidden;white-space:nowrap';
    probe.textContent = word;
    p.appendChild(probe);
    const whole = probe.getBoundingClientRect().width;
    probe.remove();
    return whole > lineOf(p);
  };
  const counted = window.__diCounted || (window.__diCounted = { nodes: new WeakSet(), boxes: new WeakSet(), pairs: new Set(), page: false });
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
  if (root.scrollWidth > root.clientWidth + 1 && !counted.page) {
    counted.page = true; scroll++; ex.scroll.push('page ' + root.scrollWidth + '>' + root.clientWidth);
  }
  for (const el of document.body.querySelectorAll('*')) {
    const s = getComputedStyle(el);
    if ((s.overflowX === 'auto' || s.overflowX === 'scroll') && el.scrollWidth > el.clientWidth + 1 && shown(el)
        && !counted.boxes.has(el)) {
      counted.boxes.add(el); scroll++; ex.scroll.push(label(el, '') + ' ' + el.scrollWidth + '>' + el.clientWidth);
    }
  }
  const lines = [];
  const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
  const ids = window.__diIds || (window.__diIds = new WeakMap());
  let next = window.__diNextId || 0;
  for (let n = walker.nextNode(); n; n = walker.nextNode()) {
    const txt = n.textContent;
    const p = n.parentElement;
    if (!txt.trim() || !p || p.closest('script,style,noscript,template') || !shown(p)) continue;
    if (!ids.has(n)) ids.set(n, ++next);
    const id = ids.get(n);
    const fresh = !counted.nodes.has(n);
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
    counted.nodes.add(n);
    if (!inSvg && fresh) {
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
          if (wt.length > 1 && !hyphenBreak(n, p, m.index, m[0])) { split++; ex.split.push(label(p, m[0])); }
        }
      }
    }
    for (const r of seen) {
      const h = r[3] - r[1];
      lines.push({ id, l: r[0], r: r[2], t: r[1] + h * 0.2, b: r[3] - h * 0.2, el: p, txt });
    }
  }
  window.__diNextId = next;
  lines.sort((a, b) => a.t - b.t);
  const pairs = new Set();
  for (let i = 0; i < lines.length; i++) {
    const a = lines[i];
    for (let j = i + 1; j < lines.length && lines[j].t < a.b; j++) {
      const b = lines[j];
      if (a.id === b.id || Math.min(a.r, b.r) - Math.max(a.l, b.l) <= 1) continue;
      const key = Math.min(a.id, b.id) + ':' + Math.max(a.id, b.id);
      if (!pairs.has(key) && !counted.pairs.has(key)) {
        pairs.add(key); counted.pairs.add(key); ex.overlap.push(label(a.el, a.txt) + ' x ' + label(b.el, b.txt));
      }
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
    const asked = props.filter((p) => el.kinds.includes(p));
    for (const n of nodes) {
      const s = getComputedStyle(n);
      const r = n.getBoundingClientRect();
      const m = {};
      if (asked.length) { m.style = {}; for (const p of asked) m.style[p] = s.getPropertyValue(p); }
      if (el.kinds.includes('min-box')) m.rect = [r.left, r.top, r.width, r.height];
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

# Playwright's object transport costs more CPU than the scripts themselves; a JSON string does not.
# What a page's rows would show, read from the rows and never from the element a miss is excused
# for. A row with the `hidden` attribute belongs to another day and counts for neither of the first
# two. `fold`: a competition group holds more rows than the page's visible rows (VISIBLE_ROWS,
# MatchesDay.astro). `score`: a row whose two scores differ (MatchRow.astro marks a winner only
# then; a played row that lost its score spans is still expected to show one). `filter`: the groups
# carry two values of a filter (FilterRows.astro offers a filter from two values).
PRESENCE_JS = r"""
() => {
  const shown = new Set();
  const groups = [...document.querySelectorAll('.fxgroup')];
  if (groups.some((g) => g.querySelectorAll('.fxrow:not([hidden])').length > %d)) shown.add('fold');
  const goals = (row) => [...row.querySelectorAll('.side .g')].map((g) => g.textContent.trim());
  if ([...document.querySelectorAll('.fxrow:not([hidden])')].some((r) => { const g = goals(r); return g.length === 2 ? g[0] !== g[1] : r.classList.contains('played'); })) shown.add('score');
  const distinct = (attr) => new Set(groups.map((g) => g.getAttribute(attr)).filter(Boolean)).size;
  if (distinct('data-entity-type') >= 2 || distinct('data-confederation') >= 2) shown.add('filter');
  return [...shown];
}
""" % di.visible_rows()
PRESENCE_JSON_JS = "() => JSON.stringify((%s)())" % PRESENCE_JS.strip()

MEASURE_JSON_JS = "(spec) => JSON.stringify((%s)(spec))" % MEASURE_JS.strip()
COUNT_JSON_JS = "(arg) => JSON.stringify((%s)(arg))" % COUNT_JS.strip()


POINTER_JS = r"""
(sel) => {
  const all = [...document.querySelectorAll(sel)];
  const i = all.findIndex((e) => e.getClientRects().length > 0);
  if (i < 0) return null;
  all[i].scrollIntoView({ block: 'center' });
  const r = all[i].getBoundingClientRect();
  return [r.left + r.width / 2, r.top + r.height / 2, i];
}
"""
STYLE_JS = "([sel, i, prop]) => getComputedStyle(document.querySelectorAll(sel)[i]).getPropertyValue(prop)"

# A page's tabs are radio inputs (`input.tab-in`); the ones not open on load, in page order.
TABS_JS = "() => [...document.querySelectorAll('input.tab-in[type=radio]')].filter((r) => !r.checked && r.id).map((r) => r.id)"
# The in-page tabs a shown Tab bar (`nav.tabs`) offers, the labels of its radio inputs (a tab that
# links to another page is that page's own); more than one with none to open means the check would
# measure the first tab alone.
TAB_BAR_JS = "() => [...document.querySelectorAll('nav.tabs')].filter((n) => n.getClientRects().length).reduce((n, bar) => Math.max(n, bar.querySelectorAll('label.tab').length), 0)"

# Open one tab as a reader's click does, let the site's script re-fit its blocks, then settle.
OPEN_TAB_JS = r"""
(id) => {
  const r = document.getElementById(id);
  r.checked = true;
  r.dispatchEvent(new Event('change', { bubbles: true }));
  window.dispatchEvent(new Event('resize'));
  window.scrollTo(0, 0);
  return document.fonts.ready.then(() => new Promise((res) => requestAnimationFrame(() => requestAnimationFrame(res))));
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


CONTINUED = " (continued)"


def join_continued(pages: list[di.Page]) -> list[di.Page]:
    """A row named `X (continued)` is no page of its own: row X also expects what it lists. One
    that does not repeat X's kind, source, URL and FI mode stays a row of its own."""
    out: dict[str, di.Page] = {}
    for p in pages:
        base = p.name.removesuffix(CONTINUED)
        first = out.get(base)
        if p.name != base and first is not None and (
                first.kind, first.source, first.url, first.fi) == (p.kind, p.source, p.url, p.fi):
            out[base] = dataclasses.replace(
                first, expect=first.expect + p.expect, expect_when=first.expect_when + p.expect_when)
        else:
            out[p.name] = p
    return list(out.values())


def plan(pages: list[di.Page], langs: list[str], dist: Path | None, mock_out: dict[str, Path],
         mock_failed: dict[str, str], every_file: bool) -> Plan:
    """Every built file and every generator page, each owned by the row that names it, a
    continued row joined to its page first (`join_continued`). A file two pages match belongs to
    the one with the literal URL; two patterns matching one file is an inventory failure. With
    `every_file`, the files no row owns are rendered too, each under its own path, and counted as a
    gap."""
    pages = join_continued(pages)
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
                 failures: list[Failure], acc: dict | None = None) -> int:
    """Measure one rendered page in its current tab; append failures; return the number of visible
    inventory matches. With `acc`, the page's tabs are measured one after another: a failure already
    found in an earlier tab is not added again, and the checks that ask whether an element is on the
    page are left to `finish_page`, which judges them across every tab."""
    data = json.loads(pw_page.evaluate(MEASURE_JSON_JS, spec))
    tokens = data["tokens"]
    total = 0
    seen: set[str] = set()
    own = acc is None
    if own:
        acc = {"seen": set(), "visible": {}, "total": 0, "found": set()}
    start = len(failures)
    if any(page.name == p for p, _ in di.PRESENCE_NEEDS):
        acc.setdefault("rows", set()).update(json.loads(pw_page.evaluate(PRESENCE_JSON_JS)))
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
                    key = (el.name, a.raw)
                    best = acc["visible"].get(key)
                    if best is None or len(matches) > best[2]:
                        acc["visible"][key] = (el.name, a, len(matches), tokens, level)
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
            # The first element with a box, scrolled to the middle; the mouse goes to its centre.
            centre = pw_page.evaluate(POINTER_JS, el.selector)
            if centre is None:
                continue
            at_centre = False
            for a in pointer:
                if not at_centre:
                    pw_page.mouse.move(centre[0], centre[1])
                    at_centre = True
                if a.kind == "press":
                    pw_page.mouse.down()
                measured = pw_page.evaluate(STYLE_JS, [el.selector, centre[2], a.prop])
                if a.kind == "press":
                    pw_page.mouse.move(0, 0)
                    pw_page.mouse.up()
                    at_centre = False
                msg = di.compare(a, measured, tokens)
                if msg:
                    failures.append(Failure(page.name, viewport, lang, "%s [%s #1]" % (el.name, el.selector), msg, level))
            if at_centre:
                pw_page.mouse.move(0, 0)
    fresh = []
    for f in failures[start:]:
        key = (f.element, f.detail, f.level)
        if key not in acc["found"]:
            acc["found"].add(key)
            fresh.append(f)
    failures[start:] = fresh
    acc["seen"] |= seen
    acc["total"] += total
    if own:
        finish_page(acc, page, viewport, lang, failures)
    return total


def finish_page(acc: dict, page: di.Page, viewport: int, lang: str, failures: list[Failure],
                added_width: bool = False) -> None:
    """The checks that ask whether an element is on the page, judged across every tab measured: an
    element counts as shown when one tab shows it, at the most matches any tab shows. At an added
    width (`BUILT_ONLY_VIEWPORTS` in a full run) a page that expects nothing, one no row owns, does
    not repeat the finding that nothing was measured on it: its pin counts that over the other
    widths."""
    for name, a, count, tokens, level in acc["visible"].values():
        msg = di.compare(a, count, tokens)
        if msg:
            failures.append(Failure(page.name, viewport, lang, name, msg, level))
    for name in page.expected_at(viewport):
        need = di.PRESENCE_NEEDS.get((page.name, name))
        if need and need not in acc.get("rows", ()):
            continue
        if name not in acc["seen"]:
            failures.append(Failure(page.name, viewport, lang, name, "expected on this page · measured 0 matches"))
    if acc["total"] == 0 and not (added_width and not page.expect):
        failures.append(Failure(page.name, viewport, lang, "(page)", "expected inventory elements · measured 0 — is the URL right?"))


def in_baseline_scope(baseline: dict, viewports: list[int], langs: list[str]) -> bool:
    """Whether a run over these widths and languages is the run the baseline pins: the ones it
    names, every one when it names none."""
    return (sorted(viewports) == sorted(baseline.get("viewports", DEFAULT_VIEWPORTS))
            and sorted(langs) == sorted(baseline.get("langs", DEFAULT_LANGS)))


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


# Back to the state a fresh load leaves: the tabs open on load open again, nothing focused, scrolled
# to the top, the gap count's memory of the page cleared; the site's scripts re-fit on the resize and
# the change, then two frames settle.
RESET_JS = r"""
() => {
  for (const r of window.__diOnLoad) {
    if (!r.checked) { r.checked = true; r.dispatchEvent(new Event('change', { bubbles: true })); }
  }
  if (document.activeElement && document.activeElement !== document.body) document.activeElement.blur();
  delete window.__diCounted; delete window.__diIds; delete window.__diNextId;
  window.scrollTo(0, 0);
  return document.fonts.ready.then(() => new Promise((res) => requestAnimationFrame(() => requestAnimationFrame(res))));
}
"""
OPEN_ON_LOAD_JS = "() => { window.__diOnLoad = [...document.querySelectorAll('input[type=radio]')].filter((r) => r.checked); }"


def render_one(pw_page, job: dict, p, lang: str, viewport: int, shots: list[int]) -> tuple[list[Failure], list[dict], bool]:
    """One target at one width, in the page as it stands: open each of its tabs, measure its
    elements, count its gaps. Returns its failures, each tab's gap count, and whether a screenshot
    was taken (a full-page screenshot resizes the page, so the next width needs a fresh load)."""
    inv, spec, artifacts = job["inv"], job["spec"], job["artifacts"]
    failures: list[Failure] = []
    founds: list[dict] = []
    shot = False
    acc = {"seen": set(), "visible": {}, "total": 0, "found": set()}
    tabs = pw_page.evaluate(TABS_JS)
    if not tabs and pw_page.evaluate(TAB_BAR_JS) > 1:
        failures.append(Failure(p.name, viewport, lang, "(page)",
                                "a Tab bar with no tab to open · only the first tab is measured"))
    for tab in [None] + tabs:
        if tab is not None:
            pw_page.evaluate(OPEN_TAB_JS, tab)
        state = len(failures)
        measure_page(pw_page, inv, spec, p, viewport, lang, failures, acc)
        # The pointer checks scroll the page, and a sticky header then lies over the content.
        pw_page.evaluate("window.scrollTo(0, 0); document.fonts.ready.then(() => new Promise((r) => requestAnimationFrame(() => r())))")
        found = json.loads(pw_page.evaluate(COUNT_JSON_JS, {"registered": job["registered"], "hyphens": job["hyphens"]}))
        founds.append({"classes": found["classes"], "ex": {k: found["ex"][k][:20] for k in COUNTS[:-1]},
                       **{k: found[k] for k in COUNTS[:-1]}})
        # After the count, which the screenshot's resize would otherwise change.
        if artifacts and any(f.level == "FAIL" for f in failures[state:]) and shots[0] < 20:
            pw_page.screenshot(path=str(Path(artifacts) / ("%s_%d_%s%s.png" % (
                p.name.replace("/", "_"), viewport, lang, "_" + tab if tab else ""))), full_page=True)
            shots[0] += 1
            shot = True
    state = len(failures)
    finish_page(acc, p, viewport, lang, failures, viewport in job["built_only"])
    if artifacts and any(f.level == "FAIL" for f in failures[state:]) and shots[0] < 20:
        pw_page.screenshot(path=str(Path(artifacts) / ("%s_%d_%s_page.png" % (
            p.name.replace("/", "_"), viewport, lang))), full_page=True)
        shots[0] += 1
        shot = True
    for f in failures:
        if f.level == "FAIL":
            f.measured = True
    return failures, founds, shot


def render_targets(job: dict) -> list[tuple[int, int, list[Failure], list[dict] | None]]:
    """Some of the targets, in their own process: each loaded once at the first width, then resized
    through the others; a mock page is not rendered at the job's `built_only` widths. Returns
    (target index, width index, failures, gap counts) per render; no gap counts when the page could
    not be rendered."""
    from playwright.sync_api import sync_playwright  # noqa: PLC0415

    viewports = job["viewports"]
    out = []
    shots = [0]
    with sync_playwright() as pw:
        # Hinting rounds Linux text to whole pixels, a layout phones and Windows do not produce.
        browser = pw.chromium.launch(args=["--font-render-hinting=none"])
        ctx = browser.new_context(viewport={"width": viewports[0], "height": 900}, device_scale_factor=1,
                                  reduced_motion="reduce")
        pw_page = ctx.new_page()

        def load(p, lang: str, url: str, viewport: int) -> str | None:
            """A fresh load at this width; why the page cannot be rendered, or None."""
            pw_page.set_viewport_size({"width": viewport, "height": 900})
            pw_page.goto(url, wait_until="load")
            if p.kind == "mock" and lang == "fi":
                label = pw_page.query_selector('label[for="t-fi"]')
                if label is None:
                    return "no FI toggle on the page"
                label.click()
                if not pw_page.is_checked("#t-fi"):
                    return "the FI toggle did not switch"
            pw_page.evaluate(OPEN_ON_LOAD_JS)
            return None

        for i, (p, lang, root, path) in job["targets"]:
            url = job["bases"][root] + path
            fresh = True
            for w, viewport in enumerate(viewports):
                if p.kind == "mock" and viewport in job["built_only"]:
                    continue
                if fresh:
                    why = load(p, lang, url, viewport)
                    if why:
                        out.append((i, w, [Failure(p.name, viewport, lang, "(page)", why)], None))
                        continue
                else:
                    pw_page.set_viewport_size({"width": viewport, "height": 900})
                    pw_page.evaluate(RESET_JS)
                failures, founds, fresh = render_one(pw_page, job, p, lang, viewport, shots)
                out.append((i, w, failures, founds))
        ctx.close()
        browser.close()
    return out


def collect(targets: list, viewports: list[int], rendered: list, built_only: tuple = ()) -> list[dict]:
    """Per width, the failures, gap counts, coverage and render count, each in the order the
    targets are listed. A mock page has no render at a `built_only` width; any other render the
    list lacks raises."""
    at = {(i, w): (f, founds) for i, w, f, founds in rendered}
    results = []
    for w, viewport in enumerate(viewports):
        failures: list[Failure] = []
        counted: dict[str, dict] = {}
        covered: dict[str, set[str]] = {}
        renders = 0
        for i, (p, lang, _root, _path) in enumerate(targets):
            if p.kind == "mock" and viewport in built_only:
                continue
            fails, founds = at[(i, w)]
            failures += fails
            if founds is None:
                continue
            page_counts = counted.setdefault(p.name, {"classes": set(), "examples": {}})
            for found in founds:
                page_counts["classes"].update(found["classes"])
                for k in COUNTS[:-1]:
                    page_counts[k] = page_counts.get(k, 0) + found[k]
                    shown = page_counts["examples"].setdefault(k, [])
                    shown += ["%d %s %s" % (viewport, lang, e) for e in found["ex"][k][:20 - len(shown)]]
            renders += 1
            covered.setdefault(lang, set()).add(p.name)
        results.append({"failures": failures, "counted": counted, "covered": covered, "renders": renders})
    return results


def registry_classes(path: Path = REGISTRY) -> frozenset[str]:
    """Every class the component registry lists, a part with no rule yet included: that part is the
    registry's own gap, counted once in its gap count."""
    reg = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    return frozenset(part["class"] for comp in reg["components"].values() for part in comp["parts"].values())


def hyphen_selectors(path: Path = REGISTRY) -> list[str]:
    """The selector of every registry part that may break a word at its hyphens."""
    reg = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    return sorted({part.get("selector") or "." + part["class"] for comp in reg["components"].values()
                   for part in comp["parts"].values() if part.get("breaks") == "hyphens"})


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--inventory", default=str(di.DOC))
    ap.add_argument("--registry", default=str(REGISTRY))
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
    # Joined before --pages picks by name, so a page is selected with its continued row.
    rows = join_continued(inv.pages)
    pages = [p for p in rows if (wanted is None or p.name in wanted)
             and not (args.no_built and p.kind == "built") and not (args.no_mocks and p.kind == "mock")]
    adhoc = []
    for spec in args.page:
        name, _, file = spec.partition("=")
        if not name or not file:
            ap.error("--page needs NAME=FILE.html")
        adhoc.append((name, Path(file).resolve()))
    if wanted:
        missing = wanted - {p.name for p in rows}
        if missing:
            ap.error("unknown page(s): %s" % ", ".join(sorted(missing)))
    viewports = [int(v) for v in args.viewports.split(",")] if args.viewports else list(DEFAULT_VIEWPORTS)
    built_only = () if args.viewports else BUILT_ONLY_VIEWPORTS
    langs = args.langs.split(",")
    baseline = di.load_baseline(Path(args.baseline))
    # The baseline pins a run over every page, over the widths and languages it names (all of them
    # when it names none); a run over anything less prints its counts and compares none.
    full_run = not (wanted or adhoc or args.no_built or args.no_mocks) \
        and in_baseline_scope(baseline, viewports, langs)
    registered = sorted(di.class_tokens(inv.elements) | registry_classes(Path(args.registry)))
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
            workers = max(1, min(len(targets), os.cpu_count() or 1))
            # Interleaved, so each process gets the same mix of light and heavy pages.
            jobs = [{"viewports": viewports, "built_only": built_only,
                     "targets": list(enumerate(targets))[k::workers], "bases": bases,
                     "inv": inv, "spec": spec, "registered": registered,
                     "hyphens": hyphen_selectors(Path(args.registry)),
                     "artifacts": str(artifacts) if artifacts else None} for k in range(workers)]
            if len(jobs) == 1:
                rendered = render_targets(jobs[0])
            else:
                with ProcessPoolExecutor(max_workers=workers) as pool:
                    rendered = [r for part in pool.map(render_targets, jobs) for r in part]
            results = collect(targets, viewports, rendered, built_only)
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
