"""Tests for scripts/parts_page.py: the page list from the Pages table, the kinds, the form dedupe,
the same-text detector, the frame document and the drawing check, on fixtures without a dev server."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "scripts"))
import check_component_registry as ccr  # noqa: E402
import parts_page as pp  # noqa: E402

TABLE = """
## Pages

| Page | Kind | Source | URL | FI | Expect |
|---|---|---|---|---|---|
| Home | built | `site_v2/dist` | `en/index.html` | path | Block heading |
| Team page | built | `site_v2/dist` | `en/teams/*/index.html` | path | Tab bar |
| home | mock | `gen_home.py` | `home_mock.html` | toggle | Block heading |
"""

STYLE_A = {p: "0px" for p in pp.STYLE_PROPS} | {"font-size": "15px", "font-weight": "600", "color": "rgb(1, 1, 1)"}
STYLE_B = dict(STYLE_A, **{"font-size": "17px", "font-weight": "700"})


def _inst(page, markup, styles, state=""):
    return {"page": page, "state": state, "key": "k", "bundle": 0,
            "captures": {w: {"style": s, "html": markup, "chain": [], "trimmed": False}
                         for w, s in styles.items()}}


def _run(page, text, style, part, width=375):
    return {"page": page, "width": width, "id": 0, "text": text,
            "style": {p: style.get(p, "") for p in pp.TEXT_PROPS}, "part": part}


def test_pages_from_table_takes_built_rows_and_picks_globs():
    picks = {"Team page": [("Team page · club", "/en/teams/club/", None)]}
    pages = pp.pages_from_table(TABLE, picks)
    assert [(p["label"], p["path"]) for p in pages] == [("Home", "/en/"), ("Team page · club", "/en/teams/club/")]


def test_pages_from_table_fails_on_a_glob_without_a_pick():
    with pytest.raises(pp.PagesError, match="Team page"):
        pp.pages_from_table(TABLE, {})


def test_every_built_row_of_the_real_table_has_a_page():
    pages = pp.pages_from_table(pp.BLOCK_STANDARD.read_text(encoding="utf-8"))
    labels = [p["label"] for p in pages]
    assert "Team page · national team" in labels and "Team page · club" in labels


def test_kinds_name_only_registry_parts():
    keys = [p["key"] for p in pp.registry_parts(ccr.load())]
    placed, unplaced = pp.kind_of(keys)
    assert placed["competition-row.name"] == "Competition name"
    assert "page-shell.root" in unplaced
    with pytest.raises(KeyError):
        pp.kind_of(keys, [("Ghost", ["no-such.part"])])


def test_skeleton_ignores_text_and_content_driven_classes():
    a = '<a class="cnm"><span class="nm">UEFA Nations <span class="nb">League</span></span></a>'
    b = '<a class="cnm"><span class="nm">Bundesliga</span></a>'
    assert pp.skeleton(a) == pp.skeleton(b)
    assert pp.skeleton('<div class="ctab fit-two"><a class="ctab-row"></a></div>') == \
        pp.skeleton('<div class="ctab fit-one"><a class="ctab-row"></a></div>')


def test_skeleton_counts_a_run_of_identical_children_once_and_sees_an_extra_child():
    three = '<nav class="tabs"><label class="tab">A</label><label class="tab">B</label><label class="tab">C</label></nav>'
    two = '<nav class="tabs"><label class="tab">A</label><label class="tab">B</label></nav>'
    tagged = '<nav class="tabs"><label class="tab">A</label><span class="nexttag">Next</span></nav>'
    assert pp.skeleton(three) == pp.skeleton(two)
    assert pp.skeleton(tagged) != pp.skeleton(two)


def test_distinct_forms_merge_same_structure_and_style_and_split_on_style():
    row = '<span class="nm">x</span>'
    forms = pp.distinct_forms([
        _inst("Home", row, {375: STYLE_A, 1000: STYLE_A}),
        _inst("Teams page", row, {375: STYLE_A, 1000: STYLE_A}),
        _inst("Home", row, {375: STYLE_B, 1000: STYLE_B}),
    ])
    assert [f["count"] for f in forms] == [2, 1]
    assert set(forms[0]["where"]) == {"Home", "Teams page"}
    assert forms[0]["where"]["Home"] == {375, 1000}


def test_distinct_forms_a_part_shown_at_one_width_only_is_its_own_form():
    row = '<span class="nm">x</span>'
    forms = pp.distinct_forms([_inst("Home", row, {375: STYLE_A, 1000: STYLE_A}),
                               _inst("Home", row, {1000: STYLE_A})])
    assert len(forms) == 2


def test_same_text_finds_the_competition_name_in_two_styles_on_one_page():
    page = "Team page · national team"
    runs = [_run(page, "UEFA Nations League", STYLE_A, "competition-row.name"),
            _run(page, "UEFA  Nations League ", STYLE_B, "group.name"),
            _run(page, "UEFA Nations League", STYLE_A, "competition-row.name", width=1000),
            _run(page, "UEFA Nations League", STYLE_B, "group.name", width=1000)]
    [f] = pp.same_text_findings(runs)
    assert f["text"] == "UEFA Nations League" and f["widths"] == [375, 1000]
    assert [v["parts"] for v in f["variants"]] == [["competition-row.name"], ["group.name"]]


def test_same_text_ignores_one_style_other_pages_and_short_or_numeric_text():
    runs = [_run("Home", "Bundesliga", STYLE_A, "a"), _run("Home", "Bundesliga", STYLE_A, "b"),
            _run("Home", "Serie A", STYLE_A, "a"), _run("Teams page", "Serie A", STYLE_B, "b"),
            _run("Home", "12", STYLE_A, "a"), _run("Home", "12", STYLE_B, "b"),
            _run("Home", "W", STYLE_A, "a"), _run("Home", "W", STYLE_B, "b")]
    assert pp.same_text_findings(runs) == []


CLUB_ROW = ('<div class="lrow tc"><div class="tcin"><span class="tc-name">Bundesliga</span>'
            '<span class="tc-right"><span class="cchips"><span class="cchip W">5</span><span class="cchip L">1</span>'
            '</span><span class="tc-nums">Goals 12:4 · Points 16</span></span></div></div>')
NATIONAL_ROW = ('<div class="lrow tc"><div class="tcin"><span class="tc-name">UEFA Nations League'
                '<span class="tc-ctx">· League phase</span><svg class="chev"></svg></span>'
                '<span class="tc-right"><span class="tc-rank2">3rd</span></span></div></div>')


def test_child_tokens_leave_out_result_and_state_classes():
    assert pp.child_tokens(CLUB_ROW) == {".tcin", ".tc-name", ".tc-right", ".cchips", ".cchip", ".tc-nums"}
    assert ".chev" in pp.child_tokens(NATIONAL_ROW)


def test_part_differences_name_the_child_elements_each_page_has():
    d = pp.part_differences([_inst("Team page · club", CLUB_ROW, {375: STYLE_A}),
                             _inst("Team page · national team", NATIONAL_ROW, {375: STYLE_A})])
    children = {tok: (have, lack) for tok, have, lack in d["children"]}
    assert children[".chev"] == (["Team page · national team"], ["Team page · club"])
    assert children[".cchip"] == (["Team page · club"], ["Team page · national team"])
    assert children[".tc-nums"] == (["Team page · club"], ["Team page · national team"])
    assert ".tc-name" not in children and d["look"] == []


def test_part_differences_report_a_look_that_differs_between_pages_only():
    band = dict(STYLE_A, **{"background-color": "rgb(30, 30, 30)"})
    bar = '<nav class="tabs"><label class="tab">A</label></nav>'
    d = pp.part_differences([_inst("Team page · club", bar, {375: band}),
                             _inst("Competition overview", bar, {375: STYLE_A})])
    assert d["look"] == [(375, "background-color", {"0px": ["Competition overview"],
                                                    "rgb(30, 30, 30)": ["Team page · club"]})]
    same_states = [_inst(p, bar, {375: s}) for p in ("Home", "Teams page") for s in (STYLE_A, STYLE_B)]
    assert pp.part_differences(same_states)["look"] == []


def test_form_differences_name_what_tells_the_forms_apart():
    forms = pp.distinct_forms([_inst("Team page · club", CLUB_ROW, {375: STYLE_A}),
                               _inst("Team page · club", NATIONAL_ROW, {375: STYLE_B})])
    d = pp.form_differences(forms)
    assert (".chev", [2]) in d["children"] and (".tc-nums", [1]) in d["children"]
    assert (375, "font-size", {"15px": [1], "17px": [2]}) in d["look"]
    assert all(prop != "color" for _, prop, _ in d["look"])


MINIMAL_CHAIN = [{"tag": "html", "attrs": [], "inputs": []}, {"tag": "body", "attrs": [], "inputs": []}]


def _row_data():
    rows = [("Team page · club", CLUB_ROW, STYLE_A), ("Team page · national team", NATIONAL_ROW, STYLE_B)]
    return {"sheets": [""], "bundles": [[0]], "runs": [], "pages": [], "colours": {},
            "instances": [{"page": p, "state": "", "key": "competition-row.row", "bundle": 0,
                           "captures": {375: {"style": s, "html": m, "chain": MINIMAL_CHAIN, "trimmed": False}}}
                          for p, m, s in rows]}


def test_render_lists_what_differs_from_page_to_page_and_between_forms():
    data = _row_data()
    parts = [{"key": "competition-row.row", "selector": ".lrow.tc", "name": "Competition row"}]
    page, counts = pp.render(data, parts, [], pp.forms_of(data["instances"]), {})
    assert counts["Row"]["competition-row.row"] == 2
    assert "has .chev on Team page · national team; not on Team page · club" in page
    assert "font-size at 375px: 15px on Team page · club; 17px on Team page · national team" in page
    assert "<li>.chev in form 2</li>" in page and "<li>.tc-nums in form 1</li>" in page
    assert "font-size at 375px: 15px in form 1; 17px in form 2" in page


def test_an_interrupted_drawing_check_leaves_the_last_page_in_place(tmp_path, monkeypatch):
    out = tmp_path / "parts_page.html"
    out.write_text("the last complete page", encoding="utf-8")

    def dies(path):
        raise RuntimeError("drawing check died")

    monkeypatch.setattr(pp, "check_fidelity", dies)
    parts = [{"key": "competition-row.row", "selector": ".lrow.tc", "name": "Competition row"}]
    with pytest.raises(RuntimeError):
        pp.write_page(out, _row_data(), parts, [])
    assert out.read_text(encoding="utf-8") == "the last complete page"
    assert (tmp_path / "parts_page.unchecked.html").exists()


def test_frame_doc_keeps_ancestor_inputs_before_the_element():
    chain = [{"tag": "html", "attrs": [["lang", "en"]], "inputs": []},
             {"tag": "body", "attrs": [["class", "fx"], ["data-theme", "dark"]], "inputs": []},
             {"tag": "div", "attrs": [["class", "inner"]],
              "inputs": ['<input type="radio" id="tab-matches" class="tab-in" checked="">']},
             {"tag": "div", "attrs": [["class", "page"], ["data-page", "matches"]], "inputs": []}]
    doc, depth = pp.frame_doc({"chain": chain, "html": '<span class="nm">Germany</span>'})
    assert depth == 2
    assert '<body class="fx" data-theme="dark">' in doc
    assert ('<div class="inner"><input type="radio" id="tab-matches" class="tab-in" checked="">'
            '<div class="page" data-page="matches"><span class="nm">Germany</span></div></div>') in doc


def test_fidelity_lists_the_properties_that_differ():
    assert pp.fidelity_mismatches(STYLE_A, dict(STYLE_A)) == []
    assert pp.fidelity_mismatches(STYLE_A, STYLE_B) == ["font-size 15px → 17px", "font-weight 600 → 700"]
    assert pp.fidelity_mismatches(STYLE_A, None) == ["not rendered"]


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


FIXTURE = """<!doctype html><html><head><style>
.tc-name{font-size:15px;font-weight:600}.tc-ctx{font-size:12px;color:gray}
.gh .nm{font-size:17px;font-weight:700}
</style></head><body>
<div class="lrow tc"><div class="tc-name">UEFA Nations <span class="nb">League<span class="tc-ctx">
<span class="nb">·&nbsp;</span>League phase</span></span></div></div>
<div class="fxgroup"><div class="gh"><a class="cnm"><span class="nm">UEFA Nations League</span></a></div></div>
<div class="fxgroup"><div class="gh"><span class="nm"><span class="nb">Saint-Germain</span></span></div></div>
<div class="vh" style="position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0 0 0 0)">UEFA Nations League</div>
</body></html>"""


@pytest.mark.skipif(not _chromium_available(), reason="Playwright's Chromium is not installed here")
def test_collect_joins_a_name_split_by_an_unbreakable_unit_and_finds_it_in_two_styles():
    from playwright.sync_api import sync_playwright

    parts = [{"key": "competition-row.name", "selector": ".tc .tc-name"},
             {"key": "group.name", "selector": ".fxgroup > .gh .nm"},
             {"key": "unit.unit", "selector": ".nb"}]
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        page = browser.new_page(viewport={"width": 375, "height": 600})
        page.set_content(FIXTURE)
        got = page.evaluate(pp.COLLECT_JS, {"parts": parts, "props": list(pp.STYLE_PROPS), "tokens": []})
        browser.close()
    runs = [dict(r, page="Team page · national team", width=375) for r in got["runs"]]
    assert {r["text"] for r in runs} >= {"UEFA Nations League", "· League phase"}
    [f] = [f for f in pp.same_text_findings(runs) if f["text"] == "UEFA Nations League"]
    assert sorted(p for v in f["variants"] for p in v["parts"]) == ["competition-row.name", "group.name"]
    assert len([i for i in got["instances"] if i["key"] == "competition-row.name" and i["visible"]]) == 1
    [saint] = [r for r in runs if r["text"] == "Saint-Germain"]
    assert saint["part"] == "group.name"


def _drawing_data(styles):
    chain = [{"tag": "html", "attrs": [], "inputs": []}, {"tag": "body", "attrs": [], "inputs": []},
             {"tag": "div", "attrs": [["class", "fxgroup"]], "inputs": []}]
    marks = ['<span class="nm">Bundesliga</span>', '<span class="nm"><b>Serie</b> A</span>']
    return {"sheets": [".nm{padding-left:7px}"], "bundles": [[0]], "runs": [], "pages": [], "colours": {},
            "instances": [{"page": "Home", "state": "", "key": "group-head.name", "bundle": 0,
                           "captures": {375: {"style": s, "html": m, "chain": chain, "trimmed": False}}}
                          for m, s in zip(marks, styles)]}


@pytest.mark.skipif(not _chromium_available(), reason="Playwright's Chromium is not installed here")
def test_the_drawing_check_measures_the_part_itself_and_marks_only_a_form_drawn_differently(tmp_path):
    parts = [{"key": "group-head.name", "selector": ".nm", "name": "Competition group name"}]
    out = tmp_path / "parts_page.html"
    placeholder = {p: "" for p in pp.STYLE_PROPS}
    pp.write_page(out, _drawing_data([placeholder, placeholder]), parts, [])
    truth = pp.check_fidelity(out)
    assert truth["1-375"]["padding-left"] == "7px" and truth["2-375"]["padding-left"] == "7px"
    broken = dict(truth["2-375"], **{"padding-left": "9px"})
    counts, fidelity = pp.write_page(out, _drawing_data([truth["1-375"], broken]), parts, [])
    assert fidelity == {"1-375": [], "2-375": ["padding-left 9px → 7px"]}
    page = out.read_text(encoding="utf-8")
    assert page.count("Out of its page:") == 1 and "padding-left 9px → 7px" in page
    assert counts["Competition name"]["group-head.name"] == 2
    assert not (tmp_path / "parts_page.unchecked.html").exists()
