"""Tests for scripts/check_component_registry.py: the registry's format, the generated element
table, the stylesheet counts, the pins on the real tree, and the CI job that runs it."""

from __future__ import annotations

import copy
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "scripts"))
import check_component_registry as ccr  # noqa: E402
import design_inventory as di  # noqa: E402

MINI = {
    "sets": {
        "text": {"13-700-muted": {"size": "13px", "weight": 700, "colour": "muted"}},
        "marks": {"dot": {"size": "6px", "colour": "ink"}},
        "spacing": ["8px"],
        "colours": ["ink", "muted"],
        "switch": {"w480": "480px"},
        "corners": ["4px", "50%"],
    },
    "components": {
        "box": {
            "name": "Box", "file": "x.astro", "used-on": ["Home"], "wide": "one line",
            "narrow": {"below": "w480", "form": "two lines"},
            "parts": {
                "label": {"class": "bx-l", "text": "13-700-muted", "breaks": "never"},
                "frame": {"class": "bx"},
                "mocked": {"class": "bx-m", "gap": "mock-css"},
                "unit": {"class": "bx-u", "breaks": "never", "gap": "lines-unmeasured"},
            },
        },
    },
}


def _write(tmp_path: Path, reg: dict) -> Path:
    p = tmp_path / "components.yml"
    p.write_text(yaml.safe_dump(reg, sort_keys=False), encoding="utf-8")
    return p


def test_the_real_registry_parses_and_its_table_is_the_block_standards():
    reg = ccr.load()
    doc = ccr.DOC.read_text(encoding="utf-8")
    assert ccr.splice(doc, ccr.table(reg)) == doc
    names = {e.name for e in di.load().elements}
    assert names == {r[0] for r in ccr.rows(reg)}


def test_the_real_tree_is_on_its_pins():
    assert ccr.main([]) == 0


def test_a_template_writes_the_classes_of_its_attributes():
    text = ('<div class="lrow tc"><span class:list={["pill", result, { winner: w, played }]} />'
            '<b class={CLASS[kind]} /><i class:list={["n", `x-${k}`, c.kind]} /></div>')
    assert ccr.template_classes(text) == ["lrow", "tc", "pill", "winner", "played", "n"]


def test_a_component_owns_the_classes_no_other_component_lists():
    reg = {"components": {
        "row": {"parts": {"row": {"class": "rw"}, "name": {"class": "nm"}}},
        "table": {"parts": {"name": {"class": "nm"}, "box": {"class": "tb"}}},
    }}
    assert ccr.own_classes(reg) == {"row": {"rw"}, "table": {"tb"}}


def _site(tmp_path: Path, files: dict) -> Path:
    for rel, text in files.items():
        p = tmp_path / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8")
    return tmp_path / "src"


def test_markup_of_a_part_outside_its_component_is_counted(tmp_path):
    reg = {"components": {
        "row": {"file": "src/ui/Row.astro", "parts": {"row": {"class": "rw"}, "name": {"class": "nm"}}},
        "table": {"file": ["src/a.astro", "src/b.astro"], "parts": {"name": {"class": "nm"}}},
    }}
    site = _site(tmp_path, {
        "src/ui/Row.astro": '<a class="rw"><span class="nm" /></a>',
        "src/Block.astro": '<div class="rw" /><div class:list={["rw", x]} /><span class="nm" />',
    })
    got = ccr.markup_counts(reg, site, tmp_path)
    assert got == {"markup outside its component": {"row": 2}, "components in several files": {"registry": 1}}


def test_a_link_to_a_page_type_the_registry_does_not_name_fails(tmp_path):
    _site(tmp_path, {
        "src/ui/Row.astro": 'const href = localeHref(lang, `${word(lang, "players")}/${slug}/`);',
        "src/ui/Team.astro": 'const href = localeHref(lang, `${word(lang, "teams")}/${slug}/`);',
    })
    reg = {"components": {
        "row": {"file": "src/ui/Row.astro", "links-to": ["team page"], "parts": {}},
        "team": {"file": "src/ui/Team.astro", "links-to": ["team page"], "parts": {}},
    }}
    got = ccr.link_failures(reg, tmp_path)
    assert got == ["components.row: src/ui/Row.astro links to the player page, which links-to does not name",
                   "components.row: links-to names the team page, which src/ui/Row.astro never links to"]


