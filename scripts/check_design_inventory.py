"""The cross-page measured check: every page in the block standard, rendered and measured.

Renders every design-mock generator the inventory lists into a temporary folder, serves that
folder and the built site over HTTP, opens each page in headless Chromium at every viewport and
language the inventory asks for, and measures every element of `docs/wireframes/block_standard.md`
as its "Measured as" column says. One line per failure, and a page that shows none of the
inventory's elements fails on its own. Exit 0 clean, 1 on any failure, 2 when the inventory does
not parse or the browser is missing.

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
import shutil
import subprocess
import sys
import tempfile
import threading
from dataclasses import dataclass
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import design_inventory as di  # noqa: E402

REPO = di.REPO
MOCKS = REPO / "design-mocks"
# A phone, the width the menu goes inline, and the width the header's search field appears: the
# narrowest desktop layout. `tests/test_design_inventory.py` ties the last to `system.css`.
DEFAULT_VIEWPORTS = (375, 700, 1010)
# Every locale the site publishes. A language the check does not render is a language whose layout
# can break green — the tab bar's rule names EN, DE and FI, so all three are measured.
# `tests/test_design_inventory.py` pins this against the site's own `LOCALES`.
DEFAULT_LANGS = ("en", "de", "fi")

# The design mocks carry English and a marked Finnish width probe in one file, toggled by CSS;
# no other language exists in them to render.
MOCK_LANGS = ("en", "fi")

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


def render_mocks(pages: list[di.Page], tmp: Path) -> dict[str, str]:
    """Run each mock generator once; return {page name: failure text} for the ones that failed."""
    failed: dict[str, str] = {}
    done: set[str] = set()
    for p in pages:
        if p.kind != "mock":
            continue
        args = p.source.split()
        if "{out}" in args:
            args = [str(tmp / p.url) if a == "{out}" else a for a in args]
        key = " ".join(args)
        if key not in done:
            done.add(key)
            try:
                proc = subprocess.run([sys.executable, *args], cwd=str(MOCKS), capture_output=True, timeout=180)
            except subprocess.TimeoutExpired:
                failed[p.name] = "generator timed out: %s" % p.source
                continue
            if proc.returncode != 0:
                tail = proc.stderr.decode("utf-8", "replace").strip().splitlines()[-1:] or ["?"]
                failed[p.name] = "generator failed (%d): %s" % (proc.returncode, tail[-1])
                continue
        if "{out}" not in p.source:
            src = MOCKS / p.url
            if src.is_file():
                shutil.copy(src, tmp / p.url)
        if not (tmp / p.url).is_file() and p.name not in failed:
            failed[p.name] = "generator wrote no %s" % p.url
    return failed


def resolve_built(page: di.Page, dist: Path, lang: str) -> Path | None:
    url = page.url
    if lang != "en":
        url = url.replace("en/", "%s/" % lang, 1)
    hits = sorted(dist.glob(url))
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


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--inventory", default=str(di.DOC))
    ap.add_argument("--dist", default=str(REPO / "site_v2" / "dist"))
    ap.add_argument("--pages", help="comma-separated page names to run (default: all)")
    ap.add_argument("--viewports", default=",".join(str(v) for v in DEFAULT_VIEWPORTS))
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
    viewports = [int(v) for v in args.viewports.split(",")]
    langs = args.langs.split(",")
    props = list(di.PROPS)
    spec = {
        "props": props,
        "tokens": list(di.TOKENS),
        "elements": [{"name": e.name, "selector": e.selector, "kinds": [a.kind for a in e.assertions]} for e in inv.elements],
    }
    failures: list[Failure] = []
    renders = 0
    covered: dict[str, set[str]] = {}   # language -> the pages actually rendered in it
    artifacts = Path(args.artifacts) if args.artifacts else None
    if artifacts:
        artifacts.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        gen_failed = render_mocks(pages, tmp) if not args.no_mocks else {}
        for name, why in gen_failed.items():
            failures.append(Failure(name, 0, "-", "(generator)", why))
        mock_srv, mock_base = serve(tmp)
        dist = Path(args.dist)
        dist_srv, dist_base = (serve(dist) if dist.is_dir() else (None, None))
        # an ad-hoc page is served from its own folder, so a stylesheet beside it resolves
        adhoc_srv: dict[Path, tuple] = {}
        for _name, file in adhoc:
            if file.parent not in adhoc_srv:
                adhoc_srv[file.parent] = serve(file.parent)
        try:
            with sync_playwright() as pw:
                try:
                    browser = pw.chromium.launch()
                except PlaywrightError as exc:
                    print("cannot launch Chromium: %s" % str(exc).splitlines()[0], file=sys.stderr)
                    return 2
                for viewport in viewports:
                    ctx = browser.new_context(viewport={"width": viewport, "height": 900}, device_scale_factor=1,
                                              reduced_motion="reduce")
                    pw_page = ctx.new_page()
                    targets: list[tuple[di.Page, str, str]] = []
                    for p in pages:
                        if p.kind == "mock":
                            if p.name in gen_failed:
                                continue
                            for lang in langs:
                                if lang != "en" and p.fi == "none":
                                    continue
                                if lang not in MOCK_LANGS:
                                    continue
                                targets.append((p, lang, mock_base + p.url))
                        else:
                            if dist_base is None:
                                failures.append(Failure(p.name, viewport, "-", "(page)", "no built site at %s (astro build first, or --no-built)" % dist))
                                continue
                            for lang in langs:
                                hit = resolve_built(p, dist, lang)
                                if hit is None:
                                    failures.append(Failure(p.name, viewport, lang, "(page)", "no file matches %s under %s" % (p.url, dist)))
                                    continue
                                targets.append((p, lang, dist_base + hit.relative_to(dist).as_posix()))
                    for name, file in adhoc:
                        targets.append((di.Page(name, "mock", "", file.name, "none", ()), "en", adhoc_srv[file.parent][1] + file.name))
                    for p, lang, url in targets:
                        pw_page.goto(url, wait_until="load")
                        if p.kind == "mock" and lang == "fi" and p.fi == "toggle":
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
                        if artifacts and any(f.level == "FAIL" for f in failures[before:]):
                            pw_page.screenshot(path=str(artifacts / ("%s_%d_%s.png" % (p.name, viewport, lang))), full_page=True)
                    ctx.close()
                browser.close()
        finally:
            mock_srv.shutdown()
            if dist_srv:
                dist_srv.shutdown()
            for srv, _base in adhoc_srv.values():
                srv.shutdown()

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
          % (len(pages) + len(adhoc), len(viewports), len(langs), caveat, renders, len(hard), len(failures) - len(hard)))
    if artifacts and hard:
        (artifacts / "failures.json").write_text(json.dumps([f.__dict__ for f in failures], indent=1), encoding="utf-8")
    return 1 if hard else 0


if __name__ == "__main__":
    sys.exit(main())
