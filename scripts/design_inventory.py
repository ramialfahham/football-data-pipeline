"""The element inventory, read from `docs/wireframes/block_standard.md`.

The document is the design chain's block standard: one table of the site's elements (each with
its selector, its rule, how it is measured, its status and where it was ruled) and one table of
the pages the measured check renders. This module parses both, so the lint
(`check_page_css.py`) and the measured check (`check_design_inventory.py`) read the same rows a
person reads, and nothing else.

The "Measured as" column is a small notation, `;`-separated, one assertion each:

    <prop>=<value>           computed style of every visible match (prop from PROPS)
    gap(next)=<px>           this box's bottom to the next sibling's first line: its box top plus
                             every padding and border down to its first text or image
    gap(prev)=<px>           the previous sibling's box bottom to this element's box top
    left-edge=section        the border box starts where the closest section starts
    stripe=<colour> from <n> rows of the parent table: row n, n+2, ... tinted, the rest transparent
    tracks=head              the row's grid tracks equal its table head's
    hover(<prop>)=<value>    the computed prop while the pointer rests on the first visible match
    press(<prop>)=<value>    the computed prop while the mouse button is down on it
    fits                     scrollWidth <= clientWidth
    one-line                 the element's text lays out on one line
    visible=<n>              exactly n matches are laid out
    min-box=<px>             width and height at least px

A colour is `transparent`, a token name (`ink`, `accent`, ...) read from the page's `.fx`
element, or `<token>@<pct>` for that token at an alpha. The parser fails closed: an unknown
key, property, token, status or column header is an error, never a silently empty inventory.
Stdlib only, so the lint runs where no browser is installed.
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
DOC = REPO / "docs" / "wireframes" / "block_standard.md"

ELEMENT_COLUMNS = ("Element", "Selector", "Rule", "Measured as", "Status", "Ruled on")
PAGE_COLUMNS = ("Page", "Kind", "Source", "URL", "FI", "Expect")
STATUSES = ("ruled", "proposed")
KINDS = ("built", "mock")
FI_MODES = ("path", "toggle", "none")
PROPS = (
    "font-size", "font-weight", "text-transform", "letter-spacing", "line-height", "white-space",
    "text-decoration-line", "color", "background-color", "border-bottom-width", "margin-top",
)
TOKENS = ("page", "surface", "sunk", "line", "div", "ink", "ink-2", "muted", "accent",
          "win", "draw", "loss", "pill-ink", "track")
PX_KINDS = ("gap(next)", "gap(prev)", "min-box")
FLAG_KINDS = ("fits", "one-line", "left-edge", "tracks")


class InventoryError(ValueError):
    """The document does not parse; the row and the token are named."""


@dataclass(frozen=True)
class Assertion:
    kind: str            # a PROPS name, or one of the keys above
    prop: str | None     # for hover()/press(): the property measured
    expected: str        # the right-hand side as written
    raw: str


@dataclass(frozen=True)
class Element:
    name: str
    selector: str
    rule: str
    assertions: tuple[Assertion, ...]
    status: str
    ruled_on: str


@dataclass(frozen=True)
class Page:
    name: str
    kind: str
    source: str
    url: str
    fi: str
    expect: tuple[str, ...]


@dataclass(frozen=True)
class Inventory:
    elements: tuple[Element, ...]
    pages: tuple[Page, ...]

    def element(self, name: str) -> Element:
        for e in self.elements:
            if e.name == name:
                return e
        raise KeyError(name)


_COLOUR = re.compile(r"^(transparent|(?P<tok>[a-z][a-z0-9-]*)(@(?P<pct>\d{1,3})%)?)$")
_PX = re.compile(r"^-?\d+(\.\d+)?px$")
_STRIPE = re.compile(r"^(?P<colour>\S+) from (?P<n>\d+)$")
_CALL = re.compile(r"^(?P<fn>hover|press)\((?P<prop>[a-z-]+)\)$")


def _check_value(kind: str, prop: str, value: str, where: str) -> None:
    if prop in ("color", "background-color"):
        m = _COLOUR.match(value)
        if not m or (m.group("tok") and m.group("tok") not in TOKENS):
            raise InventoryError("%s: %s expects a colour (transparent, a token, token@pct), got %r" % (where, kind, value))
    elif prop in ("font-size", "letter-spacing", "border-bottom-width", "margin-top"):
        if not _PX.match(value):
            raise InventoryError("%s: %s expects a px value, got %r" % (where, kind, value))
    elif prop == "font-weight":
        if not value.isdigit():
            raise InventoryError("%s: font-weight expects a number, got %r" % (where, value))
    elif prop == "text-transform":
        if value not in ("uppercase", "none", "capitalize"):
            raise InventoryError("%s: text-transform expects uppercase/none/capitalize, got %r" % (where, value))
    elif prop == "white-space":
        if value not in ("normal", "nowrap"):
            raise InventoryError("%s: white-space expects normal/nowrap, got %r" % (where, value))
    elif prop == "text-decoration-line":
        if value not in ("none", "underline"):
            raise InventoryError("%s: text-decoration-line expects none/underline, got %r" % (where, value))
    elif prop == "line-height":
        if not (_PX.match(value) or value == "normal"):
            raise InventoryError("%s: line-height expects px or normal, got %r" % (where, value))


def parse_measured(text: str, where: str = "row") -> tuple[Assertion, ...]:
    out: list[Assertion] = []
    for raw in (part.strip() for part in text.strip().strip("`").split(";")):
        if not raw:
            continue
        if raw in FLAG_KINDS:
            if raw in ("left-edge", "tracks"):
                raise InventoryError("%s: %r needs a value (left-edge=section, tracks=head)" % (where, raw))
            out.append(Assertion(raw, None, "", raw))
            continue
        if "=" not in raw:
            raise InventoryError("%s: cannot read %r" % (where, raw))
        key, value = (s.strip() for s in raw.split("=", 1))
        if key == "left-edge":
            if value != "section":
                raise InventoryError("%s: left-edge expects 'section', got %r" % (where, value))
        elif key == "tracks":
            if value != "head":
                raise InventoryError("%s: tracks expects 'head', got %r" % (where, value))
        elif key in PX_KINDS:
            if not _PX.match(value):
                raise InventoryError("%s: %s expects a px value, got %r" % (where, key, value))
        elif key == "visible":
            if not value.isdigit():
                raise InventoryError("%s: visible expects a count, got %r" % (where, value))
        elif key == "stripe":
            m = _STRIPE.match(value)
            if not m:
                raise InventoryError("%s: stripe expects '<colour> from <n>', got %r" % (where, value))
            _check_value("stripe", "background-color", m.group("colour"), where)
        elif _CALL.match(key):
            m = _CALL.match(key)
            prop = m.group("prop")
            if prop not in PROPS:
                raise InventoryError("%s: %s() measures an unknown property %r" % (where, m.group("fn"), prop))
            _check_value(key, prop, value, where)
            out.append(Assertion(m.group("fn"), prop, value, raw))
            continue
        elif key in PROPS:
            _check_value(key, key, value, where)
        else:
            raise InventoryError("%s: unknown key %r" % (where, key))
        out.append(Assertion(key, None, value, raw))
    return tuple(out)


def _tables(text: str) -> dict[str, list[list[str]]]:
    """Every markdown table under a `## heading`, keyed by the heading, as rows of cells."""
    out: dict[str, list[list[str]]] = {}
    heading = None
    for line in text.splitlines():
        if line.startswith("## "):
            heading = line[3:].strip()
            continue
        if heading is None or not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if all(re.fullmatch(r":?-{3,}:?", c) for c in cells):
            continue
        out.setdefault(heading, []).append(cells)
    return out


def _strip_code(cell: str) -> str:
    return cell.strip().strip("`").strip()


def load(path: Path = DOC) -> Inventory:
    text = Path(path).read_text(encoding="utf-8")
    tables = _tables(text)
    if "Elements" not in tables or "Pages" not in tables:
        raise InventoryError("%s: needs a '## Elements' table and a '## Pages' table" % path)
    rows = tables["Elements"]
    if tuple(rows[0]) != ELEMENT_COLUMNS:
        raise InventoryError("Elements: columns must be %s, got %s" % (" · ".join(ELEMENT_COLUMNS), " · ".join(rows[0])))
    elements: list[Element] = []
    for cells in rows[1:]:
        if len(cells) != len(ELEMENT_COLUMNS):
            raise InventoryError("Elements: row %r has %d cells, expected %d" % (cells[0], len(cells), len(ELEMENT_COLUMNS)))
        name, selector, rule, measured, status, ruled_on = cells
        selector = _strip_code(selector)
        if not name or not selector:
            raise InventoryError("Elements: a row without a name or a selector: %r" % cells)
        if status not in STATUSES:
            raise InventoryError("Elements: %s: status must be one of %s, got %r" % (name, "/".join(STATUSES), status))
        if any(e.name == name for e in elements):
            raise InventoryError("Elements: %s listed twice" % name)
        elements.append(Element(name, selector, rule, parse_measured(measured, "Elements: " + name), status, ruled_on))
    if not elements:
        raise InventoryError("Elements: no rows")
    rows = tables["Pages"]
    if tuple(rows[0]) != PAGE_COLUMNS:
        raise InventoryError("Pages: columns must be %s, got %s" % (" · ".join(PAGE_COLUMNS), " · ".join(rows[0])))
    pages: list[Page] = []
    names = {e.name for e in elements}
    for cells in rows[1:]:
        if len(cells) != len(PAGE_COLUMNS):
            raise InventoryError("Pages: row %r has %d cells, expected %d" % (cells[0], len(cells), len(PAGE_COLUMNS)))
        name, kind, source, url, fi, expect = cells
        if kind not in KINDS:
            raise InventoryError("Pages: %s: kind must be built or mock, got %r" % (name, kind))
        if fi not in FI_MODES:
            raise InventoryError("Pages: %s: FI must be path, toggle or none, got %r" % (name, fi))
        expected = tuple(s.strip() for s in expect.split(",") if s.strip())
        unknown = [s for s in expected if s not in names]
        if unknown:
            raise InventoryError("Pages: %s expects elements the inventory does not name: %s" % (name, ", ".join(unknown)))
        if any(p.name == name for p in pages):
            raise InventoryError("Pages: %s listed twice" % name)
        pages.append(Page(name, kind, _strip_code(source), _strip_code(url), fi, expected))
    if not pages:
        raise InventoryError("Pages: no rows")
    return Inventory(tuple(elements), tuple(pages))


_CLASS = re.compile(r"\.([A-Za-z_][\w-]*)")


def class_tokens(elements: tuple[Element, ...]) -> frozenset[str]:
    """Every class name any inventory selector uses — the lint's guarded set."""
    out: set[str] = set()
    for e in elements:
        out.update(_CLASS.findall(e.selector))
    return frozenset(out)


