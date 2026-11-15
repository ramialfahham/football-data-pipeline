"""Measures the phone rules on the built site at 260-768px in EN, DE and FI: tap areas, separator dots, square linked rows and no sideways scroll.

Needs `site_v2/dist` and Playwright's Chromium (the validate:ui image); skipped without them.
"""

import functools
import http.server
import threading
from pathlib import Path

import pytest

DIST = Path(__file__).resolve().parents[1] / "site_v2" / "dist"
WIDTHS = [260, 280, 320, 375, 768]
HEADER_ICON_NARROW = 340

pytestmark = pytest.mark.skipif(not (DIST / "en" / "index.html").exists(), reason="no built site")
sync_api = pytest.importorskip("playwright.sync_api")


def _first(pattern: str) -> str:
    hit = sorted(DIST.glob(pattern))
    if not hit:
        pytest.fail(f"the built site has no page for {pattern}")
    return "/" + hit[0].parent.relative_to(DIST).as_posix() + "/"


def _pages() -> list[str]:
    pages = ["/en/", "/de/", "/fi/", "/en/competitions/", "/en/teams/", "/en/players/", "/en/matches/"]
    for lang, teams, players, matches in (
        ("en", "teams", "players", "matches"),
        ("de", "mannschaften", "spieler", "spiele"),
        ("fi", "joukkueet", "pelaajat", "ottelut"),
    ):
        pages += [
            _first(f"{lang}/{teams}/1-fc-koln/index.html"),
            _first(f"{lang}/{players}/a-daghim-362564/index.html"),
            _first(f"{lang}/bundesliga/{matches}/2026-10-18-*/index.html"),
            _first(f"{lang}/bundesliga/index.html"),
        ]
    return sorted(set(pages))


TAPS = """
() => {
  const out = [];
  const els = [...document.querySelectorAll('a[href], button, summary, select, label[for]')];
  for (const e of els) {
    const rects = [...e.getClientRects()];
    if (!rects.length || getComputedStyle(e).visibility === 'hidden') continue;
    let w = Math.max(...rects.map((r) => r.width)), h = Math.max(...rects.map((r) => r.height));
    if (w < 1.5) continue;
    const layer = getComputedStyle(e, '::after');
    if (layer.position === 'absolute' && layer.content !== 'none') {
      w = Math.max(w, parseFloat(layer.width) || 0);
      h = Math.max(h, parseFloat(layer.height) || 0);
    }
    const p = e.closest('p, li, div');
    const inText = e.tagName === 'A' && getComputedStyle(e).display === 'inline' && p && p !== e.parentElement
      && [...p.childNodes].filter((n) => n !== e).map((n) => n.textContent).join('').replace(/[\\s·›]+/g, '').length > 8;
    if (inText) continue;
    const icon = e.classList.contains('iconbtn');
    if (h < 43.5 || (w < 43.5 && !(icon && innerWidth <= %d && w >= 33.5))) out.push(`${e.tagName}.${[...e.classList].join('.')} ${Math.round(w)}x${Math.round(h)} ${(e.textContent || '').trim().slice(0, 20)}`);
  }
  return out;
}
""" % HEADER_ICON_NARROW

DOTS = """
() => {
  const bad = [];
  const shown = (el) => el.getClientRects().length > 0;
  for (const d of document.querySelectorAll('[data-dot]')) {
    if (d.hidden) {
      d.hidden = false;
      const r = d.getClientRects()[0];
      let host = d.parentElement;
      while (host.parentElement && ['inline', 'inline-block', 'contents'].includes(getComputedStyle(host).display)) host = host.parentElement;
      const w = document.createTreeWalker(host, NodeFilter.SHOW_TEXT);
      w.currentNode = d;
      let before = null;
      for (let n = w.previousNode(); n && !before; n = w.previousNode()) {
        if (!n.textContent.trim() || n.parentElement.closest('[data-dot]') || !n.parentElement.getClientRects().length) continue;
        const range = document.createRange();
        range.selectNodeContents(n);
        const rs = range.getClientRects();
        if (rs.length) before = rs[rs.length - 1];
      }
      if (r && before && r.top < before.bottom - 1) bad.push('hidden but on the line of the text before it: ' + host.textContent.trim().slice(0, 50));
      d.hidden = true;
      continue;
    }
    if (!shown(d)) continue;
    const rect = d.getClientRects()[0];
    let host = d.parentElement;
    while (host.parentElement && ['inline', 'inline-block', 'contents'].includes(getComputedStyle(host).display)) host = host.parentElement;
    const walk = (dir) => {
      const w = document.createTreeWalker(host, NodeFilter.SHOW_TEXT);
      w.currentNode = d;
      for (let n = dir > 0 ? w.nextNode() : w.previousNode(); n; n = dir > 0 ? w.nextNode() : w.previousNode()) {
        if (!n.textContent.trim() || n.parentElement.closest('[data-dot]') || !shown(n.parentElement)) continue;
        const r = document.createRange();
        r.selectNodeContents(n);
        const rs = r.getClientRects();
        if (rs.length) return dir > 0 ? rs[0] : rs[rs.length - 1];
      }
      return null;
    };
    const before = walk(-1), after = walk(1);
    if (!before || rect.top >= before.bottom - 1) bad.push('starts a line: ' + host.textContent.trim().slice(0, 50));
    else if (after && after.top >= rect.bottom - 1) bad.push('ends a line: ' + host.textContent.trim().slice(0, 50));
  }
  return bad;
}
"""

