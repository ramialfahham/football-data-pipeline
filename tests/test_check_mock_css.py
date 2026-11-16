"""The mock CSS check: Today must equal main's rules, `html.prop` rules are listed, `.mock-*` ignored.

The fixtures hold a small stand-in for main's stylesheet (`base.css`) and one mock per case. The
browser tests skip where Chromium is not installed; the classifier tests run everywhere.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "design-mocks"))
import check_mock_css as cm  # noqa: E402

FIXTURES = REPO / "tests" / "fixtures" / "mock_css"


def _chromium_available() -> bool:
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        return False
    try:
        with sync_playwright() as pw:
            pw.chromium.launch().close()
        return True
    except Exception:
        return False


needs_browser = pytest.mark.skipif(not _chromium_available(), reason="Playwright's Chromium is not installed here")


def _run(name: str):
    return cm.check((FIXTURES / name).read_text(encoding="utf-8"), (FIXTURES / "base.css").read_text(encoding="utf-8"))


@pytest.mark.parametrize("sel, kind", [
    (".card", "today"),
    ("html.prop .card", "proposed"),
    ("html.prop, html.prop .card", "proposed"),
    ("html.prop .card, .card", "today"),
    (".mock-bar", "mock"),
    (".mock-a, .mock-b", "mock"),
    (".mock-a, .card", "today"),
    (".card:not(.mock-x)", "today"),
    (".mock-frame .card", "today"),
    (".card .mock-a", "mock"),
    ("html.property .card", "today"),
    ("html.prop-x", "today"),
])
def test_classify(sel, kind):
    assert cm.classify(sel) == kind


@needs_browser
def test_clean_mock_passes_despite_formatting_differences():
    diffs, proposed = _run("clean.html")
    assert diffs == [] and proposed == []


@needs_browser
def test_changed_main_rule_fails_with_both_sides():
    diffs, _ = _run("changed.html")
    assert len(diffs) == 1
    assert diffs[0].startswith("changed: .card .t")
    assert "font-size: 13px" in diffs[0] and "font-size: 17px" in diffs[0]


@needs_browser
def test_new_unscoped_rule_fails():
    diffs, _ = _run("new_rule.html")
    assert len(diffs) == 1 and diffs[0].startswith("new in mock: .extra")


@needs_browser
def test_missing_main_rule_fails():
    diffs, _ = _run("missing.html")
    assert len(diffs) == 1 and diffs[0].startswith("missing from mock: .card .t")


@needs_browser
def test_proposed_listed_and_mock_and_font_face_ignored():
    diffs, proposed = _run("proposed.html")
    assert diffs == []
    assert [s for s, _ in proposed] == ["html.prop .card .t", "html.prop, html.prop .card"]
    assert "font-size: 20px" in proposed[0][1]


def _inline(base: str, mock: str):
    return cm.check(f"<style>{mock}</style>", base)


@needs_browser
@pytest.mark.parametrize("base, mock, fragment", [
    (".a{color:red}.a{color:blue}", ".a{color:blue}.a{color:red}", "changed: .a"),
    (".a{color:red}.a{color:red}", ".a{color:red}", "changed: .a"),
    (".a{color:red}.b{color:red}", ".b{color:red}.a{color:red}", "rule order differs"),
    (".card{color:red}", ".card{color:red;.x{color:blue}}", "new in mock: .card > & .x"),
    ("", "@layer a,b;", "new in mock: @layer a, b;"),
    ("", ".card:not(.mock-x){color:red}", "new in mock: .card:not(.mock-x)"),
    ("", ".mock-frame .card{color:red}", "new in mock: .mock-frame .card"),
    (".a{background:var(--x)}", ".a{background:var(--y)}", "changed: .a"),
    (".a{margin:var(--x) 0}", ".a{margin:var(--x) 4px}", "changed: .a"),
    ("", '@import url("data:text/css,.q{color:red}");', "new in mock: @import"),
    ("", "@import url(https://x.test/a.css);", "new in mock: @import"),
    ("", ".card[title=\".mock-x\"]{color:red}", "new in mock: .card[title="),
    ("", "html.property .card{color:red}", "new in mock: html.property .card"),
    ("", "@media (min-width:1px){.card{color:red !important}}", "new in mock: @media (min-width: 1px) .card"),
    ("@supports (display:grid){.g{display:grid}}", "@supports (display:grid){.g{display:flex}}", "changed: @supports (display:grid) .g"),
])
def test_holes_are_caught(base, mock, fragment):
    diffs, _ = _inline(base, mock)
    assert any(d.startswith(fragment) or fragment in d for d in diffs), diffs


@needs_browser
def test_media_attribute_on_style_is_part_of_the_context():
    diffs, _ = cm.check('<style media="print">.a{color:red}</style>', ".a{color:red}")
    assert len(diffs) == 2


@needs_browser
def test_linked_stylesheet_is_flagged():
    diffs, _ = cm.check('<link rel="stylesheet" href="https://x.test/a.css">', "")
    assert diffs and "linked stylesheet not read" in diffs[0]


@needs_browser
def test_cli_exit_codes(capsys, tmp_path):
    css = REPO / "site_v2" / "src" / "styles" / "system.css"
    mock = tmp_path / "m.html"
    mock.write_text(f"<style>{css.read_text(encoding='utf-8')}\nhtml.prop .x{{color:red}}</style>", encoding="utf-8")
    assert cm.main([str(mock), "--base", "HEAD"]) == 0
    assert "Proposed rules (html.prop): 1" in capsys.readouterr().out
    mock.write_text("<style>.x{color:red}</style>", encoding="utf-8")
    assert cm.main([str(mock), "--base", "HEAD"]) == 1
    assert cm.main([str(tmp_path / "none.html")]) == 2
    assert cm.main([str(mock), "--base", "no-such-ref"]) == 2
    bad = tmp_path / "bad.html"
    bad.write_bytes(b"\xff\xfe<style>")
    assert cm.main([str(bad), "--base", "HEAD"]) == 2
