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


@pytest.mark.parametrize("change, message", [
    (lambda r: r["components"]["box"]["parts"]["label"].update(colour="ink"), "unknown key colour"),
    (lambda r: r["components"]["box"]["parts"]["label"].update(text="99-100-ink"), "is in no set"),
    (lambda r: r["components"]["box"]["narrow"].update(below="w999"), "switch 'w999' is in no set"),
    (lambda r: r["components"]["box"]["parts"]["label"].update(breaks="anywhere"), "breaks must be one of"),
    (lambda r: r["components"]["box"]["parts"]["label"].update(gap="later"), "gap must be one of"),
    (lambda r: r["components"]["box"]["parts"]["frame"].update({"class": True}), "are strings"),
    (lambda r: r["components"]["box"]["parts"]["frame"].update(element="Box frame"), "needs rule, measured and ruled-on"),
    (lambda r: r["sets"].pop("marks"), "missing marks"),
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
    assert got["set sizes"] == {"text": 1, "marks": 1, "spacing": 1, "colours": 2, "switch": 1}


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


@pytest.mark.parametrize("path", ["tests/fixtures/component_registry/baseline.json",
                                  "tests/fixtures/font_coverage/baseline.json"])
def test_no_pin_rises_above_mains(path):
    base = _mains(path)
    if base is None:
        pytest.skip("main has no %s yet; this branch introduces it" % path)
    now, was = _flat(json.loads((REPO / path).read_text(encoding="utf-8"))), _flat(base)
    up = ["%s · %s · %d, main %d" % (k[0], k[1], n, was.get(k, 0)) for k, n in sorted(now.items(), key=str) if n > was.get(k, 0)]
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
