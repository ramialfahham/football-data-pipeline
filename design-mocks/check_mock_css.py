"""A standalone design mock's styles against main's `system.css`.

A mock carries its own copy of the site's styles. Its "Today" side must be main's styles and
nothing else; what it proposes is scoped under `html.prop`, and that list is what a reviewer reads.

Both style sets are loaded in headless Chromium and read from `document.styleSheets`, so
formatting, comments and shorthand spelling cannot make two equal sets differ. A rule is
(at-rule context + selector, sorted declarations).

- a rule whose every selector is under `html.prop` is Proposed and printed as a numbered list;
- a rule whose every selector names a `.mock-*` class is mock harness and ignored; so is `@font-face`;
- every other rule is Today and must equal main's rule set: a rule main lacks, a main rule
  changed, a main rule missing are each printed and fail.

Usage: python design-mocks/check_mock_css.py <mock.html> [--base <git ref, default gitlab/main>]
Exit 0 when Today equals main, 1 when it does not, 2 when a file or ref cannot be read.
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SYSTEM_CSS = "site_v2/src/styles/system.css"
PROPOSED_SCOPE = re.compile(r"html\.prop(?![\w-])")
MOCK_CLASS = re.compile(r"\.mock-")

READ_RULES = """
() => {
  const out = [];
  const decls = (style) => {
    const d = [];
    for (let i = 0; i < style.length; i++) {
      const n = style[i];
      d.push([n, style.getPropertyValue(n), style.getPropertyPriority(n)]);
    }
    if (d.some((x) => x[1] === '')) {
      const text = style.cssText.split(';').map((s) => s.trim()).filter(Boolean).sort().join('; ');
      d.push(['(as written, shorthand with var())', text, '']);
    }
    return d;
  };
  const walk = (rules, ctx) => {
    for (const r of rules) {
      if (r.type === CSSRule.STYLE_RULE) {
        out.push({ctx, sel: r.selectorText, decls: decls(r.style)});
        if (r.cssRules && r.cssRules.length) walk(r.cssRules, ctx + r.selectorText + ' > ');
      } else if (r.type === CSSRule.KEYFRAMES_RULE) {
        for (const k of r.cssRules) out.push({ctx: ctx + '@keyframes ' + r.name + ' ', sel: k.keyText, decls: decls(k.style)});
      } else if (r.type === CSSRule.FONT_FACE_RULE) {
        continue;
      } else if (r.cssRules) {
        const head = r.cssText.slice(0, r.cssText.indexOf('{')).trim();
        walk(r.cssRules, ctx + head + ' ');
      } else {
        out.push({ctx, sel: r.cssText, decls: []});
      }
    }
  };
  for (const sheet of document.styleSheets) {
    const media = sheet.media.mediaText;
    try { walk(sheet.cssRules, media && media !== 'all' ? '@media ' + media + ' ' : ''); } catch (e) { out.push({ctx: '', sel: '<unreadable sheet>', decls: []}); }
  }
  for (const l of document.querySelectorAll('link[rel~=stylesheet]')) {
    out.push({ctx: '', sel: '<linked stylesheet not read: ' + l.getAttribute('href') + '>', decls: []});
  }
  return out;
}
"""


def _selectors(sel: str) -> list[str]:
    parts, depth, cur = [], 0, ""
    for ch in sel:
        if ch in "([":
            depth += 1
        elif ch in ")]":
            depth -= 1
        if ch == "," and depth == 0:
            parts.append(cur.strip())
            cur = ""
        else:
            cur += ch
    parts.append(cur.strip())
    return parts


def _is_mock(part: str) -> bool:
    flat = re.sub(r"\[[^\]]*\]", "", re.sub(r"\([^()]*\)", "", part))
    last = re.split(r"[\s>+~]+", flat.strip())[-1]
    return bool(MOCK_CLASS.search(last))


def classify(sel: str) -> str:
    parts = _selectors(sel)
    if all(_is_mock(p) for p in parts):
        return "mock"
    if all(PROPOSED_SCOPE.match(p) for p in parts):
        return "proposed"
    return "today"


def read_rules(html: str) -> list[dict]:
    from playwright.sync_api import sync_playwright

    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        try:
            page = browser.new_context().new_page()
            page.route("**/*", lambda route: route.abort() if route.request.url.startswith("http") else route.continue_())
            page.set_content(html, wait_until="domcontentloaded")
            return page.evaluate(READ_RULES)
        finally:
            browser.close()


def main_css(ref: str) -> str:
    out = subprocess.run(["git", "show", f"{ref}:{SYSTEM_CSS}"], cwd=REPO, capture_output=True, text=True, encoding="utf-8")
    if out.returncode != 0:
        raise RuntimeError(f"cannot read {SYSTEM_CSS} at {ref}: {out.stderr.strip()}")
    return out.stdout


def _key(rule: dict) -> tuple[str, str]:
    return rule["ctx"], rule["sel"]


def _decls(rule: dict) -> tuple:
    return tuple(sorted((n, v, i) for n, v, i in rule["decls"]))


def _fmt(decls: tuple | None) -> str:
    if decls is None:
        return "(absent)"
    return "; ".join(f"{n}: {v}{' !important' if i else ''}" for n, v, i in decls)


def _bucket(rules: list[dict]) -> dict[tuple[str, str], list[tuple]]:
    b: dict[tuple[str, str], list[tuple]] = {}
    for r in rules:
        b.setdefault(_key(r), []).append(_decls(r))
    return b


def compare(base_rules: list[dict], mock_rules: list[dict]) -> tuple[list[str], list[tuple[str, str]]]:
    """Return (Today differences as printable blocks, Proposed rules as (selector, declarations))."""
    base_today = [r for r in base_rules if classify(r["sel"]) == "today"]
    mock_today = [r for r in mock_rules if classify(r["sel"]) == "today"]
    base, today = _bucket(base_today), _bucket(mock_today)
    proposed = [
        (f"{r['ctx']}{r['sel']}", _fmt(_decls(r)))
        for r in mock_rules if classify(r["sel"]) == "proposed"
    ]
    diffs: list[str] = []
    for key in sorted(set(base) | set(today)):
        b, m = base.get(key, set()), today.get(key, set())
        if b == m:
            continue
        kind = "new in mock" if not b else "missing from mock" if not m else "changed"
        diffs.append(
            f"{kind}: {key[0]}{key[1]}\n"
            f"    main: {' | '.join(_fmt(d) for d in b) or '(absent)'}\n"
            f"    mock: {' | '.join(_fmt(d) for d in m) or '(absent)'}"
        )
    if not diffs and [_key(r) for r in base_today] != [_key(r) for r in mock_today]:
        diffs.append("rule order differs from main: the same rules, in another order, cascade differently")
    return diffs, proposed


def check(mock_html: str, base_css: str) -> tuple[list[str], list[tuple[str, str]]]:
    return compare(read_rules(f"<style>{base_css}</style>"), read_rules(mock_html))


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("mock", type=Path)
    ap.add_argument("--base", default="gitlab/main")
    args = ap.parse_args(argv)
    sys.stdout.reconfigure(encoding="utf-8")
    try:
        html = args.mock.read_text(encoding="utf-8")
        css = main_css(args.base)
    except (OSError, RuntimeError, ValueError) as e:
        print(f"ERROR: {e}")
        return 2
    try:
        diffs, proposed = check(html, css)
    except Exception as e:
        print(f"ERROR: the browser could not read the styles: {e}")
        return 2
    print(f"Today differences from {args.base}: {len(diffs)}")
    for d in diffs:
        print(f"  {d}")
    print(f"Proposed rules (html.prop): {len(proposed)}")
    for n, (sel, decl) in enumerate(proposed, 1):
        print(f"  {n}. {sel} {{ {decl} }}")
    return 1 if diffs else 0


if __name__ == "__main__":
    sys.exit(main())
