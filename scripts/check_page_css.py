"""The page-CSS lint: an inventory element is styled in `system.css` and nowhere else.

Fails on a `<style>` block or a `style=` attribute in `site_v2/src/**/*.astro`, a stylesheet
under `site_v2/src` other than `styles/system.css`, or a CSS-shaped string in the generator of
any mock page the block standard lists (or a module it imports) whose selector, or whose
element, carries a class the block standard's Selector column names — any class, anywhere in
the selector: a page-internal class that happens to share a name with an element's is a
collision to rename, not a case to reason about. The class list and the page list come from
`docs/wireframes/block_standard.md` through `design_inventory.py`; nothing here is hand-listed.
A data-driven bar width on a non-inventory class passes; a mock's harness CSS (toggles, the
stage, the legend) passes because it names no inventory class; a generator the Pages table does
not name (a diagram, a standards sheet) is not a page and is not linted.

Exit 0 clean, 1 with findings (`path:line · where · token`), 2 when the inventory does not parse.
"""

from __future__ import annotations

import argparse
import ast
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
    diagram, a standards sheet) and is not linted."""
    names = {p.source.split()[0] for p in inv.pages if p.kind == "mock" and p.source}
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


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--inventory", default=str(di.DOC))
    args = ap.parse_args(argv)
    try:
        findings, scanned = run(Path(args.inventory))
    except di.InventoryError as exc:
        print("INVENTORY ERROR: %s" % exc, file=sys.stderr)
        return 2
    for f in findings:
        print("FAIL  " + f)
    print("page-css lint: %d files scanned, %d finding(s)" % (scanned, len(findings)))
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
