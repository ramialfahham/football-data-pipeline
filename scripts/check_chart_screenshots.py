"""The chart screenshot check: the site's charts pinned as screenshots of the built pages, each chart
mark in the colour the theme gives it, and the scatter plot's difference label clear of everything.

Serves the built site, opens it in headless Chromium and checks:
- colours: on the pages in `CHARTS`, in both themes, every mark in `MARKS` must compute to its
  theme colour, read from the page's own tokens; a selector that matches nothing fails, so a
  renamed class cannot pass by matching nothing;
- screenshots: each chart in `CHARTS` at 375px and 1010px, in English dark, English light and
  Finnish dark, as a reader reaches it (a click on its tab), is compared by the SHA-256 of its PNG
  with `tests/fixtures/chart_screenshots/` (`manifest.json` names the platform the pins were taken
  on and each file's hash). Text renders differently on each operating system, so
  pins are taken on Linux only: a manifest from any other platform fails everywhere, and a run
  off Linux compares nothing. The pages are built from the committed data, so a change to that data
  changes the pins too. On every platform each PNG in the pins must match its hash in the manifest
  and no PNG may be missing from it, so a changed look shows in the MR as a changed image. On any
  difference on Linux the new screenshots and manifest are written to `--artifacts`, so a changed
  look reaches the pins only as committed files in its MR;
- scatter labels: on every built page that draws a scatter plot, in every language and at every
  width in `LABEL_WIDTHS`, the difference label meets no line (the deserved points line, the dotted
  distance line, an axis or a tick), no dot, no other text and stays inside the drawing; a run that
  measures no scatter plot fails.

    python scripts/check_chart_screenshots.py --artifacts artifacts/chart_screenshots
    python scripts/check_chart_screenshots.py --update      # Linux only: rewrite the pins

Exit 0 clean, 1 on a colour, screenshot or label finding, 2 when the pins cannot be written here.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from check_design_inventory import serve  # noqa: E402

REPO = Path(__file__).resolve().parent.parent
DIST = REPO / "site_v2" / "dist"
PINS = REPO / "tests" / "fixtures" / "chart_screenshots"
PLATFORM = sys.platform
PIN_PLATFORM = "linux"
VIEWPORTS = (375, 1010)
STATES = (("en", "dark"), ("en", "light"), ("fi", "dark"))
TEAM = {"en": "en/teams/1-fc-koln/", "fi": "fi/joukkueet/1-fc-koln/"}
MATCH = {"en": "en/bundesliga/matches/2026-09-05-tsg-1899-hoffenheim-vs-borussia-dortmund/",
         "fi": "fi/bundesliga/ottelut/2026-09-05-tsg-1899-hoffenheim-vs-borussia-dortmund/"}
CHARTS = (("scatter", TEAM, ".chart", 0), ("strip", TEAM, ".chart", 1), ("comparison", MATCH, ".cmp", 0))
MARKS = {
    "team": (
        ("svg .chart-dot.chart-me", "fill", "--chart-team"),
        ("svg .chart-dot:not(.chart-me)", "fill", "--chart-other"),
        (".rs-band .chart-dot.chart-me", "background-color", "--chart-team"),
        (".rs-band .chart-dot:not(.chart-me)", "background-color", "--chart-other"),
    ),
    "match": (
        (".cmp-val.chart-better", "color", "--chart-better"),
        (".chart-bar > .chart-better > span", "background-color", "--chart-better"),
    ),
}

COLOUR_JS = """([marks]) => {
  const out = [], host = document.body, theme = host.dataset.theme;
  const probe = document.createElement('i');
  host.appendChild(probe);
  for (const [sel, prop, token] of marks) {
    probe.style.color = `var(${token})`;
    const want = getComputedStyle(probe).color;
    const els = [...host.querySelectorAll(sel)];
    if (!els.length) out.push(`${theme} · ${sel} · matches nothing`);
    for (const e of els) {
      const got = getComputedStyle(e).getPropertyValue(prop);
      if (got !== want) { out.push(`${theme} · ${sel} · ${prop} ${got}, the theme's ${token} is ${want}`); break; }
    }
  }
  probe.remove();
  return out;
}"""
# The way a reader reaches a chart: shown already, or shown by a click on one of the page's tabs.
REACH_JS = """([sel, n]) => {
  const shown = () => { const el = document.querySelectorAll(sel)[n]; return !!el && el.getBoundingClientRect().width > 0; };
  if (shown()) return true;
  for (const tab of document.querySelectorAll('label[for]')) {
    const input = document.getElementById(tab.htmlFor);
    if (!input || input.type !== 'radio') continue;
    tab.click();
    if (shown()) return true;
  }
  return false;
}"""
PAINTED_JS = "() => new Promise((r) => requestAnimationFrame(() => requestAnimationFrame(r)))"
THEME_JS = "(t) => { document.body.dataset.theme = t; }"
LABEL_WIDTHS = (280, 320, 360, 375, 414, 479, 480, 560, 700, 768, 900, 1010)
SCATTER_SHOWN = "() => [...document.querySelectorAll('svg.dp-chart')].some((s) => s.getBoundingClientRect().width > 0)"
LABEL_JS = """() => {
  const svg = [...document.querySelectorAll('svg.dp-chart')].find((s) => s.getBoundingClientRect().width > 0);
  const label = svg && svg.querySelector('[data-role="gap"]');
  if (!label) return null;
  const R = label.getBoundingClientRect(), m = svg.getScreenCTM(), out = [];
  const at = (l, x, y) => new DOMPoint(+l.getAttribute(x), +l.getAttribute(y)).matrixTransform(m);
  const side = (p, q, s) => (s.x - p.x) * (q.y - p.y) - (s.y - p.y) * (q.x - p.x);
  const cross = (p, q, s, u) => (side(s, u, p) > 0) !== (side(s, u, q) > 0) && (side(p, q, s) > 0) !== (side(p, q, u) > 0);
  const Q = { l: R.left - 1, t: R.top - 1, r: R.right + 1, b: R.bottom + 1 };
  const inQ = (p) => p.x > Q.l && p.x < Q.r && p.y > Q.t && p.y < Q.b;
  const corners = [{ x: Q.l, y: Q.t }, { x: Q.r, y: Q.t }, { x: Q.r, y: Q.b }, { x: Q.l, y: Q.b }];
  const lineMeets = (l) => { const a = at(l, 'x1', 'y1'), b = at(l, 'x2', 'y2');
    return inQ(a) || inQ(b) || corners.some((s, i) => cross(a, b, s, corners[(i + 1) % 4])); };
  const name = (l) => l.classList.contains('chart-ref') ? 'the deserved points line'
    : l.classList.contains('chart-gap') ? 'the dotted distance line' : 'an axis or tick';
  for (const l of svg.querySelectorAll('line')) if (lineMeets(l)) out.push(name(l));
  for (const c of svg.querySelectorAll('circle')) {
    const d = c.getBoundingClientRect(), cx = (d.left + d.right) / 2, cy = (d.top + d.bottom) / 2, r = (d.right - d.left) / 2;
    const nx = Math.max(R.left, Math.min(cx, R.right)), ny = Math.max(R.top, Math.min(cy, R.bottom));
    if ((nx - cx) ** 2 + (ny - cy) ** 2 < r * r) out.push('a dot');
  }
  for (const t of svg.querySelectorAll('text')) {
    const b = t.getBoundingClientRect();
    if (t !== label && b.left < R.right && R.left < b.right && b.top < R.bottom && R.top < b.bottom) out.push('the text "' + t.textContent + '"');
  }
  const S = svg.getBoundingClientRect();
  if (R.left < S.left || R.right > S.right || R.top < S.top || R.bottom > S.bottom) out.push('the edge of the drawing');
  return [...new Set(out)];
}"""
# A reader's click on a tab label, then the measurement, in one task: no frame is rendered in between,
# so only what the click itself runs counts, as in a page the browser is not painting.
READER_JS = """() => {
  const shown = %s;
  const measure = %s;
  for (const tab of document.querySelectorAll('label[for]')) {
    const input = document.getElementById(tab.htmlFor);
    if (!input || input.type !== 'radio') continue;
    tab.click();
    if (shown()) return measure();
  }
  return null;
}""" % (SCATTER_SHOWN, LABEL_JS)


def colour_findings(page, base: str) -> list[str]:
    out = []
    for kind, pages in (("team", TEAM), ("match", MATCH)):
        page.set_viewport_size({"width": 1010, "height": 900})
        page.goto(base + pages["en"], wait_until="load")
        for theme in ("dark", "light"):
            page.evaluate(THEME_JS, theme)
            out += ["%s · %s" % (pages["en"], f) for f in page.evaluate(COLOUR_JS, [[list(m) for m in MARKS[kind]]])]
    return out


def screenshots(page, base: str) -> tuple[dict[str, bytes], list[str]]:
    shots, missing = {}, []
    for name, pages, sel, n in CHARTS:
        for vw in VIEWPORTS:
            for lang, theme in STATES:
                page.set_viewport_size({"width": vw, "height": 4000})
                page.goto(base + pages[lang], wait_until="load")
                page.evaluate(THEME_JS, theme)
                if not page.evaluate(REACH_JS, [sel, n]):
                    missing.append("%s · %s · no tab shows it" % (pages[lang], name))
                    continue
                page.evaluate(PAINTED_JS)
                shots["%s-%s-%s-%d.png" % (name, lang, theme, vw)] = page.locator(sel).nth(n).screenshot(animations="disabled")
    return shots, missing


def scatter_pages(dist: Path) -> list[str]:
    """Every built page that draws a scatter plot, found by its markup, not by a list of paths."""
    return sorted(p.parent.relative_to(dist).as_posix() for p in dist.glob("*/*/*/index.html")
                  if 'class="dp-chart' in p.read_text(encoding="utf-8"))


def label_findings(page, base: str, pages: list[str]) -> tuple[list[str], int]:
    """Every (page, width) whose difference label meets something in a reader's flow (a fresh load
    at that width, a click on the tab that shows the scatter plot, the measurement), and how many
    were measured. The script is never run again or injected."""
    out, measured = [], 0
    for path in pages:
        for w in LABEL_WIDTHS:
            page.set_viewport_size({"width": w, "height": 812})
            page.goto(base + path + "/", wait_until="domcontentloaded")
            hits = page.evaluate(READER_JS)
            if hits is None:
                out.append("%s · %dpx · no tab shows a scatter plot" % (path, w))
                continue
            measured += 1
            if hits:
                out.append("%s · %dpx · the difference label meets %s" % (path, w, ", ".join(hits)))
    return out, measured


def manifest_of(shots: dict[str, bytes], platform: str | None = None) -> dict:
    return {"platform": platform or PLATFORM, "shots": {n: hashlib.sha256(b).hexdigest() for n, b in sorted(shots.items())}}


def compare(pinned: dict, now: dict) -> list[str]:
    """Every pin that differs from this run: changed, new, or gone."""
    was, got = pinned.get("shots", {}), now["shots"]
    return ([n + " · changed" for n in sorted(was) if n in got and was[n] != got[n]]
            + [n + " · new" for n in sorted(got) if n not in was]
            + [n + " · gone" for n in sorted(was) if n not in got])


def pin_findings(pins: Path, pinned: dict) -> list[str]:
    """The committed pins must be the screenshots the manifest names: each entry's PNG present with
    that hash, and no PNG the manifest does not name, so a changed look shows as a changed image."""
    shots = pinned.get("shots", {})
    out = []
    for name, digest in sorted(shots.items()):
        png = pins / name
        if not png.is_file():
            out.append(name + " · in the manifest, not in the pins")
        elif hashlib.sha256(png.read_bytes()).hexdigest() != digest:
            out.append(name + " · does not match its hash in the manifest")
    out += [p.name + " · in the pins, not in the manifest" for p in sorted(pins.glob("*.png")) if p.name not in shots]
    return out


def write(folder: Path, shots: dict[str, bytes], manifest: dict) -> None:
    folder.mkdir(parents=True, exist_ok=True)
    for stale in folder.glob("*.png"):
        if stale.name not in shots:
            stale.unlink()
    for name, png in shots.items():
        (folder / name).write_bytes(png)
    (folder / "manifest.json").write_text(json.dumps(manifest, indent=1) + "\n", encoding="utf-8")


def measure(dist: Path) -> tuple[list[str], dict[str, bytes], list[str], list[str], int]:
    """Colour findings, screenshots, charts no tab shows, label findings and label measurements."""
    from playwright.sync_api import sync_playwright

    srv, base = serve(dist)
    try:
        with sync_playwright() as pw:
            # The same text widths as the design check.
            browser = pw.chromium.launch(args=["--font-render-hinting=none"])
            page = browser.new_page(viewport={"width": 1010, "height": 900})
            colours = colour_findings(page, base)
            shots, missing = screenshots(page, base)
            labels, measured = label_findings(page, base, scatter_pages(dist))
            browser.close()
    finally:
        srv.shutdown()
    return colours, shots, missing, labels, measured


def screenshot_verdict(pinned: dict, now: dict, platform: str) -> tuple[list[str], bool]:
    """The screenshot findings and whether the screenshots were compared. Only pins taken on Linux
    are valid, on every platform, so a pin set from another machine can never switch the comparison
    off; a run on another platform compares nothing, since its text renders differently."""
    if pinned and pinned.get("platform") != PIN_PLATFORM:
        return ["manifest.json · taken on %s; pins are taken on %s only" % (pinned.get("platform"), PIN_PLATFORM)], False
    if not platform.startswith(PIN_PLATFORM):
        return [], False
    return (compare(pinned, now) if pinned else ["manifest.json · missing"]), True


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--dist", default=str(DIST), help="the built site")
    ap.add_argument("--pins", default=str(PINS))
    ap.add_argument("--artifacts", help="where the new screenshots go on a difference")
    ap.add_argument("--update", action="store_true", help="rewrite the pins (Linux only)")
    args = ap.parse_args(argv)
    pins = Path(args.pins)
    on_pin_platform = PLATFORM.startswith(PIN_PLATFORM)
    if args.update and not on_pin_platform:
        print("check_chart_screenshots: the pins are taken on Linux only (text renders differently per system); this is %s" % PLATFORM)
        return 2
    colours, shots, missing, labels, measured = measure(Path(args.dist))
    if not measured:
        labels = labels + ["no scatter plot was measured"]
    findings = ["colour · " + f for f in colours] + ["chart · " + f for f in missing] + ["scatter label · " + f for f in labels]
    for f in findings:
        print("FAIL  " + f)
    print("check_chart_screenshots: %d colour finding(s), %d scatter label finding(s) over %d measurements"
          % (len(colours), len(labels), measured))
    now = manifest_of(shots)
    if args.update:
        write(pins, shots, now)
        print("check_chart_screenshots: %d pins written to %s" % (len(shots), pins))
        return 1 if findings else 0
    manifest = pins / "manifest.json"
    pinned = json.loads(manifest.read_text(encoding="utf-8")) if manifest.is_file() else {}
    diffs, compared = screenshot_verdict(pinned, now, PLATFORM)
    diffs = pin_findings(pins, pinned) + diffs
    for d in diffs:
        print("FAIL  screenshot · " + d)
    if not compared and not diffs:
        print("check_chart_screenshots: %d screenshots not compared: the pins are taken on %s, this is %s"
              % (len(shots), PIN_PLATFORM, PLATFORM))
    if diffs and args.artifacts and on_pin_platform:
        write(Path(args.artifacts), shots, now)
        print("check_chart_screenshots: the new screenshots are in %s" % args.artifacts)
    print("check_chart_screenshots: %d screenshot difference(s) over %d screenshots" % (len(diffs), len(shots)))
    return 1 if findings or diffs else 0


if __name__ == "__main__":
    sys.exit(main())