ROWS = """
() => [...document.querySelectorAll('a.fxrow, a.ctab-row, a.frow, a.lrow, a.brow, a.comp-row')]
  .filter((e) => e.getClientRects().length)
  .filter((e) => { const s = getComputedStyle(e); return s.borderTopLeftRadius !== '0px' || parseFloat(s.marginLeft) < 0 || parseFloat(s.marginRight) < 0; })
  .map((e) => e.className)
"""


@pytest.fixture(scope="module")
def site():
    class Quiet(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *args, **kwargs):
            pass

    handler = functools.partial(Quiet, directory=str(DIST))
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{server.server_address[1]}"
    server.shutdown()


@pytest.fixture(scope="module")
def browser():
    with sync_api.sync_playwright() as p:
        b = p.chromium.launch()
        yield b
        b.close()


def _measure(browser, site, script: str) -> list[str]:
    found: list[str] = []
    for width in WIDTHS:
        page = browser.new_context(viewport={"width": width, "height": 900}).new_page()
        for url in _pages():
            page.goto(site + url, wait_until="load")
            page.wait_for_timeout(200)
            found += [f"{width}px {url} {item}" for item in page.evaluate(script)]
        page.close()
    return found


def test_the_header_fits_at_280_and_300px(browser, site):
    found = []
    for width in (280, 300):
        page = browser.new_context(viewport={"width": width, "height": 900}).new_page()
        for url in ("/en/", "/de/", "/fi/", "/en/teams/"):
            page.goto(site + url, wait_until="load")
            page.wait_for_timeout(200)
            if page.evaluate("(() => { const h = document.querySelector('.header-in'); return h.scrollWidth > h.clientWidth; })()"):
                found.append(f"{width}px {url}")
        page.close()
    assert found == []


def test_no_page_scrolls_sideways(browser, site):
    found = []
    for width in WIDTHS[1:]:
        page = browser.new_context(viewport={"width": width, "height": 900}).new_page()
        for url in _pages():
            page.goto(site + url, wait_until="load")
            page.wait_for_timeout(200)
            if page.evaluate("document.documentElement.scrollWidth > innerWidth"):
                found.append(f"{width}px {url}")
        page.close()
    assert found == []


def test_every_link_and_button_has_a_44px_tap_area(browser, site):
    assert _measure(browser, site, TAPS) == []


def test_no_separator_dot_starts_or_ends_a_line(browser, site):
    assert _measure(browser, site, DOTS) == []


def test_linked_rows_are_square_and_do_not_stick_out(browser, site):
    assert _measure(browser, site, ROWS) == []


PICKER = """
() => {
  const title = document.querySelector('.mdstep [data-long]')?.closest('.mdtitle');
  if (!title) return null;
  const shown = [...title.querySelectorAll('[data-long], [data-short]')].filter((e) => e.getClientRects().length);
  return {
    form: shown.map((e) => (e.hasAttribute('data-long') ? 'long' : 'short')).join(),
    text: shown.map((e) => e.textContent.trim()).join(),
    overflow: title.scrollWidth > title.clientWidth + 0.5,
  };
}
"""


@pytest.mark.parametrize("url", ["/en/matches/", "/de/spiele/", "/fi/ottelut/"])
def test_the_day_picker_shows_the_short_date_where_the_long_one_does_not_fit(browser, site, url):
    import re

    seen = {}
    for width in (280, 1010):
        page = browser.new_context(viewport={"width": width, "height": 900}).new_page()
        page.goto(site + url, wait_until="load")
        page.wait_for_timeout(300)
        seen[width] = page.evaluate(PICKER)
        page.close()
    assert seen[280] is not None
    assert seen[280]["form"] == "short" and re.fullmatch(r"[^\W\d_]{2} \d{1,2}\.\d{1,2}\.", seen[280]["text"]), seen[280]
    assert seen[1010]["form"] == "long", seen[1010]
    assert not seen[280]["overflow"] and not seen[1010]["overflow"]