def parse_css_color(s: str) -> tuple[float, float, float, float]:
    """A computed colour as (r, g, b, a) on 0–255 / 0–1: rgb(), rgba(), color(srgb …), #hex."""
    s = s.strip()
    m = re.match(r"^rgba?\(\s*([\d.]+)\s*,\s*([\d.]+)\s*,\s*([\d.]+)\s*(?:,\s*([\d.]+)\s*)?\)$", s)
    if m:
        r, g, b = (float(m.group(i)) for i in (1, 2, 3))
        return r, g, b, float(m.group(4)) if m.group(4) is not None else 1.0
    m = re.match(r"^color\(srgb\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)\s*(?:/\s*([\d.]+)\s*)?\)$", s)
    if m:
        r, g, b = (float(m.group(i)) * 255 for i in (1, 2, 3))
        return r, g, b, float(m.group(4)) if m.group(4) is not None else 1.0
    m = re.match(r"^#([0-9a-fA-F]{6})$", s)
    if m:
        h = m.group(1)
        return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), 1.0
    m = re.match(r"^#([0-9a-fA-F]{3})$", s)
    if m:
        h = m.group(1)
        return int(h[0] * 2, 16), int(h[1] * 2, 16), int(h[2] * 2, 16), 1.0
    if s == "transparent":
        return 0.0, 0.0, 0.0, 0.0
    raise ValueError("not a colour: %r" % s)


