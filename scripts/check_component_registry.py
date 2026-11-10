"""The component registry check: `docs/design/components.yml` is the site's one list of components.

Reads the registry and fails closed on a key, set reference or form it does not know. Then:

- generates the element table of `docs/wireframes/block_standard.md` from the registry and fails
  when the document's table differs (`--write` rewrites it);
- counts the gaps of the registry's checks 3 and 4 in `site_v2/src/styles/system.css`:
  `stylesheet values` — a font size, weight, colour, spacing or switch width no set holds;
  `forms` — a component whose rules switch at a width other than its one narrow form's;
  `unlisted classes` — a class the stylesheet styles and no component or rule lists;
- counts the parts the registry records as a gap (`gap:` on a part), per kind;
- counts the values each set holds.

Checks 1, 2 and 5 are measured by `check_design_inventory.py` on the generated rows: a part's class
is registered, its text style is asserted, and a part that never breaks is asserted on one line.
Every count is compared with `tests/fixtures/component_registry/baseline.json` in both directions.
Exit 0 clean, 1 on a table out of date or a count off its pin, 2 when the registry does not parse.

    python scripts/check_component_registry.py [--write]
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parent.parent
REGISTRY = REPO / "docs" / "design" / "components.yml"
DOC = REPO / "docs" / "wireframes" / "block_standard.md"
SYSTEM_CSS = REPO / "site_v2" / "src" / "styles" / "system.css"
BASELINE = REPO / "tests" / "fixtures" / "component_registry" / "baseline.json"

SETS = ("text", "marks", "spacing", "colours", "switch")
COMPONENT_KEYS = {"name", "file", "used-on", "parts", "wide", "narrow", "never-split", "short-forms"}
PART_KEYS = {"class", "selector", "text", "mark", "breaks", "element", "rule", "measured", "status", "ruled-on", "gap"}
RULE_KEYS = {"selector", "rule", "measured", "status", "ruled-on"}
TEXT_KEYS = {"size", "weight", "colour", "case"}
BREAKS = ("never", "between words")
GAPS = {
    "mock-css": "a design mock's CSS restyles this class, so the block standard cannot list it yet",
    "style-varies": "the part's text shows in more than one style today",
    "lines-unmeasured": "the part never breaks, and its mixed text sizes defeat the line count",
}
FITS = "fits"
RULED_ON = "the component registry"
HEADER = "| Element | Selector | Rule | Measured as | Status | Ruled on |"

TOKENS = ("page", "surface", "sunk", "line", "div", "ink", "ink-2", "muted", "accent",
          "win", "draw", "loss", "pill-ink", "track")


class RegistryError(ValueError):
    """The registry does not parse; the component, part and key are named."""


def _keys(where: str, got: dict, allowed: set[str], required: set[str] = frozenset()) -> None:
    if not isinstance(got, dict):
        raise RegistryError("%s: expected a mapping" % where)
    unknown = sorted(set(got) - allowed)
    if unknown:
        raise RegistryError("%s: unknown key %s" % (where, ", ".join(unknown)))
    missing = sorted(required - set(got))
    if missing:
        raise RegistryError("%s: missing %s" % (where, ", ".join(missing)))


def load(path: Path = REGISTRY) -> dict:
    reg = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    _keys("registry", reg, {"sets", "components", "rules"}, {"sets", "components"})
    sets = reg["sets"]
    _keys("sets", sets, set(SETS), set(SETS))
    for name, style in sets["text"].items():
        _keys("sets.text.%s" % name, style, TEXT_KEYS, {"size", "weight", "colour"})
    for name, mark in sets["marks"].items():
        _keys("sets.marks.%s" % name, mark, {"size", "colour"}, {"size", "colour"})
    for name in ("spacing", "colours"):
        if not isinstance(sets[name], list):
            raise RegistryError("sets.%s: expected a list" % name)
    for name, width in sets["switch"].items():
        if not re.fullmatch(r"\d+px", str(width)):
            raise RegistryError("sets.switch.%s: expected a px width, got %r" % (name, width))
    elements: set[str] = set()
    for cid, comp in reg["components"].items():
        where = "components.%s" % cid
        _keys(where, comp, COMPONENT_KEYS, {"name", "file", "used-on", "parts", "wide"})
        narrow = comp.get("narrow")
        if narrow is not None:
            _keys(where + ".narrow", narrow, {"below", "form"}, {"below", "form"})
            if narrow["below"] != FITS and narrow["below"] not in sets["switch"]:
                raise RegistryError("%s.narrow: switch %r is in no set" % (where, narrow["below"]))
        terms = comp.get("short-forms", [])
        if not isinstance(terms, list) or not all(isinstance(x, str) for x in terms) or len(set(terms)) != len(terms):
            raise RegistryError("%s.short-forms: expected a list of distinct term keys, got %r" % (where, terms))
        for pid, part in comp["parts"].items():
            pw = "%s.parts.%s" % (where, pid)
            _keys(pw, part, PART_KEYS, {"class"})
            if not isinstance(pid, str) or not isinstance(part["class"], str):
                raise RegistryError("%s: a part's name and class are strings; quote on, off, yes and no" % pw)
            if "text" in part and part["text"] not in sets["text"]:
                raise RegistryError("%s: text style %r is in no set" % (pw, part["text"]))
            if "mark" in part and part["mark"] not in sets["marks"]:
                raise RegistryError("%s: mark %r is in no set" % (pw, part["mark"]))
            if "breaks" in part and part["breaks"] not in BREAKS:
                raise RegistryError("%s: breaks must be one of %s" % (pw, " / ".join(BREAKS)))
            if "gap" in part and part["gap"] not in GAPS:
                raise RegistryError("%s: gap must be one of %s" % (pw, " / ".join(GAPS)))
            if "element" in part:
                if not {"rule", "measured", "ruled-on"} <= set(part):
                    raise RegistryError("%s: an element row needs rule, measured and ruled-on" % pw)
                if part["element"] in elements:
                    raise RegistryError("%s: element %r listed twice" % (pw, part["element"]))
                elements.add(part["element"])
    for name, rule in (reg.get("rules") or {}).items():
        _keys("rules.%s" % name, rule, RULE_KEYS, {"selector", "rule", "measured", "ruled-on"})
        if name in elements:
            raise RegistryError("rules.%s: element listed twice" % name)
        elements.add(name)
    return reg


def _selector(part: dict) -> str:
    return part.get("selector") or "." + part["class"]


def _style(sets: dict, name: str) -> str:
    s = sets["text"][name]
    out = []
    if re.fullmatch(r"[\d.]+px", str(s["size"])):
        out.append("font-size=%s" % s["size"])
    out.append("font-weight=%s" % s["weight"])
    if s["colour"] in TOKENS:
        out.append("color=%s" % s["colour"])
    if s.get("case") == "upper":
        out.append("text-transform=uppercase")
    return "; ".join(out)


def rows(reg: dict) -> list[tuple[str, str, str, str, str, str]]:
    """The element table: one row per part that names its element, one per new text part, one
    for the rest of each component's parts, then the rules. A part recorded as a `mock-css` gap is
    left out."""
    sets = reg["sets"]
    out = []
    for comp in reg["components"].values():
        rest = []
        for pid, part in comp["parts"].items():
            if part.get("gap") == "mock-css":
                continue
            if "element" in part:
                out.append((part["element"], _selector(part), part["rule"], part["measured"],
                            part.get("status", "ruled"), part["ruled-on"]))
                continue
            measured = []
            if "text" in part:
                measured.append(_style(sets, part["text"]))
            if part.get("breaks") == "never" and "gap" not in part:
                measured.append("one-line; fits")
            if not measured:
                rest.append(_selector(part))
                continue
            label = pid.replace("-", " ")
            rule = "the %s's %s" % (comp["name"].lower(), label)
            if "text" in part:
                rule += ", in the %s text style" % part["text"]
            if part.get("breaks") == "never":
                rule += ", never broken"
            out.append(("%s %s" % (comp["name"], label), _selector(part), rule, "; ".join(measured), "ruled", RULED_ON))
        if rest:
            out.append(("%s parts" % comp["name"], ", ".join(rest),
                        "the %s's other parts: registered, no text of their own" % comp["name"].lower(), "", "ruled", RULED_ON))
    for name, rule in (reg.get("rules") or {}).items():
        out.append((name, rule["selector"], rule["rule"], rule["measured"], rule.get("status", "ruled"), rule["ruled-on"]))
    return out


def table(reg: dict) -> str:
    lines = [HEADER, "|---|---|---|---|---|---|"]
    for name, sel, rule, measured, status, ruled_on in rows(reg):
        lines.append("| %s | `%s` | %s | %s | %s | %s |" % (name, sel, rule, "`%s`" % measured if measured else "", status, ruled_on))
    return "\n".join(lines) + "\n"


def splice(doc: str, new_table: str) -> str:
    start = doc.index(HEADER)
    end = doc.index("\n\n", start) + 1
    return doc[:start] + new_table + doc[end:]


# --- the stylesheet -------------------------------------------------------------------------

_COMMENT = re.compile(r"/\*.*?\*/", re.DOTALL)
_DECL = re.compile(r"(?<![\w-])(--[\w-]+|[a-z-]+)\s*:\s*([^;{}]+)")
_QUERY = re.compile(r"@(?:media|container)\b([^{]*)\{")
_WIDTH = re.compile(r"\((min|max)-width:\s*([\d.]+)px\)")
_CLASS = re.compile(r"\.([A-Za-z_][\w-]*)")
_FUNC = re.compile(r"[a-z-]+\((?:[^()]|\([^()]*\))*\)|[^\s,()]+")
SPACING_PROPS = re.compile(r"^(margin|padding)(-(top|right|bottom|left|inline|block)(-(start|end))?)?$|^(row-|column-)?gap$")
COLOUR_PROPS = ("color", "background-color", "background", "fill", "stroke")


def _css(path: Path = SYSTEM_CSS) -> str:
    text = _COMMENT.sub(lambda m: " " * len(m.group(0)), path.read_text(encoding="utf-8"))
    return re.sub(r"@font-face\s*\{[^}]*\}", "", text)


def _vars(css: str) -> dict[str, str]:
    return {m.group(1): m.group(2).strip() for m in _DECL.finditer(css) if m.group(1).startswith("--")}


def _resolve(value: str, defs: dict[str, str]) -> str:
    m = re.fullmatch(r"var\((--[\w-]+)\)", value)
    return _resolve(defs[m.group(1)], defs) if m and m.group(1) in defs else value


def switch_width(kind: str, px: str) -> str:
    """The width a query switches at: `max-width: 699.98px` and `min-width: 700px` are both 700."""
    w = float(px)
    return "%dpx" % (round(w + 0.02) if kind == "max" and w % 1 else round(w))


def stylesheet_values(css: str) -> dict[str, list[str]]:
    """Every value the stylesheet writes, per set: font sizes, weights, colours, spacings, widths."""
    defs = _vars(css)
    out: dict[str, list[str]] = {"size": [], "weight": [], "colour": [], "spacing": [], "switch": []}
    for m in _DECL.finditer(css):
        prop, value = m.group(1), m.group(2).strip()
        if prop.startswith("--"):
            continue
        if prop == "font":
            if value == "inherit":
                continue
            parts = value.split()
            out["weight"].append(parts[0])
            out["size"].append(parts[1].split("/")[0])
        elif prop == "font-size" and value != "inherit":
            out["size"].append(_resolve(value, defs))
        elif prop == "font-weight":
            out["weight"].append(value)
        elif prop in COLOUR_PROPS:
            for tok in re.findall(r"var\(--([\w-]+)\)|(#[0-9a-fA-F]{3,8})\b", value):
                out["colour"].append(tok[0] or tok[1].lower())
        elif SPACING_PROPS.match(prop):
            for tok in _FUNC.findall(value):
                if tok not in ("0", "0px", "auto", "inherit", "!important"):
                    out["spacing"].append(tok)
    for q in _QUERY.finditer(css):
        for kind, px in _WIDTH.findall(q.group(1)):
            out["switch"].append(switch_width(kind, px))
    return out


def _set_values(reg: dict) -> dict[str, set[str]]:
    sets = reg["sets"]
    return {
        "size": {str(s["size"]) for s in sets["text"].values()},
        "weight": {str(s["weight"]) for s in sets["text"].values()},
        "colour": {str(c) for c in sets["colours"]} | {str(s["colour"]) for s in sets["text"].values()},
        "spacing": {str(v) for v in sets["spacing"]},
        "switch": {str(v) for v in sets["switch"].values()},
    }


def _rules(css: str):
    """(selector text, switch widths of the queries around it) for every style rule."""
    out = []
    stack: list[list[str]] = []
    pos = 0
    for m in re.finditer(r"[{}]", css):
        head = css[pos:m.start()].strip()
        pos = m.end()
        if m.group(0) == "{":
            q = _QUERY.match(head + "{") if head.startswith("@") else None
            widths = [switch_width(k, px) for k, px in _WIDTH.findall(q.group(1))] if q else []
            if not head.startswith("@"):
                out.append((head, [w for frame in stack for w in frame]))
            stack.append(widths)
        elif stack:
            stack.pop()
    return out


_PSEUDO = re.compile(r":(?:not|has|is|where)\((?:[^()]|\([^()]*\))*\)")


def owners(reg: dict, selector: str) -> set[str]:
    """The components a style rule styles. For each alternative of the selector, its subject is the
    last class outside `:not()`, `:has()` and the like; the owners are the components that list
    that class, narrowed to those sharing the most of the rule's classes, then to those with a part
    of that class."""
    universe = {cid: {c for part in comp["parts"].values() for c in _CLASS.findall(_selector(part))} | {part["class"] for part in comp["parts"].values()}
                for cid, comp in reg["components"].items()}
    own = {cid: {part["class"] for part in comp["parts"].values()} for cid, comp in reg["components"].items()}
    out: set[str] = set()
    for alt in selector.split(","):
        subjects = _CLASS.findall(_PSEUDO.sub("", alt))
        if not subjects:
            continue
        subject, classes = subjects[-1], set(_CLASS.findall(alt))
        found = [cid for cid, u in universe.items() if subject in u]
        if not found:
            continue
        best = max(len(universe[cid] & classes) for cid in found)
        found = [cid for cid in found if len(universe[cid] & classes) == best]
        mine = [cid for cid in found if subject in own[cid]]
        out.update(mine or found)
    return out


def component_widths(reg: dict, css: str) -> dict[str, set[str]]:
    """The switch widths of the query rules that style each component."""
    out: dict[str, set[str]] = {}
    for sel, ws in _rules(css):
        if ws:
            for cid in owners(reg, sel):
                out.setdefault(cid, set()).update(ws)
    return out


def counts(reg: dict, css: str) -> dict[str, dict[str, int]]:
    allowed = _set_values(reg)
    out: dict[str, dict[str, int]] = {"stylesheet values": {}, "forms": {}, "unlisted classes": {}, "part gaps": {}, "set sizes": {}}
    for group, values in stylesheet_values(css).items():
        n = sum(1 for v in values if v not in allowed[group])
        if n:
            out["stylesheet values"][group] = n
    listed: set[str] = set()
    for comp in reg["components"].values():
        for part in comp["parts"].values():
            listed.update(_CLASS.findall(_selector(part)))
            listed.add(part["class"])
    for rule in (reg.get("rules") or {}).values():
        listed.update(_CLASS.findall(rule["selector"]))
    widths = component_widths(reg, css)
    styled = {c for sel, _ in _rules(css) for c in _CLASS.findall(sel)}
    for cid, comp in reg["components"].items():
        narrow = comp.get("narrow")
        declared = reg["sets"]["switch"].get(narrow["below"]) if narrow else None
        extra = len(widths.get(cid, set()) - {declared})
        if extra:
            out["forms"][cid] = extra
    unlisted = len(styled - listed)
    if unlisted:
        out["unlisted classes"]["system.css"] = unlisted
    for comp in reg["components"].values():
        for part in comp["parts"].values():
            if "gap" in part:
                out["part gaps"][part["gap"]] = out["part gaps"].get(part["gap"], 0) + 1
    for name in SETS:
        out["set sizes"][name] = len(reg["sets"][name])
    return out


def compare(measured: dict, pinned: dict) -> list[str]:
    lines = []
    for group in sorted(set(measured) | set(pinned)):
        m, p = measured.get(group, {}), pinned.get(group, {})
        for key in sorted(set(m) | set(p)):
            now, was = m.get(key, 0), p.get(key, 0)
            if now > was:
                lines.append("count rose · %s · %s · %d, baseline %d" % (group, key, now, was))
            elif now < was:
                lines.append("count fell · %s · %s · %d, baseline %d: lower the baseline" % (group, key, now, was))
    return lines


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--registry", default=str(REGISTRY))
    ap.add_argument("--doc", default=str(DOC))
    ap.add_argument("--css", default=str(SYSTEM_CSS))
    ap.add_argument("--baseline", default=str(BASELINE))
    ap.add_argument("--write", action="store_true", help="rewrite the block standard's element table")
    args = ap.parse_args(argv)
    try:
        reg = load(Path(args.registry))
    except (RegistryError, yaml.YAMLError) as e:
        print("FAIL  registry: %s" % e)
        return 2
    doc_path = Path(args.doc)
    doc = doc_path.read_text(encoding="utf-8")
    want = splice(doc, table(reg))
    failures = []
    if args.write:
        doc_path.write_text(want, encoding="utf-8")
    elif want != doc:
        failures.append("%s: the element table differs from the registry; run with --write" % doc_path.name)
    measured = counts(reg, _css(Path(args.css)))
    failures += compare(measured, json.loads(Path(args.baseline).read_text(encoding="utf-8")))
    for f in failures:
        print("FAIL  " + f)
    for group, by_key in measured.items():
        print("count %s: %s" % (group, ", ".join("%s %d" % kv for kv in sorted(by_key.items())) or "0"))
    print("component registry: %d components, %d table rows, %d failure(s)"
          % (len(reg["components"]), len(rows(reg)), len(failures)))
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