def test_a_nation_page_link_is_not_a_player_page_link(tmp_path):
    _site(tmp_path, {
        "src/ui/Head.astro": 'const href = localeHref(lang, `${word(lang, "players")}/${nation}/`);',
        "src/ui/Row.astro": 'const href = localeHref(lang, `${word(lang, "players")}/${page}/`);',
    })
    reg = {"components": {
        "head": {"file": "src/ui/Head.astro", "links-to": ["player page"], "parts": {}},
        "row": {"file": "src/ui/Row.astro", "links-to": ["nation page"], "parts": {}},
    }}
    assert ccr.link_failures(reg, tmp_path) == [
        "components.head: src/ui/Head.astro links to the nation page, which links-to does not name",
        "components.head: links-to names the player page, which src/ui/Head.astro never links to",
        "components.row: src/ui/Row.astro links to the player page, which links-to does not name",
        "components.row: links-to names the nation page, which src/ui/Row.astro never links to"]


def test_links_to_names_only_known_page_types(tmp_path):
    reg = copy.deepcopy(MINI)
    reg["components"]["box"]["links-to"] = ["stats page"]
    with pytest.raises(ccr.RegistryError, match="links-to"):
        ccr.load(_write(tmp_path, reg))


@pytest.mark.parametrize("change, message", [
    (lambda r: r["components"]["box"]["parts"]["label"].update(colour="ink"), "unknown key colour"),
    (lambda r: r["components"]["box"]["parts"]["label"].update(text="99-100-ink"), "is in no set"),
    (lambda r: r["components"]["box"]["narrow"].update(below="w999"), "switch 'w999' is in no set"),
    (lambda r: r["components"]["box"]["parts"]["label"].update(breaks="anywhere"), "breaks must be one of"),
    (lambda r: r["components"]["box"]["parts"]["label"].update(gap="later"), "gap must be one of"),
    (lambda r: r["components"]["box"]["parts"]["frame"].update({"class": True}), "are strings"),
    (lambda r: r["components"]["box"]["parts"]["frame"].update(element="Box frame"), "needs rule, measured and ruled-on"),
    (lambda r: r["components"]["box"].update({"short-forms": "played"}), "expected a list of distinct term keys"),
    (lambda r: r["components"]["box"].update({"short-forms": ["played", "played"]}), "expected a list of distinct term keys"),
    (lambda r: r["sets"].pop("marks"), "missing marks"),
    (lambda r: r["sets"].update(corners="4px"), "sets.corners: expected a list"),
    (lambda r: r["sets"]["switch"].update(w1="wide"), "expected a px width"),
])
def test_the_registry_fails_closed(tmp_path, change, message):
    reg = copy.deepcopy(MINI)
    change(reg)
    with pytest.raises(ccr.RegistryError, match=message):
        ccr.load(_write(tmp_path, reg))


def test_a_bare_yaml_on_is_refused_as_a_class(tmp_path):
    p = tmp_path / "components.yml"
    text = yaml.safe_dump(MINI, sort_keys=False).replace("class: bx\n", "class: on\n")
    p.write_text(text, encoding="utf-8")
    with pytest.raises(ccr.RegistryError, match="are strings"):
        ccr.load(p)


def test_the_generated_rows():
    rows = {r[0]: r for r in ccr.rows(MINI)}
    assert rows["Box label"][1:4] == (".bx-l", "the box's label, in the 13-700-muted text style, never broken",
                                      "font-size=13px; font-weight=700; color=muted; one-line; fits")
    assert rows["Box parts"][1] == ".bx, .bx-u"
    assert rows["Box parts"][3] == ""
    assert not any(".bx-m" in r[1] for r in rows.values()), "a mock-css part stays out of the table"
    di.parse_measured(rows["Box label"][3])


