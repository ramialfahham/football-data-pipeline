"""Regenerate the README screenshots: python scripts/readme_screenshots.py

Serves an existing site_v2/dist (run `npm run build` in site_v2 first, the script never builds) and
saves three crops (the page top and two named blocks) of five pages, each at phone and desktop width,
to docs/images/readme/. Player photos are replaced by the initials fallback; club crests stay.
A page whose approved design is not built yet can come from a design mock instead:
--mock <home|match|played|team|player>=<html file>, repeatable. The mock files are not in the
repository; pass the path of each approved mock. Without --mock every page is the built one.
"""
from __future__ import annotations

import functools
import http.server
import sys
import threading
from pathlib import Path

from playwright.sync_api import TimeoutError as PlaywrightTimeout
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
SITE = ROOT / "site_v2"
DIST = SITE / "dist"
OUT = ROOT / "docs" / "images" / "readme"

PAGES = {
    "home": ("en/", None),
    "match": ("en/bundesliga/matches/2026-10-18-bayer-04-leverkusen-vs-sc-freiburg/", None),
    "played": ("en/bundesliga/matches/2026-09-05-tsg-1899-hoffenheim-vs-borussia-dortmund/", None),
    "team": ("en/teams/1-fc-koln/", "tab-performance"),
    "player": ("en/players/e-haaland-1100/", None),
}
BLOCKS = {
    "home": [("block", None, ".eyebrow >> text=\"Top players\" >> visible=true", 80), ("block2", None, ".eyebrow >> text=\"Top teams\" >> visible=true", 80)],
    "match": [("block", None, ".eyebrow >> text=\"Players to watch\" >> visible=true", 90), ("block2", None, ".eyebrow >> text=\"Head to head\" >> visible=true", 90)],
    "played": [("block", None, ".eyebrow >> text=\"Match leaders\" >> visible=true", 90), ("block2", None, ".eyebrow >> text=\"Match statistics\" >> visible=true", 90)],
    "team": [
        ("block", None, "svg.dp-chart >> visible=true", 150),
        ("block2", "tab-overview", ".eyebrow >> text=\"Competitions\" >> visible=true", 90),
    ],
    "player": [("block", None, ".eyebrow >> text=\"Compared with other players\" >> visible=true", 80), ("block2", None, ".eyebrow >> text=\"Recent matches\" >> visible=true", 90)],
}
PHOTO_SELECTOR = '.pphoto img, img[src*="/football/players/"]'
STRIP_PLAYER_PHOTOS = (
    """() => {
  const initials = (el, n) => {
    const row = el.closest('.plrow, header, .ctab-row');
    const nm = row && row.querySelector('.nm, h1');
    return ((nm && nm.textContent) || '').trim().split(/\\s+/).map(w => w[0] || '').join('').slice(0, n).toUpperCase();
  };
  let bad = 0;
  document.querySelectorAll('%s').forEach(img => {
    const slot = img.parentElement;
    const span = document.createElement('span');
    span.textContent = initials(img, slot.classList.contains('pphoto') ? 2 : 3);
    img.replaceWith(span);
    if (!span.textContent) bad += 1;
  });
  return bad + document.querySelectorAll('%s').length;
}"""
    % (PHOTO_SELECTOR, PHOTO_SELECTOR)
)
IMAGES_LOADED = """() => [...document.images].every(i => {
  const r = i.getBoundingClientRect();
  return r.bottom < 0 || r.top > innerHeight || (i.complete && i.naturalWidth > 0);
})"""
VIEWPORTS = {"phone": (375, 812), "desktop": (1010, 900)}
MAX_BYTES = 300 * 1024


def require_dist() -> None:
    if not (DIST / "en" / "index.html").exists():
        sys.exit("site_v2/dist is missing: run `npm run build` in site_v2 first")


