"""The page-CSS lint: an inventory element is styled in `system.css` and nowhere else.

Fails on a `<style>` block or a `style=` attribute in `site_v2/src/**/*.astro`, a stylesheet
under `site_v2/src` other than `styles/system.css`, or a CSS-shaped string in the generator of
any mock page the block standard lists (or a module it imports) whose selector, or whose
element, carries a class the block standard's Selector column names — any class, anywhere in
the selector: a page-internal class that happens to share a name with an element's is a
collision to rename, not a case to reason about. The class list and the page list come from
`docs/wireframes/block_standard.md` through `design_inventory.py`; nothing here is hand-listed.
A data-driven bar width on a non-inventory class passes; a mock's harness CSS (toggles, the
stage, the legend) passes because it names no inventory class.

It also counts five gaps, each pinned in the baseline (`design_inventory.BASELINE`, `static`):
- `mock_css`: the same findings in every other `gen_*.py` generator and the modules it imports,
  per file (a generator the Pages table does not name is not a page, so it is counted, not failed);
- `css_outside_system_css`: a `<style>` block or a `style=` attribute in an `.astro` file, another
  stylesheet, or a style write in a site script, per file;
- `width_rules`: `@media` and `@container` rules per width they name, so a new width is a new key;
- `banned_properties`: declarations that split a word or cut text off, per file;
- `literal_text`: text written into a component or page template instead of the strings, per file.
A count that differs from its pin fails, in both directions.

Exit 0 clean, 1 with findings (`path:line · where · token`) or a count off its pin, 2 when the
inventory does not parse.
"""

from __future__ import annotations

import argparse
import ast
import html
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import design_inventory as di  # noqa: E402

REPO = di.REPO
SITE_SRC = REPO / "site_v2" / "src"
SYSTEM_CSS = SITE_SRC / "styles" / "system.css"
MOCKS = REPO / "design-mocks"

_STYLE_BLOCK = re.compile(r"<style\b[^>]*>(.*?)</style>", re.DOTALL | re.IGNORECASE)
_TAG = re.compile(r"<([a-zA-Z][\w-]*)\b([^>]*)>", re.DOTALL)
_STYLE_ATTR = re.compile(r"\bstyle\s*=", re.IGNORECASE)
_CLASS_ATTR = re.compile(r"""\bclass(?::list)?\s*=\s*(?:"([^"]*)"|'([^']*)'|\{([^}]*)\})""", re.DOTALL)
_CLASS = re.compile(r"\.([A-Za-z_][\w-]*)")
_RULE_SHAPE = re.compile(r"[^{}]+\{[^{}]*:[^{}]*\}")
_COMMENT = re.compile(r"/\*.*?\*/", re.DOTALL)


def selectors_in(css: str):
    """(selector text, line offset) for every rule in a stylesheet, at-rule blocks unwrapped."""
    css = _COMMENT.sub(lambda m: " " * len(m.group(0)), css)
    depth_stack: list[str] = []
    buf = ""
    line = 1
    start_line = 1
    i = 0
    while i < len(css):
        c = css[i]
        if c == "\n":
            line += 1
        if c == "{":
            head = buf.strip()
            if head.startswith("@"):
                depth_stack.append("@")
            else:
                depth_stack.append("rule")
                if head:
                    yield head, start_line
            buf = ""
            start_line = line
        elif c == "}":
            if depth_stack:
                depth_stack.pop()
            buf = ""
            start_line = line
        elif c == ";" and (not depth_stack or depth_stack[-1] == "@"):
            buf = ""
            start_line = line
        else:
            if not buf.strip():
                start_line = line
            buf += c
        i += 1


def guarded_tokens(selector: str, tokens: frozenset[str]) -> list[str]:
    return sorted(set(_CLASS.findall(selector)) & tokens)


