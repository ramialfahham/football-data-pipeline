"""The block standard's machine side: the parser fails closed, the lint finds page CSS, and the
measured check goes RED on the defects it exists for.

`docs/wireframes/block_standard.md` is read by `scripts/design_inventory.py`; the lint
(`scripts/check_page_css.py`) and the measured check (`scripts/check_design_inventory.py`) read
nothing else. The RED proof renders `tests/fixtures/design_inventory/green.html` (the page as the
inventory rules it, with the real stylesheet beside it) and `red.html` (the same page with the
defects of the competition page review reconstructed on top: the 11px block name, the 34px and
15px added under a heading, the surface-coloured hover, stripes from the first row, a tab bar
that overflows, every matchday's picker step shown at once with 20px arrows) and asserts the
check is green on one and red on exactly those elements on the other. A check only ever seen
green proves nothing. The browser tests skip where Chromium is not installed; the parser and
lint tests run everywhere.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import textwrap
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "scripts"))
import check_page_css as lint  # noqa: E402
import design_inventory as di  # noqa: E402

FIXTURES = REPO / "tests" / "fixtures" / "design_inventory"
SYSTEM_CSS = REPO / "site_v2" / "src" / "styles" / "system.css"

DOC_HEAD = textwrap.dedent("""\
    # test inventory

    ## Elements

    | Element | Selector | Rule | Measured as | Status | Ruled on |
    |---|---|---|---|---|---|
    """)
PAGES = textwrap.dedent("""\

    ## Pages

    | Page | Kind | Source | URL | FI | Expect |
    |---|---|---|---|---|---|
    | home | mock | `gen_home.py` | `home.html` | toggle | Block heading |
    """)


def _doc(tmp_path: Path, rows: str, pages: str = PAGES) -> Path:
    p = tmp_path / "block_standard.md"
    p.write_text(DOC_HEAD + rows + pages, encoding="utf-8")
    return p


GOOD_ROW = "| Block heading | `.sechead .eyebrow` | 13px capitals | `font-size=13px; text-transform=uppercase; color=muted` | ruled | #129 |\n"


def test_the_check_renders_every_locale_the_site_publishes():
    """The check's language set against the site's own, so neither can move alone.

    German went unmeasured for the whole life of this check because the two lists are maintained
    independently: the site declared three locales while `DEFAULT_LANGS` named two, and the
    summary line reported success either way. A fourth locale would repeat it silently, so the
    two files are pinned to each other the way `FAST_GATES` and the validate-local skill are.
    """
    sys.path.insert(0, str(REPO / "scripts"))
    import check_design_inventory as cdi  # noqa: PLC0415

    href = (REPO / "site_v2" / "src" / "lib" / "href.ts").read_text(encoding="utf-8")
    declared = re.search(r"export const LOCALES: Lang\[\] = \[([^\]]*)\]", href)
    assert declared, "href.ts no longer declares LOCALES in the shape this test reads"
    site_locales = sorted(re.findall(r'"([a-z]{2})"', declared.group(1)))

    assert sorted(cdi.DEFAULT_LANGS) == site_locales, (
        "the measured check renders %s while the site publishes %s — a locale the check does not "
        "render can break its layout and still pass" % (sorted(cdi.DEFAULT_LANGS), site_locales)
    )
    # The mocks are the documented exception: one HTML file, English plus a marked Finnish width
    # probe, no German text to render. That narrower set must stay a subset, not drift wider.
    assert set(cdi.MOCK_LANGS) <= set(cdi.DEFAULT_LANGS)


def test_the_check_renders_the_width_the_search_field_appears_at():
    """The header's search field is hidden below the width `system.css` shows it at, so a check
    that never renders that width has never seen the field, and a broken one passed. The width
    is read from the stylesheet, so moving the breakpoint without the check turns this red."""
    sys.path.insert(0, str(REPO / "scripts"))
    import check_design_inventory as cdi  # noqa: PLC0415

    css = SYSTEM_CSS.read_text(encoding="utf-8")
    shown = re.search(r"@media \(min-width: (\d+)px\) \{\s*\.searchbox \{ display: flex; \}", css)
    assert shown, "system.css no longer shows .searchbox in the media query this test reads"
    width = int(shown.group(1))
    assert width in cdi.DEFAULT_VIEWPORTS, (
        "the search field appears at %dpx and the check renders %s: it cannot see the field"
        % (width, cdi.DEFAULT_VIEWPORTS))
    inv = di.load()
    field = inv.element("Search field")
    assert any(a.kind == "visible" and a.expected == "1" and a.when == ">=%d" % width
               for a in field.assertions), "the Search field row must assert it is shown from %dpx" % width


def test_the_content_column_header_and_footer_share_the_page_width():
    """The Page width row measures the header and the footer on the built pages; the content
    column cannot be named there because mock harnesses restyle `.inner`. This pins the column to
    the same width in the stylesheet, and the earlier widths to the pages that keep them."""
    (expected,) = [a.expected for a in di.load().element("Page width").assertions if a.kind == "max-width"]
    css = SYSTEM_CSS.read_text(encoding="utf-8")

    def max_width(selector: str) -> str:
        m = re.search(r"(?m)^%s \{[^}]*?max-width: (\d+px);" % re.escape(selector), css)
        assert m, "system.css has no max-width rule starting with %r" % selector
        return m.group(1)

    for sel in (".inner", ".header-in", ".footer-in", ".shell"):
        assert max_width(sel) == expected, "%s is %s, the Page width is %s" % (sel, max_width(sel), expected)
    assert max_width(".fx.legacy-width .inner") == "680px"
    assert max_width(".fx.legacy-width .header-in, .fx.legacy-width .footer-in") == "1100px"
    pages = SYSTEM_CSS.parent.parent / "pages"
    keep = sorted(p.relative_to(pages).as_posix() for p in pages.rglob("*.astro")
                  if re.search(r"\blegacyWidth\b", p.read_text(encoding="utf-8")))
    assert keep == [], keep


def test_a_width_condition_limits_an_assertion_to_its_viewports(tmp_path):
    row = "| X | `.x` | r | `visible=1 [>=1010px]; visible=0 [<1010px]; one-line` | ruled | #1 |\n"
    wide, narrow, always = di.load(_doc(tmp_path, GOOD_ROW + row)).element("X").assertions
    assert (wide.when, narrow.when, always.when) == (">=1010", "<1010", "")
    assert [di.applies(wide, v) for v in (375, 700, 1009, 1010, 1280)] == [False, False, False, True, True]
    assert [di.applies(narrow, v) for v in (375, 700, 1009, 1010, 1280)] == [True, True, True, False, False]
    assert all(di.applies(always, v) for v in (375, 700, 1010))
    assert "[>=1010px]" in di.compare(wide, 0, {}), "a failure names the condition it was measured under"


def test_a_page_expects_an_element_only_at_the_widths_it_names():
    page = di.Page("p", "built", "site_v2/dist", "en/index.html", "path",
                   ("Block heading", "Search field", "Search button"), ("", ">=1010", "<1010"))
    assert page.expected_at(375) == ("Block heading", "Search button")
    assert page.expected_at(1010) == ("Block heading", "Search field")
    built = [p for p in di.load().pages if p.kind == "built"]
    assert built and all("Search field" in p.expected_at(1010) and "Search button" in p.expected_at(375)
                         for p in built), "every built page carries the site header, so each must show its search"


# ---------------------------------------------------------------- the parser

def test_the_committed_inventory_parses_and_is_not_empty():
    inv = di.load()
    assert len(inv.elements) >= 30, "the inventory lost rows: %d" % len(inv.elements)
    assert sum(len(e.assertions) for e in inv.elements) >= 80
    assert len(inv.pages) >= 10
    assert {p.kind for p in inv.pages} == {"built", "mock"}
    proposed = [e.name for e in inv.elements if e.status == "proposed"]
    assert proposed == ["Breadcrumb current page"], (
        "a proposed row is measured but never fails: %s" % proposed)
    names = {e.name for e in inv.elements}
    for p in inv.pages:
        assert set(p.expect) <= names


def test_the_committed_inventory_names_every_generator_of_record():
    inv = di.load()
    sources = {p.source.split()[0] for p in inv.pages if p.kind == "mock"}
    for gen in ("gen_overview_after_teams.py", "gen_competition_matchdays.py", "gen_competition_teams.py", "gen_home_with_rules.py"):
        assert gen in sources, gen


@pytest.mark.parametrize("row, fragment", [
    ("| X | `.x` | r | `font-size=13` | ruled | #1 |\n", "px value"),
    ("| X | `.x` | r | `max-width=960` | ruled | #1 |\n", "px value"),
    ("| X | `.x` | r | `gap(nxt)=14px` | ruled | #1 |\n", "unknown key"),
    ("| X | `.x` | r | `colour=ink` | ruled | #1 |\n", "unknown key"),
    ("| X | `.x` | r | `color=pink` | ruled | #1 |\n", "colour"),
    ("| X | `.x` | r | `hover(opacity)=1` | ruled | #1 |\n", "unknown property"),
    ("| X | `.x` | r | `stripe=ink from two` | ruled | #1 |\n", "stripe expects"),
    ("| X | `.x` | r | `left-edge` | ruled | #1 |\n", "needs a value"),
    ("| X | `.x` | r | `visible=1 [>1010px]` | ruled | #1 |\n", "width condition"),
    ("| X | `.x` | r | `visible=1 [>=1010]` | ruled | #1 |\n", "width condition"),
    ("| X | `.x` | r | `visible=1 >=1010px]` | ruled | #1 |\n", "width condition"),
    ("| X | `.x` | r | `[>=1010px]` | ruled | #1 |\n", "width condition"),
    ("| X | `.x` | r | `font-size=13px` | maybe | #1 |\n", "status"),
    ("| X |  | r | `font-size=13px` | ruled | #1 |\n", "without a name or a selector"),
    (GOOD_ROW + GOOD_ROW, "listed twice"),
])
def test_the_parser_fails_closed_on_a_bad_element_row(tmp_path, row, fragment):
    with pytest.raises(di.InventoryError, match=fragment):
        di.load(_doc(tmp_path, row))


def test_a_max_width_assertion_compares_the_computed_px_value():
    (a,) = di.parse_measured("max-width=960px")
    assert di.compare(a, "960px", {}) is None
    assert "measured 680px" in di.compare(a, "680px", {})
    assert "measured none" in di.compare(a, "none", {})


def test_the_parser_fails_closed_on_a_renamed_column(tmp_path):
    doc = _doc(tmp_path, GOOD_ROW)
    doc.write_text(doc.read_text(encoding="utf-8").replace("| Measured as |", "| Measured |"), encoding="utf-8")
    with pytest.raises(di.InventoryError, match="columns must be"):
        di.load(doc)


@pytest.mark.parametrize("pages, fragment", [
    ("\n## Pages\n\n| Page | Kind | Source | URL | FI | Expect |\n|---|---|---|---|---|---|\n| h | page | `g.py` | `h.html` | toggle | |\n", "kind must be"),
    ("\n## Pages\n\n| Page | Kind | Source | URL | FI | Expect |\n|---|---|---|---|---|---|\n| h | mock | `g.py` | `h.html` | finnish | |\n", "FI must be"),
    ("\n## Pages\n\n| Page | Kind | Source | URL | FI | Expect |\n|---|---|---|---|---|---|\n| h | mock | `g.py` | `h.html` | toggle | Picker |\n", "does not name"),
    ("\n## Pages\n\n| Page | Kind | Source | URL | FI | Expect |\n|---|---|---|---|---|---|\n| h | mock | `g.py` | `h.html` | toggle | Block heading [>1010px] |\n", "width condition"),
    ("\n## Pages\n\n| Page | Kind | Source | URL | FI | Expect |\n|---|---|---|---|---|---|\n", "no rows"),
    ("\n", "needs a '## Elements' table and a '## Pages' table"),
])
def test_the_parser_fails_closed_on_a_bad_page_row(tmp_path, pages, fragment):
    with pytest.raises(di.InventoryError, match=fragment):
        di.load(_doc(tmp_path, GOOD_ROW, pages))


def test_class_tokens_are_every_class_in_every_selector(tmp_path):
    rows = GOOD_ROW + "| Row | `a.ctab-row, .fxrow .when .t` | r | `fits` | ruled | #1 |\n"
    inv = di.load(_doc(tmp_path, rows))
    assert di.class_tokens(inv.elements) == {"sechead", "eyebrow", "ctab-row", "fxrow", "when", "t"}


# ---------------------------------------------------------------- colours and comparisons

TOKENS = {"ink": "#f1f3f7", "accent": "#3bb072", "sunk": "#1c1f27", "muted": "#8b9099"}


def test_computed_colours_parse_in_every_form_chromium_uses():
    assert di.parse_css_color("rgb(59, 176, 114)") == (59, 176, 114, 1.0)
    assert di.parse_css_color("rgba(0, 0, 0, 0)") == (0, 0, 0, 0.0)
    r, g, b, a = di.parse_css_color("color(srgb 0.945098 0.952941 0.968627 / 0.11)")
    assert (round(r), round(g), round(b), a) == (241, 243, 247, 0.11)
    assert di.parse_css_color("#3bb072") == (59, 176, 114, 1.0)
    with pytest.raises(ValueError):
        di.parse_css_color("hsl(1 2% 3%)")


def test_a_tint_matches_its_token_at_its_alpha_and_nothing_else():
    a = di.Assertion("hover", "background-color", "ink@11%", "hover(background-color)=ink@11%")
    assert di.compare(a, "color(srgb 0.945098 0.952941 0.968627 / 0.11)", TOKENS) is None
    assert "measured" in di.compare(a, "color(srgb 0.945098 0.952941 0.968627 / 0.05)", TOKENS)
    assert "measured" in di.compare(a, "rgb(22, 25, 32)", TOKENS)
    solid = di.Assertion("color", None, "accent", "color=accent")
    assert di.compare(solid, "rgb(59, 176, 114)", TOKENS) is None
    assert di.compare(solid, "rgb(241, 243, 247)", TOKENS)


def test_comparisons_name_the_expected_and_the_measured():
    assert di.compare(di.Assertion("font-size", None, "13px", "font-size=13px"), "11px", TOKENS) == "expected font-size=13px · measured 11px"
    assert di.compare(di.Assertion("font-size", None, "13px", "font-size=13px"), "13.2px", TOKENS) is None
    assert di.compare(di.Assertion("gap(next)", None, "14px", "gap(next)=14px"), 23.0, TOKENS) == "expected gap(next)=14px · measured 23.0px"
    assert di.compare(di.Assertion("gap(next)", None, "14px", "gap(next)=14px"), 14.8, TOKENS) is None
    assert di.compare(di.Assertion("fits", None, "", "fits"), (348, 343), TOKENS) == "expected fits · measured scrollWidth 348 > clientWidth 343"
    assert di.compare(di.Assertion("one-line", None, "", "one-line"), 2, TOKENS) == "expected one-line · measured 2 lines"
    assert di.compare(di.Assertion("whole-words", None, "", "whole-words"), (74.0, 66), TOKENS) == "expected whole-words · longest word 74px in a 66px box"
    assert di.compare(di.Assertion("whole-words", None, "", "whole-words"), (66.6, 66), TOKENS) is None
    assert di.compare(di.Assertion("fit-marked", None, "", "fit-marked"), False, TOKENS) == "expected fit-marked · the block carries neither fit-one nor fit-two"
    assert di.compare(di.Assertion("fit-marked", None, "", "fit-marked"), True, TOKENS) is None
    assert di.compare(di.Assertion("left-edge", None, "section", "left-edge=section"), 8.0, TOKENS).endswith("off the section's left")
    assert di.compare(di.Assertion("tracks", None, "head", "tracks=head"), ("32px 200px", "32px 180px"), TOKENS).startswith("expected tracks=head")
    assert di.compare(di.Assertion("visible", None, "1", "visible=1"), 3, TOKENS) == "expected visible=1 · measured 3"
    assert di.compare(di.Assertion("visible", None, "1", "visible=1"), 1, TOKENS) is None
    assert di.compare(di.Assertion("min-box", None, "34px", "min-box=34px"), (20.0, 20.0), TOKENS) == "expected min-box=34px · measured 20×20"
    assert di.compare(di.Assertion("min-box", None, "34px", "min-box=34px"), (34.0, 33.6), TOKENS) is None
    stripe = di.Assertion("stripe", None, "ink@5% from 2", "stripe=ink@5% from 2")
    plain, tint = "rgba(0, 0, 0, 0)", "color(srgb 0.945098 0.952941 0.968627 / 0.05)"
    assert di.compare(stripe, [plain, tint, plain, tint], TOKENS) is None
    assert "row 1" in di.compare(stripe, [tint, plain, tint], TOKENS)
    assert "row 2" in di.compare(stripe, [plain, plain, plain], TOKENS)


# ---------------------------------------------------------------- the lint

def _tree(tmp_path: Path) -> tuple[Path, Path]:
    site = tmp_path / "site_v2" / "src"
    (site / "styles").mkdir(parents=True)
    (site / "styles" / "system.css").write_text(".sechead { margin: 0 }", encoding="utf-8")
    mocks = tmp_path / "design-mocks"
    mocks.mkdir()
    return site, mocks


def test_the_lint_flags_a_style_block_and_an_inline_style_on_an_inventory_class(tmp_path):
    site, mocks = _tree(tmp_path)
    (site / "A.astro").write_text('<div class="sechead"><span class="eyebrow" style="margin-top:14px">x</span></div>\n'
                                  "<style>\n.card { color: red }\n@media (hover: hover) { .sechead:hover { color: red } }\n</style>\n", encoding="utf-8")
    (site / "B.astro").write_text('<div class="fill" style={`width:${w}%`}></div>\n', encoding="utf-8")
    (site / "C.astro").write_text('<div class:list={["frow", on && "x"]} style="top:0"></div>\n', encoding="utf-8")
    findings, scanned = lint.run(di.DOC, site, mocks)
    joined = "\n".join(findings)
    assert "A.astro:1 · style= on <span> · eyebrow" in joined
    assert "A.astro:4 · <style> rule `.sechead:hover` · sechead" in joined
    assert "C.astro:1 · style= on <div> · frow" in joined
    assert "B.astro" not in joined, "a data-driven width on a non-inventory class passes"
    assert len(findings) == 3


def test_the_lint_flags_another_stylesheet_but_not_system_css(tmp_path):
    site, mocks = _tree(tmp_path)
    (site / "styles" / "page.css").write_text(".ctab-row { border: 0 }\n.other { color: red }\n", encoding="utf-8")
    findings, _ = lint.run(di.DOC, site, mocks)
    assert findings == ["site_v2/src/styles/page.css:1 · stylesheet rule `.ctab-row` · ctab-row"]


def test_the_lint_reads_a_mocks_css_strings_and_the_modules_it_imports(tmp_path):
    site, mocks = _tree(tmp_path)
    (mocks / "gen_home.py").write_text('import rows\nCSS = """\n.stage { max-width: 375px }\n.sechead .eyebrow { font-size: 13px; }\n"""\n', encoding="utf-8")
    (mocks / "rows.py").write_text('ROW_CSS = """\n.fxrow .side .nm { white-space: normal; }\n"""\n', encoding="utf-8")
    (mocks / "gen_diagram.py").write_text('CSS = """\n.sub { color: red; }\n"""\n', encoding="utf-8")
    (mocks / "check_x.py").write_text('BROKEN = """\n.ctab-row { border-bottom: 1px }\n"""\n', encoding="utf-8")
    rows = GOOD_ROW + "| Match row name | `.fxrow .side .nm` | wraps | `white-space=normal` | ruled | #50 |\n"
    findings, _ = lint.run(_doc(tmp_path, rows), site, mocks)
    joined = "\n".join(findings)
    assert "gen_home.py:4 · CSS string rule `.sechead .eyebrow`" in joined
    assert "rows.py:2 · CSS string rule `.fxrow .side .nm`" in joined
    assert "check_x.py" not in joined, "a check's reconstructed-defect string is not a page"
    assert len(findings) == 2


def test_the_lint_is_green_on_the_tree():
    findings, scanned = lint.run(di.DOC)
    assert findings == []
    assert scanned >= 40


def test_the_lint_lints_only_the_generators_the_pages_table_names(tmp_path):
    inv = di.load()
    named = {p.source.split()[0] for p in inv.pages if p.kind == "mock"}
    linted = {p.name for p in lint.mock_modules(inv)}
    assert named <= linted
    assert "rows.py" in linted and "interaction.py" in linted, "the shared row modules are imported by every page"
    assert "gen_navmap.py" not in linted and "gen_sitemap.py" not in linted, "a diagram is not a page"
    counted = {p.name for p in lint.unlisted_mock_modules(inv)}
    assert not counted & linted
    assert {"gen_match_page.py", "gen_team_mock.py", "gen_navmap.py"} <= counted, "every other generator is counted"


# ---------------------------------------------------------------- the static gap counts

def test_the_static_counts_match_the_baseline():
    measured = lint.counts(di.DOC)
    off = di.compare_counts(measured, di.load_baseline()["static"])
    assert off == [], "\n".join(off)


def test_a_count_off_its_pin_fails_in_both_directions():
    off = di.compare_counts({"g": {"a": 3, "b": 1}}, {"g": {"a": 2, "b": 1, "c": 4}})
    assert off == ["count rose · g · a · 3, baseline 2", "count fell · g · c · 0, baseline 4: lower the baseline"]
    assert di.compare_counts({"g": {"a": 1}}, {"g": {"a": 1}}) == []


def test_the_lint_exits_red_on_a_count_off_its_pin(tmp_path, capsys):
    baseline = di.load_baseline()
    assert lint.main([]) == 0
    capsys.readouterr()
    baseline["static"]["literal_text"]["site_v2/src/pages/index.astro"] -= 1
    lowered = tmp_path / "baseline.json"
    lowered.write_text(json.dumps(baseline), encoding="utf-8")
    assert lint.main(["--baseline", str(lowered)]) == 1
    assert "FAIL  count rose · literal_text · site_v2/src/pages/index.astro · 2, baseline 1" in capsys.readouterr().out


def test_the_rendered_counts_compare_only_on_a_full_run_on_the_baselines_platform():
    import check_design_inventory as cdi  # noqa: PLC0415
    pinned = {"platform": "linux", "pages": {"Home": {"split": 3, "classes": 23}}}
    measured = {"Home": {"scroll": 0, "overflow": 0, "split": 4, "overlap": 0, "classes": 23}}
    note, off = cdi.compare_rendered(measured, pinned, True, "linux")
    assert note == "" and off == ["count rose · Home · split · 4, baseline 3"]
    measured["Home"]["split"] = 3
    assert cdi.compare_rendered(measured, pinned, True, "linux") == ("", [])
    measured["Home"]["classes"] = 22
    assert cdi.compare_rendered(measured, pinned, True, "linux")[1] == [
        "count fell · Home · classes · 22, baseline 23: lower the baseline"]
    assert cdi.compare_rendered(measured, pinned, True, "win32") == (
        "the baseline is measured on linux, this run on win32", [])
    assert cdi.compare_rendered(measured, pinned, False, "linux") == ("a narrower run than the baseline's", [])


def test_a_run_is_compared_only_over_the_widths_and_languages_its_baseline_names():
    import check_design_inventory as cdi  # noqa: PLC0415
    every = (list(cdi.DEFAULT_VIEWPORTS), list(cdi.DEFAULT_LANGS))
    assert cdi.in_baseline_scope({}, *every)
    assert not cdi.in_baseline_scope({}, [280, 1010], ["de"])
    quick = {"viewports": [280, 1010], "langs": ["de"]}
    assert cdi.in_baseline_scope(quick, [1010, 280], ["de"])
    assert not cdi.in_baseline_scope(quick, *every)
    assert not cdi.in_baseline_scope(quick, [280, 1010], ["de", "en"])
    assert not cdi.in_baseline_scope(quick, [280], ["de"])


def test_the_merge_request_run_names_the_scope_of_its_pin_file():
    quick = di.load_baseline(REPO / "tests" / "fixtures" / "design_inventory" / "baseline_quick.json")
    ci = (REPO / ".gitlab-ci.yml").read_text(encoding="utf-8")
    import check_design_inventory as cdi  # noqa: PLC0415
    flags = "--viewports %s --langs %s --baseline tests/fixtures/design_inventory/baseline_quick.json" % (
        ",".join(str(v) for v in quick["viewports"]), ",".join(quick["langs"]))
    step = re.search(r'SCOPE=""\n\s*if \[ "\$CI_PIPELINE_SOURCE" = "merge_request_event" \]; then\n(.*?)\n\s*fi\n(.*?\$SCOPE)',
                     ci, re.S)
    assert step, "validate:ui no longer sets the quick scope only on a merge request pipeline"
    assert flags in step.group(1)
    assert "--viewports" not in step.group(2) and "--langs" not in step.group(2) and "--baseline" not in step.group(2), (
        "the unconditional design check run must read no scope, so main renders every width and language")
    assert quick["rendered"]["platform"] == "linux"
    assert set(quick["viewports"]) <= set(cdi.DEFAULT_VIEWPORTS) and set(quick["langs"]) <= set(cdi.DEFAULT_LANGS)


def test_the_static_counts_find_each_gap(tmp_path):
    site, mocks = _tree(tmp_path)
    (site / "styles" / "system.css").write_text(
        "/* hyphens: auto */\n.a { hyphens: auto; overflow-wrap: anywhere; }\n.b { text-overflow: ellipsis; word-break: break-all; }\n"
        ".c { overflow-wrap: break-word; -webkit-line-clamp: 2; overflow-wrap: normal; }\n"
        "@media (min-width: 700px) { .a { color: red } }\n@media (max-width: 699.98px) { .a { color: red } }\n"
        "@container (min-width: 700px) { .a { color: red } }\n@media (hover: hover) { .a { color: red } }\n", encoding="utf-8")
    (site / "styles" / "page.css").write_text(".x { color: red }\n", encoding="utf-8")
    (site / "A.astro").write_text(
        '---\nconst label = "Not template text";\n---\n'
        '<header class="brand">Brand<span class="iq">Name</span></header>\n'
        '<!-- a comment -->\n<p>{t(lang, "key")} · {n}</p>\n'
        '{items.map((x) => <li title="Literal title" alt={x.alt}>Item {x.n}</li>)}\n'
        '<input placeholder="Search" aria-label="not shown" />\n'
        '<div style={`width:${w}%`}></div>\n<style>\n.y { text-overflow: ellipsis; }\n</style>\n'
        '<script>\nel.style.width = "1px"; if (el.style.width == "1px") {}\n</script>\n', encoding="utf-8")
    (site / "fit.mjs").write_text("copy.style.cssText = 'x';\nnode.setAttribute('style', 'x');\n", encoding="utf-8")
    (site / "fit.test.mjs").write_text("copy.style.cssText = 'x';\n", encoding="utf-8")
    (mocks / "gen_home.py").write_text('CSS = """\n.stage { max-width: 375px }\n"""\n', encoding="utf-8")
    (mocks / "gen_other.py").write_text('import shared\n', encoding="utf-8")
    (mocks / "shared.py").write_text('CSS = """\n.sechead .eyebrow { color: red; }\n.sechead { color: red; }\n"""\n', encoding="utf-8")
    c = lint.counts(_doc(tmp_path, GOOD_ROW), site, mocks)
    assert c["mock_css"] == {"design-mocks/shared.py": 2}
    assert c["css_outside_system_css"] == {"site_v2/src/A.astro": 3, "site_v2/src/fit.mjs": 2, "site_v2/src/styles/page.css": 1}
    assert c["width_rules"] == {"700px": 2, "699.98px": 1}
    assert c["banned_properties"] == {"site_v2/src/styles/system.css": 6, "site_v2/src/A.astro": 1}
    found = lint.literal_text((site / "A.astro").read_text(encoding="utf-8"))
    assert [v for _line, v in found] == ["Brand", "Name", "Literal title", "Item", "Search"], found
    assert found[0][0] == 4
    assert c["literal_text"] == {"site_v2/src/A.astro": 5}


# ---------------------------------------------------------------- the measured check: RED proof

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


def _run_check(tmp_path: Path, name: str) -> tuple[int, str]:
    folder = tmp_path / "pages"
    folder.mkdir(exist_ok=True)
    shutil.copy(FIXTURES / ("%s.html" % name), folder / ("%s.html" % name))
    shutil.copy(SYSTEM_CSS, folder / "system.css")
    # The fixtures reconstruct the competition page as it was ruled, at the widths it was ruled at.
    proc = subprocess.run(
        [sys.executable, str(REPO / "scripts" / "check_design_inventory.py"), "--no-mocks", "--no-built",
         "--page", "%s=%s" % (name, folder / ("%s.html" % name)), "--langs", "en", "--viewports", "375,700,1010"],
        capture_output=True, text=True, encoding="utf-8", env={**os.environ, "PYTHONIOENCODING": "utf-8"},
    )
    return proc.returncode, proc.stdout + proc.stderr


@needs_browser
def test_the_check_is_green_on_the_page_as_ruled(tmp_path):
    code, out = _run_check(tmp_path, "green")
    assert code == 0, out
    assert "0 failures" in out


@needs_browser
def test_the_check_goes_red_on_the_defects_it_exists_for(tmp_path):
    code, out = _run_check(tmp_path, "red")
    assert code == 1, out
    failed = {line.split(" · ")[3].split(" [")[0] for line in out.splitlines() if line.startswith("FAIL")}
    assert failed == {"Block heading", "Block heading gap", "Row link", "Table row", "Tab bar", "Fact row value",
                      "Matchday picker", "Picker arrow", "Search field", "Search button"}, failed
    assert "expected visible=1 [>=1010px] · measured 0" in out
    assert "expected visible=0 [>=1010px] · measured 1" in out
    assert "measured 11px" in out
    assert "measured 49.0px" in out
    assert "expected visible=1 · measured 3" in out
    assert "measured 20×20" in out
    assert "scrollWidth" in out
    assert "row 1 measured" in out


@needs_browser
def test_the_gap_counts_count_each_defect_once(tmp_path):
    folder = tmp_path / "pages"
    folder.mkdir()
    shutil.copy(FIXTURES / "counts_red.html", folder / "counts_red.html")
    proc = subprocess.run(
        [sys.executable, str(REPO / "scripts" / "check_design_inventory.py"), "--no-mocks", "--no-built",
         "--page", "red=%s" % (folder / "counts_red.html"), "--langs", "en", "--viewports", "320"],
        capture_output=True, text=True, encoding="utf-8", env={**os.environ, "PYTHONIOENCODING": "utf-8"},
    )
    out = proc.stdout + proc.stderr
    assert "COUNT red · scroll 1 · overflow 2 · split 1 · overlap 2 · classes 7" in out, out
    assert "not compared: a narrower run than the baseline's" in out, out


@needs_browser
def test_a_class_the_component_registry_lists_is_not_counted_as_unknown(tmp_path):
    page = tmp_path / "probe.html"
    page.write_text('<!doctype html><html lang="en"><body><span class="zz-listed">a</span>'
                    '<span class="zz-unlisted">b</span><span class="crest">c</span></body></html>', encoding="utf-8")
    registry = tmp_path / "components.yml"
    registry.write_text("components:\n  probe:\n    parts:\n      listed: {class: zz-listed, gap: mock-css}\n",
                        encoding="utf-8")

    def classes(*extra):
        art = tmp_path / ("art" + str(len(extra)))
        subprocess.run(
            [sys.executable, str(REPO / "scripts" / "check_design_inventory.py"), "--no-mocks", "--no-built",
             "--page", "probe=%s" % page, "--langs", "en", "--viewports", "320", "--artifacts", str(art), *extra],
            capture_output=True, text=True, encoding="utf-8", env={**os.environ, "PYTHONIOENCODING": "utf-8"},
        )
        return json.loads((art / "counts.json").read_text(encoding="utf-8"))["classes"]["probe"]

    assert classes() == ["zz-listed", "zz-unlisted"]
    assert classes("--registry", str(registry)) == ["crest", "zz-unlisted"]


@needs_browser
def test_the_gap_counts_open_every_tab_and_count_a_shared_defect_once(tmp_path):
    folder = tmp_path / "pages"
    folder.mkdir()
    shutil.copy(FIXTURES / "counts_tabs.html", folder / "counts_tabs.html")
    proc = subprocess.run(
        [sys.executable, str(REPO / "scripts" / "check_design_inventory.py"), "--no-mocks", "--no-built",
         "--page", "tabs=%s" % (folder / "counts_tabs.html"), "--langs", "en", "--viewports", "320"],
        capture_output=True, text=True, encoding="utf-8", env={**os.environ, "PYTHONIOENCODING": "utf-8"},
    )
    out = proc.stdout + proc.stderr
    assert "COUNT tabs · scroll 0 · overflow 2 · split 1 · overlap 0" in out, out
    assert "a Tab bar with no tab to open" not in out, out


@needs_browser
def test_a_tab_bar_with_no_tab_to_open_fails_instead_of_measuring_one_tab(tmp_path):
    folder = tmp_path / "pages"
    folder.mkdir()
    (folder / "bar.html").write_text(
        '<!doctype html><html lang="en"><head><meta charset="utf-8"><title>t</title></head><body>'
        '<nav class="tabs"><label class="tab">Overview</label><label class="tab">Matches</label></nav>'
        "<p>One tab only</p></body></html>", encoding="utf-8")
    proc = subprocess.run(
        [sys.executable, str(REPO / "scripts" / "check_design_inventory.py"), "--no-mocks", "--no-built",
         "--page", "bar=%s" % (folder / "bar.html"), "--langs", "en", "--viewports", "320"],
        capture_output=True, text=True, encoding="utf-8", env={**os.environ, "PYTHONIOENCODING": "utf-8"},
    )
    out = proc.stdout + proc.stderr
    assert "FAIL  bar · 320 · en · (page) · a Tab bar with no tab to open" in out, out
    assert proc.returncode == 1, out


def test_a_page_is_judged_across_its_tabs_and_a_failure_in_every_tab_counts_once():
    import check_design_inventory as cdi  # noqa: PLC0415

    size = di.Assertion(kind="font-size", prop=None, expected="14px", raw="font-size=14px")
    shown = di.Assertion(kind="visible", prop=None, expected="1", raw="visible=1")
    inv = di.Inventory((di.Element("Shared", ".shared", "", (size,), "ruled", ""),
                        di.Element("Tabbed", ".tabbed", "", (shown,), "ruled", "")), ())
    page = di.Page("tabs", "built", "", "", "", ("Tabbed",))

    def tab(tabbed_open):
        match = {"style": {"font-size": "13px"}, "rect": [0, 0, 10, 10]}
        return {"tokens": {}, "elements": {
            "Shared": {"matches": [match], "inDom": 1},
            "Tabbed": {"matches": [match] if tabbed_open else [], "inDom": 1}}}

    class Page:
        def __init__(self, states):
            self.states = iter(states)

        def evaluate(self, _js, _arg=None):
            return json.dumps(next(self.states))

    failures, acc = [], {"seen": set(), "visible": {}, "total": 0, "found": set()}
    pw = Page([tab(False), tab(True)])
    for _ in range(2):
        cdi.measure_page(pw, inv, {}, page, 375, "en", failures, acc)
    cdi.finish_page(acc, page, 375, "en", failures)
    assert [f.element for f in failures] == ["Shared [.shared #1]"], [f.line() for f in failures]

    failures, acc = [], {"seen": set(), "visible": {}, "total": 0, "found": set()}
    pw = Page([tab(False), tab(False)])
    for _ in range(2):
        cdi.measure_page(pw, inv, {}, page, 375, "en", failures, acc)
    cdi.finish_page(acc, page, 375, "en", failures)
    assert sorted(f.detail.split(" · ")[0] for f in failures if f.element == "Tabbed") == [
        "expected on this page", "expected visible=1"], [f.line() for f in failures]


def test_the_full_baseline_names_no_scope():
    full = di.load_baseline()
    assert "viewports" not in full and "langs" not in full, (
        "main's run reads baseline.json over every width and language; a scope named here would "
        "make it a narrower run that compares nothing")


@pytest.mark.parametrize("name", ["baseline.json", "baseline_quick.json"])
def test_the_baseline_names_only_pages_the_check_renders_and_counts_it_knows(name):
    baseline = di.load_baseline(REPO / "tests" / "fixtures" / "design_inventory" / name)
    rendered = baseline["rendered"]
    assert rendered["platform"] == "linux", "the baseline is measured in validate:ui's browser image"
    names = {p.name for p in di.load().pages}
    import check_design_inventory as cdi  # noqa: PLC0415
    for page, by_count in rendered["pages"].items():
        assert page in names or page.endswith(".html"), page
        assert all(k in cdi.COUNTS or k.startswith(cdi.MISS) for k in by_count), (page, by_count)
        assert all(n > 0 for n in by_count.values()), (page, by_count)
    assert set(baseline["coverage"]) <= set(cdi.COVERAGE)
    assert set(baseline["coverage"].get("generator fails", {})) <= set(cdi.generators())


def test_every_mock_row_names_a_generator_on_disk():
    import check_design_inventory as cdi  # noqa: PLC0415
    gens = set(cdi.generators())
    for p in di.load().pages:
        if p.kind == "mock":
            assert p.source in gens, (p.name, p.source)


def test_the_check_owns_every_built_file_and_counts_the_rest(tmp_path):
    import check_design_inventory as cdi  # noqa: PLC0415
    dist = tmp_path / "dist"
    for rel in ("index.html", "en/index.html", "en/teams/a/index.html", "en/teams/b/index.html", "en/players/p/index.html"):
        (dist / rel).parent.mkdir(parents=True, exist_ok=True)
        (dist / rel).write_text("<p>x</p>", encoding="utf-8")
    pages = [di.Page("Home", "built", "site_v2/dist", "en/index.html", "path", ()),
             di.Page("Team page", "built", "site_v2/dist", "en/teams/*/index.html", "path", ()),
             di.Page("Team a", "built", "site_v2/dist", "en/teams/a/index.html", "path", ())]
    run = cdi.plan(pages, ["en"], dist, {}, {}, every_file=True)
    assert {path: p.name for p, _lang, _root, path in run.targets} == {
        "index.html": "index.html", "en/index.html": "Home", "en/teams/a/index.html": "Team a",
        "en/teams/b/index.html": "Team page", "en/players/p/index.html": "en/players/p/index.html"}
    assert run.coverage == {"page with no row": {"en/players/p/index.html": 1, "index.html": 1}}
    assert run.failures == []
    root = di.Page("Root", "built", "site_v2/dist", "index.html", "path", ())
    run = cdi.plan(pages + [root], ["en", "de", "fi"], dist, {}, {}, every_file=True)
    assert [f.detail for f in run.failures if f.page == "Root"] == [], "a row matching one file in every language is not a clash"
    pages.append(di.Page("Other", "built", "site_v2/dist", "en/*/b/index.html", "path", ()))
    pages.append(di.Page("Team a again", "built", "site_v2/dist", "en/teams/a/index.html", "path", ()))
    run = cdi.plan(pages, ["en"], dist, {}, {}, every_file=True)
    assert [f.detail for f in run.failures] == ["en/teams/b/index.html is also matched by Team page",
                                                "en/teams/a/index.html is also matched by Team a"]


def test_every_generator_is_run_and_one_that_fails_or_writes_nothing_is_counted(tmp_path):
    import check_design_inventory as cdi  # noqa: PLC0415
    mocks = tmp_path / "mocks"
    mocks.mkdir()
    (mocks / "gen_ok.py").write_text(
        "import pathlib, sys\nd = pathlib.Path(sys.argv[2])\n(d / 'a.html').write_text('<p>a</p>')\n"
        "(d / 'b.html').write_text('<label for=\"t-fi\"></label>')\n", encoding="utf-8")
    (mocks / "gen_bad.py").write_text("raise SystemExit('drift')\n", encoding="utf-8")
    (mocks / "gen_silent.py").write_text("pass\n", encoding="utf-8")
    (mocks / "helper.py").write_text("raise SystemExit('not a generator')\n", encoding="utf-8")
    assert cdi.generators(mocks) == ["gen_bad.py", "gen_ok.py", "gen_silent.py"]
    out, failed = cdi.run_generators(cdi.generators(mocks), tmp_path / "out", mocks)
    assert set(out) == {"gen_ok.py"}
    assert failed == {"gen_bad.py": "exit 1: drift", "gen_silent.py": "wrote no page into --out DIR"}
    pages = [di.Page("a page", "mock", "gen_ok.py", "a.html", "toggle", ()),
             di.Page("gone", "mock", "gen_ok.py", "c.html", "toggle", ())]
    run = cdi.plan(pages, ["en", "de", "fi"], None, out, failed, every_file=True)
    assert {(p.name, lang) for p, lang, _root, _path in run.targets} == {
        ("a page", "en"), ("a page", "fi"), ("gen_ok.py/b.html", "en"), ("gen_ok.py/b.html", "fi")}
    assert run.coverage == {"generator fails": {"gen_bad.py": 1, "gen_silent.py": 1},
                            "mock page with no row": {"gen_ok.py/b.html": 1},
                            "language missing": {"a page": 1, "gen_ok.py/b.html": 1}}
    assert [f.detail for f in run.failures] == ["gen_ok.py wrote no c.html"]


@needs_browser
def test_a_coverage_gap_or_a_miss_off_its_pin_fails_a_full_run(tmp_path):
    doc = _doc(tmp_path, GOOD_ROW, "\n## Pages\n\n| Page | Kind | Source | URL | FI | Expect |\n|---|---|---|---|---|---|\n"
               "| Home | built | `site_v2/dist` | `en/index.html` | path | Block heading |\n")
    dist = tmp_path / "dist"
    for rel in ("en/index.html", "de/index.html", "fi/index.html", "en/extra/index.html"):
        (dist / rel).parent.mkdir(parents=True, exist_ok=True)
        (dist / rel).write_text('<!doctype html><body><div class="sechead"><span class="eyebrow">Block</span></div></body>',
                                encoding="utf-8")
    mocks = tmp_path / "mocks"
    mocks.mkdir()
    (mocks / "gen_bad.py").write_text("raise SystemExit('drift')\n", encoding="utf-8")

    def run(rendered: dict, coverage: dict, n: int) -> tuple[int, str, dict]:
        baseline, artifacts = tmp_path / ("baseline%d.json" % n), tmp_path / ("artifacts%d" % n)
        baseline.write_text(json.dumps({"static": {}, "coverage": coverage,
                                        "rendered": {"platform": sys.platform, "pages": rendered}}), encoding="utf-8")
        proc = subprocess.run(
            [sys.executable, str(REPO / "scripts" / "check_design_inventory.py"), "--inventory", str(doc),
             "--dist", str(dist), "--mocks", str(mocks), "--baseline", str(baseline), "--artifacts", str(artifacts)],
            capture_output=True, text=True, encoding="utf-8", env={**os.environ, "PYTHONIOENCODING": "utf-8"})
        return proc.returncode, proc.stdout + proc.stderr, json.loads((artifacts / "counts.json").read_text(encoding="utf-8"))

    code, out, counts = run({}, {}, 1)
    assert code == 1, out
    assert "count rose · generator fails · gen_bad.py · 1, baseline 0" in out, out
    assert "count rose · page with no row · en/extra/index.html · 1, baseline 0" in out, out
    assert "INFO  gen_bad.py · 0 · - · (generator) · exit 1: drift" in out, out
    misses = counts["pages"]["Home"]["miss · Block heading"]
    assert misses > 0, counts["pages"]
    code, out, _ = run(counts["pages"], counts["coverage"], 2)
    assert code == 0, out
    counts["pages"]["Home"]["miss · Block heading"] -= 1
    code, out, _ = run(counts["pages"], counts["coverage"], 3)
    assert code == 1, out
    assert "count rose · Home · miss · Block heading · %d, baseline %d" % (misses, misses - 1) in out, out


@needs_browser
def test_a_narrower_run_is_compared_only_with_a_baseline_that_names_its_scope(tmp_path):
    doc = _doc(tmp_path, GOOD_ROW, "\n## Pages\n\n| Page | Kind | Source | URL | FI | Expect |\n|---|---|---|---|---|---|\n"
               "| Home | built | `site_v2/dist` | `en/index.html` | path | Block heading |\n")
    dist = tmp_path / "dist"
    for rel in ("en/index.html", "en/extra/index.html"):
        (dist / rel).parent.mkdir(parents=True, exist_ok=True)
        (dist / rel).write_text('<!doctype html><body><div class="sechead"><span class="eyebrow">Block</span></div></body>',
                                encoding="utf-8")
    mocks = tmp_path / "mocks"
    mocks.mkdir()

    def run(scope: dict) -> tuple[int, str]:
        baseline = tmp_path / "baseline.json"
        baseline.write_text(json.dumps({**scope, "static": {}, "coverage": {},
                                        "rendered": {"platform": sys.platform, "pages": {}}}), encoding="utf-8")
        proc = subprocess.run(
            [sys.executable, str(REPO / "scripts" / "check_design_inventory.py"), "--inventory", str(doc),
             "--dist", str(dist), "--mocks", str(mocks), "--baseline", str(baseline),
             "--viewports", "1010", "--langs", "en"],
            capture_output=True, text=True, encoding="utf-8", env={**os.environ, "PYTHONIOENCODING": "utf-8"})
        return proc.returncode, proc.stdout + proc.stderr

    code, out = run({"viewports": [1010], "langs": ["en"]})
    assert code == 1, out
    assert "count rose · page with no row · en/extra/index.html · 1, baseline 0" in out, out
    assert "not compared" not in out, out
    code, out = run({})
    assert "not compared: a narrower run than the baseline's" in out, out
    assert "count rose" not in out, out


def test_a_pin_may_not_rise_above_mains_and_a_new_entry_starts_at_zero():
    base = {"static": {"g": {"a": 2}}, "coverage": {}, "rendered": {"platform": "linux", "pages": {"Home": {"split": 3}}}}
    now = json.loads(json.dumps(base))
    now["static"]["g"]["a"] = 1
    assert di.rises(now, base) == []
    now["rendered"]["pages"]["Home"]["split"] = 4
    now["coverage"]["page with no row"] = {"en/new/index.html": 1}
    now["rendered"]["pages"]["New page"] = {"overflow": 0}
    assert di.rises(now, base) == ["coverage · page with no row · en/new/index.html · 1, main 0",
                                   "rendered · Home · split · 4, main 3"]


def _mains_baseline(name: str = "baseline.json") -> dict | None:
    """The baseline on the branch this one merges into: the MR's base in an MR pipeline, the first
    parent on any other CI pipeline, the merge base with GitLab's main on a working copy. None for
    a pin file other than baseline.json that the base does not hold yet."""
    def git(*args):
        return subprocess.run(["git", "-c", "safe.directory=*", *args], cwd=REPO, capture_output=True, text=True,
                              encoding="utf-8")

    ref = os.environ.get("CI_MERGE_REQUEST_DIFF_BASE_SHA") or ("HEAD^1" if os.environ.get("CI") else "")
    if not ref:
        remote = "gitlab/main" if git("rev-parse", "--verify", "-q", "gitlab/main").returncode == 0 else "origin/main"
        ref = git("merge-base", "HEAD", remote).stdout.strip()
    assert ref, "no base to compare the baseline with"
    path = "%s:tests/fixtures/design_inventory/%s" % (ref, name)
    proc = git("show", path)
    if proc.returncode and os.environ.get("CI"):
        # A shallow CI clone may not hold the base commit; fetch it.
        if ref == "HEAD^1":
            git("fetch", "--no-tags", "--deepen=1", "origin")
        else:
            git("fetch", "--no-tags", "--depth=1", "origin", ref)
        proc = git("show", path)
    if proc.returncode and name != "baseline.json" and re.search(r"does not exist in|exists on disk, but not in", proc.stderr):
        return None
    assert proc.returncode == 0, "main's baseline is not in this clone (%s): %s" % (ref, proc.stderr.strip())
    return json.loads(proc.stdout)


def _declared_width(rise: str) -> bool:
    """A page-CSS width pin for a breakpoint the component registry's switch set holds: a declared
    breakpoint is vocabulary, not a gap."""
    m = re.match(r"static · width_rules · ([\d.]+)px · ", rise)
    if not m:
        return False
    import yaml
    reg = yaml.safe_load((REPO / "docs" / "design" / "components.yml").read_text(encoding="utf-8"))
    width = float(m.group(1))
    declared = (float(str(w)[:-2]) for w in reg["sets"]["switch"].values())
    # A max-width query writes a declared width d as d - 0.02.
    return any(abs(width - d) < 1e-6 or abs(width - (d - 0.02)) < 1e-6 for d in declared)


def test_a_width_pin_rises_only_for_a_declared_breakpoint():
    assert _declared_width("static · width_rules · 279.98px · 1, main 0")
    assert _declared_width("static · width_rules · 340px · 2, main 1")
    assert not _declared_width("static · width_rules · 290px · 1, main 0")
    assert not _declared_width("static · width_rules · 339.6px · 1, main 0")
    assert not _declared_width("static · css_outside_system_css · site_v2/src/x.astro · 1, main 0")


def test_no_pin_rises_above_mains():
    current, base = di.load_baseline(), _mains_baseline()
    if "coverage" not in base:
        # Main's baseline predates the count over every page; this branch introduces it.
        return
    up = [r for r in di.rises(current, base) if not _declared_width(r)]
    assert up == [], "a pin rose above main's; a new gap is fixed, not pinned:\n" + "\n".join(up)


def test_no_quick_pin_rises_above_mains():
    base = _mains_baseline("baseline_quick.json")
    if base is None:
        # Main holds no quick pins yet; this branch introduces them.
        return
    current = di.load_baseline(REPO / "tests" / "fixtures" / "design_inventory" / "baseline_quick.json")
    up = di.rises(current, base)
    assert up == [], "a quick pin rose above main's; a new gap is fixed, not pinned:\n" + "\n".join(up)


def _built_page_check(tmp_path: Path, html: str) -> tuple[int, str]:
    """The check on one BUILT page whose only Expect is the header's search, at 1010px. A
    `visible=` assertion measures only what its selector finds, so removal is caught here or
    nowhere."""
    real = di.DOC.read_text(encoding="utf-8")
    tmp_path.mkdir(parents=True, exist_ok=True)
    doc = tmp_path / "block_standard.md"
    doc.write_text(real.split("\n## Pages")[0] + "\n## Pages\n\n| Page | Kind | Source | URL | FI | Expect |\n"
                   "|---|---|---|---|---|---|\n| header | built | `site_v2/dist` | `en/index.html` | path | "
                   "Search field [>=1010px], Search button [<1010px] |\n", encoding="utf-8")
    dist = tmp_path / "dist" / "en"
    dist.mkdir(parents=True)
    (dist / "index.html").write_text(html, encoding="utf-8")
    shutil.copy(SYSTEM_CSS, dist / "system.css")
    proc = subprocess.run(
        [sys.executable, str(REPO / "scripts" / "check_design_inventory.py"), "--no-mocks",
         "--inventory", str(doc), "--dist", str(tmp_path / "dist"), "--langs", "en", "--viewports", "1010"],
        capture_output=True, text=True, encoding="utf-8", env={**os.environ, "PYTHONIOENCODING": "utf-8"},
    )
    return proc.returncode, proc.stdout + proc.stderr


@needs_browser
def test_a_search_field_removed_from_the_page_fails(tmp_path):
    green = (FIXTURES / "green.html").read_text(encoding="utf-8")
    code, out = _built_page_check(tmp_path, green)
    assert code == 0, out
    removed = re.sub(r'<div class="searchbox">.*?</div>', "", green, flags=re.S)
    assert removed != green
    code, out = _built_page_check(tmp_path / "removed", removed)
    assert code == 1, out
    assert "Search field · expected on this page · measured 0 matches" in out, out


@needs_browser
def test_the_summary_names_a_language_that_did_not_reach_every_page(tmp_path):
    """The one-line summary may never let a language count stand for pages it did not reach.

    This is the gate reporting on itself, so it is the one number nobody double-checks. An
    earlier version of this caveat was computed from the CONFIGURED page list rather than from
    the renders that happened, which left `--page` targets — English only, always — counted as
    covered in every requested language, and suppressed the caveat entirely when no inventory
    page was selected. Both shapes are pinned here.
    """
    folder = tmp_path / "pages"
    folder.mkdir()
    shutil.copy(FIXTURES / "green.html", folder / "green.html")
    shutil.copy(SYSTEM_CSS, folder / "system.css")

    def run(langs):
        proc = subprocess.run(
            [sys.executable, str(REPO / "scripts" / "check_design_inventory.py"), "--no-mocks", "--no-built",
             "--page", "green=%s" % (folder / "green.html"), "--langs", langs, "--viewports", "375"],
            capture_output=True, text=True, encoding="utf-8", env={**os.environ, "PYTHONIOENCODING": "utf-8"},
        )
        return [ln for ln in (proc.stdout + proc.stderr).splitlines() if "renders" in ln][-1]

    # An ad-hoc page renders in English whatever is asked for, so the two others reached nothing
    # and must say so as 0 rather than disappear from the tally.
    asked_three = run("en,de,fi")
    assert "pages per language: en 1, de 0, fi 0" in asked_three, asked_three
    assert "3 languages" in asked_three, asked_three

    # Coverage is uniform when only one language is asked for: no caveat, or it is noise that
    # trains the reader to ignore the line.
    asked_one = run("en")
    assert "pages per language" not in asked_one, asked_one


@needs_browser
def test_the_check_fails_a_page_that_shows_nothing_from_the_inventory(tmp_path):
    folder = tmp_path / "pages"
    folder.mkdir()
    (folder / "empty.html").write_text("<!doctype html><body class=\"fx\"><p>nothing</p></body>", encoding="utf-8")
    proc = subprocess.run(
        [sys.executable, str(REPO / "scripts" / "check_design_inventory.py"), "--no-mocks", "--no-built",
         "--page", "empty=%s" % (folder / "empty.html"), "--langs", "en", "--viewports", "375"],
        capture_output=True, text=True, encoding="utf-8", env={**os.environ, "PYTHONIOENCODING": "utf-8"},
    )
    assert proc.returncode == 1
    assert "measured 0" in proc.stdout


def test_the_check_refuses_an_inventory_it_cannot_read(tmp_path):
    bad = _doc(tmp_path, "| X | `.x` | r | `gap(nxt)=14px` | ruled | #1 |\n")
    proc = subprocess.run(
        [sys.executable, str(REPO / "scripts" / "check_design_inventory.py"), "--inventory", str(bad), "--no-mocks", "--no-built"],
        capture_output=True, text=True, encoding="utf-8",
    )
    assert proc.returncode == 2
    assert "INVENTORY ERROR" in proc.stderr


# --- the check in CI ------------------------------------------------------------------------
# `validate:ui` measures the site `build:site-v2` built, so its shape is pinned here: the
# `needs`, the shared rules (GitLab refuses a pipeline whose `needs:` target its own rules
# excluded), the shared stage (a `needs:` target may not sit in a later stage), the artifact
# the check reads, the browser image equal to the playwright pin, and the three steps.


def _ci():
    import yaml

    return yaml.safe_load((REPO / ".gitlab-ci.yml").read_text(encoding="utf-8"))


def _ui_pins():
    pins = {}
    for line in (REPO / "requirements-ui.txt").read_text(encoding="utf-8").splitlines():
        if line and not line.startswith("#"):
            name, version = line.split("==", 1)
            pins[name.strip().lower()] = version.strip()
    return pins


def _playwright_pin():
    return _ui_pins().get("playwright") or pytest.fail("requirements-ui.txt has no exact playwright pin")


# import name -> distribution name where the two differ
_DIST = {"yaml": "pyyaml"}


def _imports_of(path: Path) -> set[str]:
    import ast

    names = set()
    for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
        if isinstance(node, ast.Import):
            names |= {a.name.split(".")[0] for a in node.names}
        elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
            names.add(node.module.split(".")[0])
    return names


def test_every_package_the_job_imports_is_in_its_requirements_file():
    """The job installs requirements-ui.txt alone, so every module a file its script names
    imports anywhere - top level or deferred, directly or through a sibling in scripts/ -
    must be pinned there or stdlib. The files come from the job's own script lines, so a
    step added to the job is covered without editing this test."""
    import re

    script = " ".join(_ci()["validate:ui"]["script"])
    queue = [REPO / p for p in re.findall(r"\b((?:scripts|tests)/[\w/]+\.py)\b", script)]
    assert queue, "the job's script names no python file"
    seen, imported = set(), set()
    while queue:
        f = queue.pop()
        if f in seen:
            continue
        seen.add(f)
        for name in _imports_of(f):
            sibling = REPO / "scripts" / (name + ".py")
            if sibling.exists():
                queue.append(sibling)
            else:
                imported.add(name)
    third_party = imported - set(sys.stdlib_module_names) - {"__future__"}
    missing = sorted(m for m in third_party if _DIST.get(m, m).lower() not in _ui_pins())
    assert not missing, "imported by the job but not in requirements-ui.txt: %s" % missing
    assert {f.name for f in seen} >= {"check_ui_i18n_metrics.py", "check_page_css.py", "design_inventory.py", "check_design_inventory.py", "test_design_inventory.py"}


def test_validate_ui_needs_the_site_build_and_shares_its_rules_and_stage():
    ci = _ci()
    ui, build = ci["validate:ui"], ci["build:site-v2"]
    assert ui["needs"] == ["build:site-v2"]
    assert ui["stage"] == build["stage"]
    assert ui["rules"] == build["rules"]
    assert "site_v2/dist" in build["artifacts"]["paths"]


def test_validate_ui_runs_on_the_browser_image_the_playwright_pin_matches():
    ci = _ci()
    image = ci["validate:ui"]["image"]
    assert image.startswith("mcr.microsoft.com/playwright/python:v")
    assert image.split(":v", 1)[1].split("-", 1)[0] == _playwright_pin()
    assert "requirements-ui.txt" in " ".join(ci["validate:ui"]["before_script"])


def test_validate_ui_runs_the_lint_the_red_proof_and_the_measured_check():
    script = " ".join(_ci()["validate:ui"]["script"])
    assert "scripts/check_page_css.py" in script
    assert "tests/test_design_inventory.py" in script
    assert "scripts/check_design_inventory.py --dist site_v2/dist" in script
    # the check before its tests: the green fixture is measured against the live stylesheet, so
    # tests first would stop a stylesheet defect at the fixture, without the pages' lines and
    # screenshots
    assert script.index("scripts/check_design_inventory.py") < script.index("tests/test_design_inventory.py")