def test_an_element_row_keeps_its_text_and_a_rule_follows_the_components():
    reg = copy.deepcopy(MINI)
    reg["components"]["box"]["parts"]["frame"].update(
        {"element": "Frame", "selector": ".bx > .f", "rule": "the frame", "measured": "fits", "status": "proposed", "ruled-on": "#1"})
    reg["rules"] = {"Row link": {"selector": "a.bx", "rule": "one link", "measured": "fits", "ruled-on": "#2"}}
    rows = ccr.rows(reg)
    assert ("Frame", ".bx > .f", "the frame", "fits", "proposed", "#1") in rows
    assert rows[-1] == ("Row link", "a.bx", "one link", "fits", "ruled", "#2")


def test_the_table_replaces_only_the_element_table():
    doc = "# T\n\nintro\n\n" + ccr.HEADER + "\n|---|\n| old | `.x` | r | `fits` | ruled | #1 |\n\n## Pages\n\nrest\n"
    out = ccr.splice(doc, ccr.table(MINI))
    assert out.startswith("# T\n\nintro\n\n" + ccr.HEADER)
    assert out.endswith("\n\n## Pages\n\nrest\n")
    assert "| old |" not in out and "| Box label |" in out


@pytest.mark.parametrize("kind, px, want", [("max", "699.98", "700px"), ("min", "700", "700px"),
                                            ("max", "480", "480px"), ("max", "479.98", "480px")])
def test_a_query_switches_at_one_width(kind, px, want):
    assert ccr.switch_width(kind, px) == want


def test_stylesheet_values_outside_the_sets_are_counted():
    css = (".bx-l { font-size: 13px; font-weight: 700; color: var(--muted); margin: 8px 0; }\n"
           ".bx { font-size: 9px; padding: 7px; background: var(--loss); }\n"
           "@container (max-width: 479.98px) { .bx-l { gap: 8px; } }\n"
           "@media (min-width: 900px) { .bx { margin-top: 8px; } }\n")
    got = ccr.counts(MINI, css)
    assert got["stylesheet values"] == {"size": 1, "spacing": 1, "colour": 1, "switch": 1}
    assert got["forms"] == {"box": 1}
    assert got["part gaps"] == {"mock-css": 1, "lines-unmeasured": 1}
    assert got["set sizes"] == {"text": 1, "marks": 1, "spacing": 1, "colours": 2, "switch": 1, "corners": 2}


def test_a_corner_radius_outside_the_set_is_counted_per_value():
    css = (".bx { border-radius: 4px; }\n.a { border-radius: 9px; }\n.b { border-radius: 3px 0 0 4px; }\n"
           ".c { border-top-left-radius: 50%; border-radius: 0; }\n")
    assert ccr.counts(MINI, css)["stylesheet values"] == {"corner": 2}
    assert "corner" not in ccr.counts(MINI, ".bx { border-radius: 4px 50%; }\n")["stylesheet values"]


def test_a_property_no_set_governs_is_counted_as_unchecked():
    css = (".bx { display: flex; gap: 8px; font-size: 13px; color: var(--ink); border-radius: 4px; }\n"
           ".bx { border-bottom: 1px solid var(--line); width: 40px; height: 4px; box-shadow: 0 0 2px #000; }\n"
           ".a { background: color-mix(in srgb, var(--ink) 5%, transparent); }\n"
           ".b { background: var(--ink); fill: none; --muted: #888; --new: 5px; }\n"
           "@media (min-width: 480px) { .bx { width: 50px; } }\n")
    assert ccr.counts(MINI, css)["unchecked property"] == {
        "border-bottom": 1, "width": 2, "height": 1, "box-shadow": 1, "background": 1, "--new": 1}


def test_a_new_unchecked_property_fails_the_pin():
    pinned = {"unchecked property": {"width": 1}}
    got = ccr.counts(MINI, ".bx { width: 1px; float: left; }\n")
    assert ccr.compare({"unchecked property": got["unchecked property"]}, pinned) == ["count rose · unchecked property · float · 1, baseline 0"]


def test_a_new_radius_fails_the_pin():
    got = ccr.counts(MINI, ".bx { border-radius: 11px; }\n")
    assert ccr.compare({"stylesheet values": got["stylesheet values"]}, {"stylesheet values": {}}) == [
        "count rose · stylesheet values · corner · 1, baseline 0"]


def test_a_declaration_inside_parentheses_is_not_split():
    assert ccr.declarations('.a { mask-image: url("data:image/svg+xml;utf8,x"); color: red }') == [
        ("mask-image", 'url("data:image/svg+xml;utf8,x")'), ("color", "red")]