def lint_astro(path: Path, tokens: frozenset[str], root: Path = REPO) -> list[str]:
    text = path.read_text(encoding="utf-8")
    rel = path.relative_to(root).as_posix()
    out: list[str] = []
    for m in _STYLE_BLOCK.finditer(text):
        base = text.count("\n", 0, m.start(1))
        for sel, off in selectors_in(m.group(1)):
            hit = guarded_tokens(sel, tokens)
            if hit:
                out.append("%s:%d · <style> rule `%s` · %s" % (rel, base + off, sel, ", ".join(hit)))
    for m in _TAG.finditer(text):
        attrs = m.group(2)
        if not _STYLE_ATTR.search(attrs):
            continue
        cm = _CLASS_ATTR.search(attrs)
        classes = set()
        if cm:
            raw = next(g for g in cm.groups() if g is not None)
            classes = set(re.findall(r"[A-Za-z_][\w-]*", raw))
        hit = sorted(classes & tokens)
        if hit:
            out.append("%s:%d · style= on <%s> · %s" % (rel, text.count("\n", 0, m.start()) + 1, m.group(1), ", ".join(hit)))
    return out


def lint_css_file(path: Path, tokens: frozenset[str], root: Path = REPO) -> list[str]:
    rel = path.relative_to(root).as_posix()
    out = []
    for sel, line in selectors_in(path.read_text(encoding="utf-8")):
        hit = guarded_tokens(sel, tokens)
        if hit:
            out.append("%s:%d · stylesheet rule `%s` · %s" % (rel, line, sel, ", ".join(hit)))
    return out


def mock_modules(inv: di.Inventory, mocks: Path = MOCKS) -> list[Path]:
    """The generator behind every mock page in the inventory and, transitively, every sibling
    module one of them imports. A generator the Pages table does not name is not a page (a
    diagram, a standards sheet): its findings are counted, not failed."""
    return _with_imports({p.source.split()[0] for p in inv.pages if p.kind == "mock" and p.source}, mocks)


def unlisted_mock_modules(inv: di.Inventory, mocks: Path = MOCKS) -> list[Path]:
    """Every other `gen_*.py` generator and the modules it imports, minus the page modules."""
    listed = {p.name for p in mock_modules(inv, mocks)}
    return [p for p in _with_imports({p.name for p in mocks.glob("gen_*.py")}, mocks) if p.name not in listed]


def _with_imports(names: set[str], mocks: Path) -> list[Path]:
    todo = [mocks / n for n in sorted(names)]
    seen: dict[str, Path] = {}
    while todo:
        p = todo.pop()
        if p.name in seen or not p.is_file():
            continue
        seen[p.name] = p
        try:
            tree = ast.parse(p.read_text(encoding="utf-8"))
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            names = []
            if isinstance(node, ast.Import):
                names = [a.name for a in node.names]
            elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
                names = [node.module]
            for n in names:
                sib = mocks / (n.split(".")[0] + ".py")
                if sib.is_file() and sib.name not in seen:
                    todo.append(sib)
    return [seen[k] for k in sorted(seen)]


def lint_mock(path: Path, tokens: frozenset[str], root: Path = REPO) -> list[str]:
    rel = path.relative_to(root).as_posix()
    out = []
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except SyntaxError as exc:
        return ["%s:%d · does not parse · %s" % (rel, exc.lineno or 0, exc.msg)]
    for node in ast.walk(tree):
        if not (isinstance(node, ast.Constant) and isinstance(node.value, str)):
            continue
        if not _RULE_SHAPE.search(node.value):
            continue
        for sel, off in selectors_in(node.value):
            hit = guarded_tokens(sel, tokens)
            if hit:
                out.append("%s:%d · CSS string rule `%s` · %s" % (rel, node.lineno + off - 1, sel, ", ".join(hit)))
    return out


def run(inventory: Path, site_src: Path = SITE_SRC, mocks: Path = MOCKS) -> tuple[list[str], int]:
    inv = di.load(inventory)
    root = site_src.parent.parent
    tokens = di.class_tokens(inv.elements)
    findings: list[str] = []
    scanned = 0
    for p in sorted(site_src.rglob("*.astro")):
        scanned += 1
        findings += lint_astro(p, tokens, root)
    for p in sorted(site_src.rglob("*.css")):
        if p.resolve() == (site_src / "styles" / "system.css").resolve():
            continue
        scanned += 1
        findings += lint_css_file(p, tokens, root)
    if mocks.is_dir():
        for p in mock_modules(inv, mocks):
            scanned += 1
            findings += lint_mock(p, tokens, root)
    return findings, scanned