def serve() -> tuple[http.server.ThreadingHTTPServer, int]:
    class Quiet(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *args):
            pass

    handler = functools.partial(Quiet, directory=str(DIST))
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server, server.server_address[1]


def parse_mocks(argv: list[str]) -> dict[str, Path]:
    mocks: dict[str, Path] = {}
    args = iter(argv)
    for arg in args:
        if arg != "--mock":
            sys.exit(f"unknown argument {arg}; usage: --mock <page>=<html file> (page: {', '.join(PAGES)})")
        name, _, file = next(args, "").partition("=")
        if name not in PAGES or not Path(file).is_file():
            sys.exit(f"--mock needs <page>=<html file>, page one of: {', '.join(PAGES)}")
        mocks[name] = Path(file).resolve()
    return mocks


def main() -> None:
    mocks = parse_mocks(sys.argv[1:])
    if len(mocks) < len(PAGES):
        require_dist()
    OUT.mkdir(parents=True, exist_ok=True)
    server, port = serve()
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            for width_name, (w, h) in VIEWPORTS.items():
                ctx = browser.new_context(viewport={"width": w, "height": h}, color_scheme="light", reduced_motion="reduce")
                page = ctx.new_page()
                for name, (path, tab) in PAGES.items():
                    url = mocks[name].as_uri() if name in mocks else f"http://127.0.0.1:{port}/{path}"
                    response = page.goto(url, wait_until="load")
                    if response is not None and response.status >= 400:
                        sys.exit(f"{url}: HTTP {response.status}")
                    try:
                        page.wait_for_load_state("networkidle", timeout=15000)
                    except PlaywrightTimeout:
                        pass
                    if name in mocks:
                        page.add_style_tag(content=".mock-ctl, .ctl, .mock-lang{display:none !important}")
                    left = page.evaluate(STRIP_PLAYER_PHOTOS)
                    if left:
                        sys.exit(f"{name}: {left} player photos remain")
                    page.evaluate("document.querySelectorAll('img[loading=lazy]').forEach(i => { i.loading = 'eager'; })")
                    try:
                        page.wait_for_load_state("networkidle", timeout=15000)
                    except PlaywrightTimeout:
                        pass
                    if tab:
                        page.click(f"label[for='{tab}']")
                    page.evaluate("window.scrollTo(0, 0)")
                    data = (page.screenshot(clip={"x": 0, "y": 0, "width": w, "height": h}))
                    if len(data) > MAX_BYTES:
                        sys.exit(f"{name}-{width_name}: {len(data)} bytes exceeds {MAX_BYTES}")
                    (OUT / f"{name}-{width_name}.png").write_bytes(data)
                    print(f"{name}-{width_name}.png {len(data) // 1024} KB")
                    for suffix, block_tab, selector, lead in BLOCKS.get(name, []):
                        if block_tab:
                            page.click(f"label[for='{block_tab}']")
                        block = page.locator(selector).first
                        try:
                            block.wait_for(state="attached", timeout=10000)
                        except PlaywrightTimeout:
                            sys.exit(f"{name}-{suffix}: no element matches {selector}")
                        top = block.evaluate("e => e.getBoundingClientRect().top + window.scrollY")
                        page.evaluate(f"window.scrollTo(0, {top - lead})")
                        try:
                            page.wait_for_function(IMAGES_LOADED, timeout=20000)
                        except PlaywrightTimeout:
                            sys.exit(f"{name}-{suffix}-{width_name}: an image in view did not load")
                        data = page.screenshot()
                        if len(data) > MAX_BYTES:
                            sys.exit(f"{name}-{suffix}-{width_name}: {len(data)} bytes exceeds {MAX_BYTES}")
                        (OUT / f"{name}-{suffix}-{width_name}.png").write_bytes(data)
                        print(f"{name}-{suffix}-{width_name}.png {len(data) // 1024} KB")
                ctx.close()
            browser.close()
    finally:
        server.shutdown()


if __name__ == "__main__":
    main()