def test_inline_styles_in_a_page_are_counted(tmp_path):
    (tmp_path / "ok.astro").write_text('<div class="a" data-style="x"></div>\n', encoding="utf-8")
    assert ccr.inline_styles(tmp_path) == {}
    (tmp_path / "a.astro").write_text('<p style="color:red">x</p>\n<span style={`width:1%`}></span>\n', encoding="utf-8")
    (tmp_path / "b.astro").write_text("<style>.x { color: red }</style>\n", encoding="utf-8")
    assert ccr.inline_styles(tmp_path) == {"style attribute": 2, "style block": 1}
    assert ccr.counts(MINI, ".bx { color: var(--ink); }\n", tmp_path)["inline styles"] == {"style attribute": 2, "style block": 1}


def test_an_inline_style_fails_the_run(tmp_path):
    base = json.loads(ccr.BASELINE.read_text(encoding="utf-8"))
    base["inline styles"] = {}
    pins = tmp_path / "baseline.json"
    pins.write_text(json.dumps(base), encoding="utf-8")
    src = tmp_path / "src"
    src.mkdir()
    assert ccr.main(["--src", str(src), "--baseline", str(pins)]) == 0
    (src / "a.astro").write_text('<p style="color:red">x</p>\n', encoding="utf-8")
    assert ccr.main(["--src", str(src), "--baseline", str(pins)]) == 1


def test_a_class_the_stylesheet_styles_and_no_component_lists_is_counted():
    got = ccr.counts(MINI, ".bx { color: var(--ink); }\n.orphan { color: var(--ink); }\n")
    assert got["unlisted classes"] == {"system.css": 1}


def test_a_query_rule_belongs_to_the_component_owning_its_subject():
    reg = {"components": {
        "board": {"parts": {"name": {"class": "nm", "selector": ".ctab.rkt .nm"}, "box": {"class": "board"}}},
        "group": {"parts": {"name": {"class": "nm", "selector": ".fxgroup .nm"}}},
        "table": {"parts": {"box": {"class": "ctab"}, "head": {"class": "ctab-head"}}},
        "last": {"parts": {"trend": {"class": "tr", "selector": ".ctab.yoyt .tr"}}},
    }}
    assert ccr.owners(reg, ".board .nm") == {"board"}
    assert ccr.owners(reg, ".ctab") == {"table"}
    assert ccr.owners(reg, ".ctab:not(.fit-one) .ctab-head") == {"table"}
    assert ccr.owners(reg, ".unknown") == set()


def test_a_count_off_its_pin_fails_in_both_directions():
    assert ccr.compare({"forms": {"box": 1}}, {"forms": {"box": 1}}) == []
    assert ccr.compare({"forms": {"box": 2}}, {"forms": {"box": 1}})[0].startswith("count rose · forms · box · 2")
    assert ccr.compare({}, {"forms": {"box": 1}})[0].startswith("count fell · forms · box · 0")


def test_an_out_of_date_table_fails(tmp_path):
    doc = tmp_path / "block_standard.md"
    doc.write_text(ccr.DOC.read_text(encoding="utf-8").replace("| Block heading |", "| Block title |", 1), encoding="utf-8")
    assert ccr.main(["--doc", str(doc)]) == 1
    assert ccr.main(["--doc", str(doc), "--write"]) == 0
    assert doc.read_text(encoding="utf-8") == ccr.DOC.read_text(encoding="utf-8")


def _mains(path: str) -> dict | None:
    """The file on the branch this one merges into, as test_design_inventory reads its baseline;
    None when that branch does not have it yet."""
    def git(*args):
        return subprocess.run(["git", "-c", "safe.directory=*", *args], cwd=REPO, capture_output=True, text=True,
                              encoding="utf-8")

    ref = os.environ.get("CI_MERGE_REQUEST_DIFF_BASE_SHA") or ("HEAD^1" if os.environ.get("CI") else "")
    if not ref:
        remote = "gitlab/main" if git("rev-parse", "--verify", "-q", "gitlab/main").returncode == 0 else "origin/main"
        ref = git("merge-base", "HEAD", remote).stdout.strip()
    assert ref, "no base to compare the baseline with"
    proc = git("show", "%s:%s" % (ref, path))
    if proc.returncode and os.environ.get("CI"):
        if ref == "HEAD^1":
            git("fetch", "--no-tags", "--deepen=1", "origin")
        else:
            git("fetch", "--no-tags", "--depth=1", "origin", ref)
        proc = git("show", "%s:%s" % (ref, path))
    if proc.returncode:
        assert "does not exist" in proc.stderr or "exists on disk, but not in" in proc.stderr, proc.stderr
        return None
    return json.loads(proc.stdout)