_STYLE_OPEN = re.compile(r"<style\b", re.IGNORECASE)
_STYLE_WRITE = re.compile(r"""\.style(?:\.[A-Za-z]\w*|\[[^\]]*\])?\s*=(?!=)|\.style\.setProperty\(|setAttribute\(\s*["']style["']""")
_BANNED = re.compile(
    r"(?<![\w-])(?:(?:-webkit-)?hyphens\s*:\s*auto|overflow-wrap\s*:\s*(?:anywhere|break-word)"
    r"|word-wrap\s*:\s*break-word|word-break\s*:\s*(?:break-all|break-word)"
    r"|text-overflow\s*:\s*ellipsis|(?:-webkit-)?line-clamp\s*:)", re.IGNORECASE)
_WIDTH_RULE = re.compile(r"@(?:media|container)\b([^{;]*)\{")
_WIDTH = re.compile(r"\b(?:min-|max-)?width\s*(?::|[<>]=?)\s*(\d+(?:\.\d+)?(?:px|em|rem))")
_VOID = frozenset("area base br col embed hr img input link meta source track wbr".split())
_VISIBLE_ATTR = re.compile(r"""(?<![\w:-])(?:placeholder|title|alt)\s*=\s*(?:"([^"]*)"|'([^']*)')""")
_LETTER = re.compile(r"[^\W_]")
_BLANKED = re.compile(r"<!--.*?-->|<(script|style)\b.*?</\1\s*>", re.DOTALL | re.IGNORECASE)


def _blank(text: str) -> str:
    return re.sub(r"[^\n]", " ", text)


def _tag_end(s: str, i: int) -> int:
    """Just past the `>` closing the tag that opens at `s[i]`, skipping quoted values and `{…}`."""
    quote, depth, j = None, 0, i + 1
    while j < len(s):
        c = s[j]
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
            return j + 1
        j += 1
    return len(s)


def _opens_element(tag: str) -> bool:
    m = re.match(r"<([A-Za-z][\w.:-]*)", tag)
    return tag == "<>" or bool(m and not tag.endswith("/>") and m.group(1).lower() not in _VOID)


def literal_text(text: str) -> list[tuple[int, str]]:
    """Every literal text in an Astro template: a run of text between tags (inside an expression's
    markup too) and the literal value of a visible attribute, when it holds a letter or a digit.
    The frontmatter, comments, scripts, styles and code inside `{…}` are not template text."""
    start = 0
    if text.startswith("---"):
        end = text.find("\n---", 3)
        start = end + 4 if end != -1 else 0
    s = _blank(text[:start]) + _BLANKED.sub(lambda m: _blank(m.group(0)), text[start:])
    out: list[tuple[int, str]] = []
    run_at: int | None = None

    def keep(at: int, raw: str) -> None:
        value = " ".join(html.unescape(raw).split())
        if _LETTER.search(value):
            out.append((s.count("\n", 0, at) + 1, value))

    def tag_at(i: int) -> int:
        j = _tag_end(s, i)
        for m in _VISIBLE_ATTR.finditer(s, i, j):
            keep(m.start(), m.group(1) if m.group(1) is not None else m.group(2))
        return j

    stack = ["markup"]
    i, n = 0, len(s)
    while i < n:
        c, nxt = s[i], s[i + 1:i + 2]
        if stack[-1] == "markup":
            if c == "{" or (c == "<" and (nxt.isalpha() or nxt in ("/", "!", ">"))):
                if run_at is not None:
                    keep(run_at, s[run_at:i])
                    run_at = None
                if c == "{":
                    stack.append("code")
                    i += 1
                    continue
                j = tag_at(i)
                if nxt == "/":
                    if len(stack) > 1:
                        stack.pop()
                elif _opens_element(s[i:j]):
                    stack.append("markup")
                i = j
                continue
            if run_at is None and not c.isspace():
                run_at = i
            i += 1
            continue
        if c in "\"'`":
            j = i + 1
            while j < n and s[j] != c:
                j += 2 if s[j] == "\\" else 1
            i = j + 1
            continue
        if s.startswith("//", i):
            i = s.find("\n", i) if "\n" in s[i:] else n
            continue
        if s.startswith("/*", i):
            j = s.find("*/", i + 2)
            i = n if j == -1 else j + 2
            continue
        if c == "{":
            stack.append("code")
        elif c == "}":
            if len(stack) > 1:
                stack.pop()
        elif c == "<" and (nxt.isalpha() or nxt == ">"):
            j = tag_at(i)
            if _opens_element(s[i:j]):
                stack.append("markup")
            i = j
            continue
        i += 1
    if run_at is not None:
        keep(run_at, s[run_at:])
    return out