def expected_color(expr: str, tokens: dict[str, str]) -> tuple[float, float, float, float]:
    """`transparent`, `ink`, `ink@11%` → (r, g, b, a), from the page's token values."""
    m = _COLOUR.match(expr)
    if not m:
        raise ValueError("not a colour expression: %r" % expr)
    if expr == "transparent":
        return 0.0, 0.0, 0.0, 0.0
    tok = m.group("tok")
    if tok not in tokens:
        raise ValueError("token %r not on the page" % tok)
    r, g, b, _a = parse_css_color(tokens[tok])
    alpha = int(m.group("pct")) / 100 if m.group("pct") else 1.0
    return r, g, b, alpha


def colours_match(expected: tuple, measured: tuple) -> bool:
    er, eg, eb, ea = expected
    mr, mg, mb, ma = measured
    if ea == 0 and ma == 0:
        return True
    return abs(ea - ma) <= 0.005 and all(abs(x - y) <= 1.0 for x, y in ((er, mr), (eg, mg), (eb, mb)))


def compare(a: Assertion, measured, tokens: dict[str, str]) -> str | None:
    """None when the measurement satisfies the assertion, else 'expected … · measured …'."""
    kind = a.kind
    prop = a.prop or kind
    if kind in ("hover", "press") or kind in PROPS:
        if prop in ("color", "background-color"):
            try:
                ok = colours_match(expected_color(a.expected, tokens), parse_css_color(str(measured)))
            except ValueError as exc:
                return "expected %s · measured %s (%s)" % (a.raw, measured, exc)
            return None if ok else "expected %s · measured %s" % (a.raw, measured)
        if prop in ("font-size", "letter-spacing", "border-bottom-width", "margin-top", "line-height"):
            if a.expected == "normal" or not _PX.match(str(measured)):
                return None if str(measured) == a.expected else "expected %s · measured %s" % (a.raw, measured)
            return None if abs(float(str(measured)[:-2]) - float(a.expected[:-2])) <= 0.5 else "expected %s · measured %s" % (a.raw, measured)
        return None if str(measured) == a.expected else "expected %s · measured %s" % (a.raw, measured)
    if kind in ("gap(next)", "gap(prev)"):
        if measured is None:
            return "expected %s · measured nothing (no sibling with a content line)" % a.raw
        return None if abs(float(measured) - float(a.expected[:-2])) <= 1.0 else "expected %s · measured %.1fpx" % (a.raw, float(measured))
    if kind == "left-edge":
        if measured is None:
            return "expected %s · measured no enclosing section" % a.raw
        return None if abs(float(measured)) <= 0.5 else "expected %s · measured %.1fpx off the section's left" % (a.raw, float(measured))
    if kind == "tracks":
        head, row = measured
        return None if head == row else "expected %s · measured head %s vs row %s" % (a.raw, head, row)
    if kind == "stripe":
        m = _STRIPE.match(a.expected)
        colour, start = m.group("colour"), int(m.group("n"))
        want = expected_color(colour, tokens)
        for i, bg in enumerate(measured, start=1):
            try:
                got = parse_css_color(str(bg))
            except ValueError:
                return "expected %s · row %d measured %s" % (a.raw, i, bg)
            tinted = (i - start) % 2 == 0 and i >= start
            if tinted and not colours_match(want, got):
                return "expected %s · row %d measured %s, expected the tint" % (a.raw, i, bg)
            if not tinted and got[3] != 0:
                return "expected %s · row %d measured %s, expected plain" % (a.raw, i, bg)
        return None
    if kind == "fits":
        sw, cw = measured
        return None if sw <= cw else "expected fits · measured scrollWidth %d > clientWidth %d" % (sw, cw)
    if kind == "one-line":
        return None if measured == 1 else "expected one-line · measured %d lines" % measured
    if kind == "visible":
        return None if int(measured) == int(a.expected) else "expected %s · measured %d" % (a.raw, measured)
    if kind == "min-box":
        w, h = measured
        need = float(a.expected[:-2])
        return None if w + 0.5 >= need and h + 0.5 >= need else "expected %s · measured %.0f×%.0f" % (a.raw, w, h)
    return "expected %s · no comparison for %s" % (a.raw, kind)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Read and validate the element inventory.")
    ap.add_argument("--inventory", default=str(DOC))
    ap.add_argument("--count", action="store_true", help="print the row counts and exit")
    ap.add_argument("--tokens", action="store_true", help="print the guarded class tokens")
    args = ap.parse_args(argv)
    try:
        inv = load(Path(args.inventory))
    except InventoryError as exc:
        print("INVENTORY ERROR: %s" % exc, file=sys.stderr)
        return 2
    if args.tokens:
        print(" ".join(sorted(class_tokens(inv.elements))))
    else:
        n_assert = sum(len(e.assertions) for e in inv.elements)
        print("%d elements, %d assertions, %d pages" % (len(inv.elements), n_assert, len(inv.pages)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