def _flat(pins: dict) -> dict:
    return {(g, k): n for g, by in pins.items() for k, n in (by.items() if isinstance(by, dict) else [(None, by)])}


def _rises(now: dict, was: dict, measured: set[str] | None = None) -> list[str]:
    """Every pin above main's, except the switch set's size: it counts declared breakpoints, not a
    gap, and the check pins it both ways; and except a count group main's baseline does not hold at
    all (`measured`, main's group names), whose first pins are what the branch introducing it
    measures. A group main holds empty is measured: every pin in it is 0. The corners set's size
    is introduced the same way, once."""
    return ["%s · %s · %d, main %d" % (k[0], k[1], n, was.get(k, 0)) for k, n in sorted(now.items(), key=str)
            if n > was.get(k, 0) and k != ("set sizes", "switch") and (measured is None or k[0] in measured)
            and not (k == ("set sizes", "corners") and k not in was)]


def test_only_the_switch_set_may_grow_past_mains():
    was = {("set sizes", "switch"): 12, ("set sizes", "colours"): 20, ("forms", "x"): 0}
    now = {("set sizes", "switch"): 13, ("set sizes", "colours"): 21, ("forms", "x"): 1}
    assert _rises(now, was) == ["forms · x · 1, main 0", "set sizes · colours · 21, main 20"]


def test_a_count_group_main_does_not_hold_starts_at_the_branchs_pins():
    main = {"forms": {"x": 1}}
    now = {("forms", "x"): 1, ("markup outside its component", "box"): 3}
    assert _rises(now, _flat(main), set(main)) == []


def test_a_rise_in_a_group_main_holds_empty_is_reported():
    main = {"forms": {"x": 1}, "stylesheet values": {}}
    now = {("forms", "x"): 1, ("stylesheet values", "size"): 1}
    assert _rises(now, _flat(main), set(main)) == ["stylesheet values · size · 1, main 0"]


def test_the_corners_set_is_introduced_once_and_then_only_falls():
    main = {"set sizes": {"colours": 20}}
    now = {("set sizes", "colours"): 20, ("set sizes", "corners"): 3}
    assert _rises(now, _flat(main), set(main)) == []
    main = {"set sizes": {"colours": 20, "corners": 2}}
    assert _rises(now, _flat(main), set(main)) == ["set sizes · corners · 3, main 2"]


@pytest.mark.parametrize("path", ["tests/fixtures/component_registry/baseline.json",
                                  "tests/fixtures/font_coverage/baseline.json"])
def test_no_pin_rises_above_mains(path):
    base = _mains(path)
    if base is None:
        pytest.skip("main has no %s yet; this branch introduces it" % path)
    up = _rises(_flat(json.loads((REPO / path).read_text(encoding="utf-8"))), _flat(base), set(base))
    assert up == [], "a pin rose above main's; a new gap is fixed, not pinned:\n" + "\n".join(up)


def _ci():
    return yaml.safe_load((REPO / ".gitlab-ci.yml").read_text(encoding="utf-8"))


def test_validate_ui_runs_the_registry_check_the_font_check_and_the_tests():
    script = " ".join(_ci()["validate:ui"]["script"])
    for step in ("scripts/check_component_registry.py", "site_v2/scripts/check-font-coverage.mjs --dist site_v2/dist",
                 "tests/test_check_component_registry.py"):
        assert step in script, step
    paths = _ci()[".ui_paths"]
    for p in ("docs/design/components.yml", "scripts/check_component_registry.py", "tests/test_check_component_registry.py",
              "tests/fixtures/component_registry/*", "tests/fixtures/font_coverage/*"):
        assert p in paths, p
