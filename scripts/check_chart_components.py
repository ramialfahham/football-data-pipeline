"""The chart-component check: a chart component sets no size, colour or font of its own.

A chart component is any `site_v2/src/**/*.astro` file that writes a class of the chart theme's
two families, `chart`/`chart-*` and `cmp`/`cmp-*`; no list names them. In one, every look comes
from the theme in `site_v2/src/styles/system.css` and every layout number from
`site_v2/src/lib/chartTheme.ts`, so the check fails:
- a presentation attribute that sets a look on any element: fill, stroke, stroke-width,
  stroke-dasharray, opacity, color, font-size, font-family, font-weight, r, rx, ry, width, height;
- a `style=` other than one data-driven position, `left:${…}%` or `width:${…}%`;
- a `<style>` block.
It also fails a colour or a pixel size written in `chartTheme.ts`, which holds layout numbers only.

The site has no tooltips, so in every file under `site_v2/src` the check also fails a `title=`
attribute on an HTML or SVG element (a component's own `title` prop is not one), a `<title>`
anywhere but in a page's `<head>`, and a script that sets a title.

Exit 0 clean, 1 with findings (`path:line · tag · what`).
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SITE_SRC = REPO / "site_v2" / "src"
THEME = SITE_SRC / "lib" / "chartTheme.ts"

LOOK_ATTRS = ("fill", "stroke", "stroke-width", "stroke-dasharray", "opacity", "color", "font-size",
              "font-family", "font-weight", "r", "rx", "ry", "width", "height")
_LOOK = re.compile(r"(?<![\w:-])(%s)\s*=" % "|".join(re.escape(a) for a in LOOK_ATTRS))
_STYLE = re.compile(r"(?<![\w:-])style\s*=\s*(\"[^\"]*\"|'[^']*'|\{`[^`]*`\}|\{[^}]*\})")
_POSITION = re.compile(r"^\{`(?:left|width):\$\{[^}]+\}%`\}$")
_STYLE_BLOCK = re.compile(r"<style\b", re.IGNORECASE)
_CLASS_TOKEN = re.compile(r"""["'\s\[]((?:chart|cmp)(?:-[\w-]+)?)["'\s\]]""")
_CLASS_ATTR = re.compile(r"""\bclass(?::list)?\s*=\s*(?:"[^"]*"|'[^']*'|\{)""")
_THEME_LOOK = re.compile(r"#[0-9a-fA-F]{3,8}\b|\brgba?\(|\bhsla?\(|\bvar\(--|\d+(?:\.\d+)?px\b")
_TITLE_ATTR = re.compile(r"(?<![\w:-])title\s*=")
_TITLE_TAG = re.compile(r"<title\b", re.IGNORECASE)
_HEAD = re.compile(r"<head\b.*?</head>", re.IGNORECASE | re.DOTALL)
_TITLE_SET = re.compile(r"""setAttribute\(\s*["']title["']|\.title\s*=(?!=)""")
_SCRIPTS = re.compile(r"<script\b[^>]*>(.*?)</script>", re.IGNORECASE | re.DOTALL)


def _frontmatter_end(text: str) -> int:
    if not text.startswith("---"):
        return 0
    end = text.find("\n---", 3)
    return 0 if end < 0 else end + 4


def tags(text: str):
    """(offset, tag name, attribute text) for every opening tag in an Astro template, `{…}` and
    quoted values skipped when finding the tag's end."""
    i = _frontmatter_end(text)
    while True:
        m = re.compile(r"<([a-zA-Z][\w.-]*)\b").search(text, i)
        if not m:
            return
        quote, depth, j = None, 0, m.end()
        while j < len(text):
            c = text[j]
            if quote:
                if c == quote:
                    quote = None
            elif c in "\"'`":
                quote = c
            elif c == "{":
                depth += 1
            elif c == "}":
                depth -= 1
            elif c == ">" and depth <= 0:
                break
            j += 1
        yield m.start(), m.group(1), text[m.end():j]
        i = j + 1


def is_chart_component(text: str) -> bool:
    body = text[_frontmatter_end(text):]
    for _, _, attrs in tags(body):
        for m in _CLASS_ATTR.finditer(attrs):
            if _CLASS_TOKEN.search(attrs[m.start():m.start() + 400]):
                return True
    return False


def lint_component(path: Path, root: Path = REPO) -> list[str]:
    rel = path.relative_to(root).as_posix()
    text = path.read_text(encoding="utf-8")
    line = lambda at: text.count("\n", 0, at) + 1  # noqa: E731
    out = []
    for m in _STYLE_BLOCK.finditer(text):
        out.append("%s:%d · <style> · a style block" % (rel, line(m.start())))
    for at, tag, attrs in tags(text):
        for a in _LOOK.finditer(attrs):
            out.append("%s:%d · <%s> · %s" % (rel, line(at), tag, a.group(1)))
        for s in _STYLE.finditer(attrs):
            if not _POSITION.match(s.group(1)):
                out.append("%s:%d · <%s> · style=%s" % (rel, line(at), tag, s.group(1)))
    return out


def lint_theme(path: Path = THEME, root: Path = REPO) -> list[str]:
    rel = path.relative_to(root).as_posix()
    out = []
    for n, text in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        code = text.split("//", 1)[0]
        for m in _THEME_LOOK.finditer(code):
            out.append("%s:%d · layout file · %s" % (rel, n, m.group(0)))
    return out


def lint_tooltips(path: Path, root: Path = REPO) -> list[str]:
    rel = path.relative_to(root).as_posix()
    text = path.read_text(encoding="utf-8")
    line = lambda at: text.count("\n", 0, at) + 1  # noqa: E731
    out = []
    if path.suffix == ".astro":
        heads = [m.span() for m in _HEAD.finditer(text)]
        comments = [m.span() for m in re.finditer(r"<!--.*?-->", text, re.DOTALL)]
        for at, tag, attrs in tags(text):
            if tag[0].islower() and _TITLE_ATTR.search(attrs):
                out.append("%s:%d · <%s> · a title attribute, a tooltip" % (rel, line(at), tag))
        for m in _TITLE_TAG.finditer(text, _frontmatter_end(text)):
            if any(a <= m.start() < b for a, b in comments):
                continue
            if not any(a <= m.start() < b for a, b in heads):
                out.append("%s:%d · <title> · outside the page's head, a tooltip" % (rel, line(m.start())))
        code = "".join(m.group(1) for m in _SCRIPTS.finditer(text))
    else:
        code = text
    for m in _TITLE_SET.finditer(code):
        out.append("%s · script · sets a title, a tooltip: %s" % (rel, m.group(0)))
    return out


def run(site_src: Path = SITE_SRC, theme: Path = THEME, root: Path = REPO) -> tuple[list[str], list[str]]:
    components = sorted(p for p in site_src.rglob("*.astro") if is_chart_component(p.read_text(encoding="utf-8")))
    findings = [f for p in components for f in lint_component(p, root)] + lint_theme(theme, root)
    for p in sorted(site_src.rglob("*")):
        if p.suffix in (".astro", ".ts", ".mjs", ".js") and p.is_file():
            findings += lint_tooltips(p, root)
    return findings, [p.relative_to(root).as_posix() for p in components]


def main() -> int:
    findings, components = run()
    for f in findings:
        print(f)
    if findings:
        print("check_chart_components: %d finding(s) in %d chart component(s)" % (len(findings), len(components)))
        return 1
    print("check_chart_components: %d chart component(s) clean: %s" % (len(components), ", ".join(components)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
