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
    | home | mock | `gen_home.py {out}` | `home.html` | toggle | Block heading |
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
    assert proposed == ["Breadcrumb current page", "Header row"], (
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
    proc = subprocess.run(
        [sys.executable, str(REPO / "scripts" / "check_design_inventory.py"), "--no-mocks", "--no-built",
         "--page", "%s=%s" % (name, folder / ("%s.html" % name)), "--langs", "en"],
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