def _stylesheets(site_src: Path, root: Path):
    """(path, CSS) for every stylesheet under the site's source and every `<style>` block."""
    for p in sorted(site_src.rglob("*.css")):
        yield p.relative_to(root).as_posix(), _COMMENT.sub(" ", p.read_text(encoding="utf-8"))
    for p in sorted(site_src.rglob("*.astro")):
        for m in _STYLE_BLOCK.finditer(p.read_text(encoding="utf-8")):
            yield p.relative_to(root).as_posix(), _COMMENT.sub(" ", m.group(1))


def counts(inventory: Path, site_src: Path = SITE_SRC, mocks: Path = MOCKS) -> dict[str, dict[str, int]]:
    """The five static gap counts, each by file (or, for width rules, by width)."""
    inv = di.load(inventory)
    root = site_src.parent.parent
    system_css = (site_src / "styles" / "system.css").resolve()
    tokens = di.class_tokens(inv.elements)
    out: dict[str, dict[str, int]] = {k: {} for k in (
        "mock_css", "css_outside_system_css", "width_rules", "banned_properties", "literal_text")}

    def add(group: str, key: str, n: int) -> None:
        if n:
            out[group][key] = out[group].get(key, 0) + n

    if mocks.is_dir():
        for p in unlisted_mock_modules(inv, mocks):
            add("mock_css", p.relative_to(root).as_posix(), len(lint_mock(p, tokens, root)))
    for p in sorted(site_src.rglob("*")):
        if not p.is_file():
            continue
        rel = p.relative_to(root).as_posix()
        if p.suffix == ".astro":
            text = p.read_text(encoding="utf-8")
            add("css_outside_system_css", rel, len(_STYLE_OPEN.findall(text)))
            add("css_outside_system_css", rel, sum(len(_STYLE_ATTR.findall(m.group(2))) for m in _TAG.finditer(text)))
            add("css_outside_system_css", rel, len(_STYLE_WRITE.findall(text)))
            add("literal_text", rel, len(literal_text(text)))
        elif p.suffix in (".css", ".scss", ".sass", ".less") and p.resolve() != system_css:
            add("css_outside_system_css", rel, 1)
        elif p.suffix in (".ts", ".mjs", ".js") and ".test." not in p.name:
            add("css_outside_system_css", rel, len(_STYLE_WRITE.findall(p.read_text(encoding="utf-8"))))
    for rel, css in _stylesheets(site_src, root):
        add("banned_properties", rel, len(_BANNED.findall(css)))
        for m in _WIDTH_RULE.finditer(css):
            for width in sorted(set(_WIDTH.findall(m.group(1)))):
                add("width_rules", width, 1)
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--inventory", default=str(di.DOC))
    ap.add_argument("--baseline", default=str(di.BASELINE))
    args = ap.parse_args(argv)
    try:
        findings, scanned = run(Path(args.inventory))
        measured = counts(Path(args.inventory))
    except di.InventoryError as exc:
        print("INVENTORY ERROR: %s" % exc, file=sys.stderr)
        return 2
    for f in findings:
        print("FAIL  " + f)
    off = di.compare_counts(measured, di.load_baseline(Path(args.baseline))["static"])
    for line in off:
        print("FAIL  " + line)
    for group, by_key in measured.items():
        print("count %s: %d (%s)" % (group, sum(by_key.values()), ", ".join("%s %d" % kv for kv in sorted(by_key.items())) or "none"))
    print("page-css lint: %d files scanned, %d finding(s), %d count(s) off the baseline" % (scanned, len(findings), len(off)))
    return 1 if findings or off else 0


if __name__ == "__main__":
    sys.exit(main())
