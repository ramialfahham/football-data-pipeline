"""Pins the narrow-screen rules the pages keep: one breadcrumb, a venue and a list name that break between words, room for the chart's axis title."""

import re
from pathlib import Path

SRC = Path(__file__).resolve().parents[1] / "site_v2" / "src"


PAGE_OWNED_CRUMB = re.compile(r"<nav\b[^>]*\bclass(?::list)?\s*=[^>]*\bcrumb\b")


def _read(rel: str) -> str:
    return (SRC / rel).read_text(encoding="utf-8")


def test_the_crumb_pattern_catches_both_ways_of_writing_the_class():
    assert PAGE_OWNED_CRUMB.search('<nav class="crumb" aria-label="x">')
    assert PAGE_OWNED_CRUMB.search('<nav class:list={["crumb", { cut }]}>')
    assert not PAGE_OWNED_CRUMB.search('<nav class="tabs">')


def test_no_page_owns_a_breadcrumb():
    offenders = [
        str(p.relative_to(SRC))
        for p in SRC.rglob("*.astro")
        if p.name != "Breadcrumb.astro" and PAGE_OWNED_CRUMB.search(p.read_text(encoding="utf-8"))
    ]
    assert offenders == []


def test_every_page_but_home_uses_the_breadcrumb_component():
    root = SRC / "pages" / "[lang]"
    missing = []
    for p in root.rglob("*.astro"):
        text = p.read_text(encoding="utf-8")
        if p.relative_to(root).as_posix() == "index.astro" or "crumbs=" not in text:
            continue
        if "Breadcrumb" not in text and "MatchesDay" not in text:
            missing.append(p.relative_to(SRC).as_posix())
    assert missing == []
    assert "<Breadcrumb" in _read("components/matches/MatchesDay.astro")


def test_a_two_level_trail_keeps_home_on_a_phone():
    text = _read("components/fixture/Breadcrumb.astro")
    assert re.search(r"far:\s*\(i === 0 && items\.length > 2\) \|\| last", text)
    pages = [
        "pages/[lang]/[competitions]/index.astro",
        "pages/[lang]/[teams]/index.astro",
        "pages/[lang]/[players]/index.astro",
    ]
    for rel in pages:
        assert len(re.findall(r"\{ name: ", re.search(r"const crumbs = \[(.*?)\];", _read(rel), re.S).group(1))) == 2, rel
    opening = re.search(r"\.\.\.\(isOpening\s*\? \[(.*?)\]\s*:", _read("components/matches/MatchesDay.astro"), re.S)
    assert opening is not None and opening.group(1).count("label:") == 1
    assert ".trail .far { display: none; }" in _read("styles/system.css")


def test_the_breadcrumb_script_does_not_sit_between_the_nav_and_the_heading():
    text = (SRC / "components" / "fixture" / "Breadcrumb.astro").read_text(encoding="utf-8")
    assert text.index("<script>") < text.index('<nav class="crumb trail"')
    assert text.rstrip().endswith("</nav>")


def test_the_venue_is_one_unit_of_the_kick_off_line():
    text = _read("components/fixture/Masthead.astro")
    assert "fixture.venue]" not in text
    assert re.search(r'<span class="nb">\{venue\}', text) is None
    assert "{venue && <span>{venue}</span>}" in text


def test_the_competition_list_name_wraps_between_words():
    block = re.search(r"\.comp-name \{(.*?)\n\}", _read("styles/system.css"), re.S)
    assert block is not None
    assert "text-overflow" not in block.group(1)
    assert "nowrap" not in block.group(1)


def test_linked_rows_are_square_and_flush():
    css = _read("styles/system.css")
    row = re.search(r"^a\.fxrow, a\.ctab-row, a\.frow, a\.lrow \{(.*?)\}", css, re.M)
    assert row is not None
    assert "border-radius" not in row.group(1) and "margin-inline" not in row.group(1)
    assert re.search(r"^a\.brow \{", css, re.M) is None
    assert "border-radius" not in "".join(re.findall(r"^a\.comp-row \{(.*?)\}", css, re.M))


def test_a_filter_button_is_at_least_44px_wide_and_no_rule_narrows_it():
    css = _read("styles/system.css")
    rules = re.findall(r"^([^{}\n]*\.seg-btn[^{}\n]*)\{([^}]*)\}", css, re.M)
    sizing = [(sel.strip(), body) for sel, body in rules if re.search(r"(?<![\w-])(min-|max-)?width\s*:", body)]
    assert [sel for sel, _ in sizing] == [".fbar > .seg:not(.sel) .seg-btn"]
    assert "min-width: 44px" in sizing[0][1]
    shrinking = [body for sel, body in rules if sel.strip().startswith(".fbar") and re.search(r"flex:\s*\d+\s+[1-9]", body)]
    assert shrinking == []


def test_a_team_competition_row_keeps_the_space_in_goals_and_points():
    text = _read("components/ui/CompetitionRow.astro")
    assert re.search(r'"goals"\)\}\{" "\}<b>', text)
    assert re.search(r'"points"\)\}\{" "\}<b>', text)


def test_the_header_buttons_shrink_before_the_header_overflows():
    css = _read("styles/system.css")
    assert ".iconbtn { width: 44px; height: 44px; flex: 0 1 auto; min-width: 34px; }" in css
    assert ".header-actions { flex: 0 1 auto; min-width: 0; }" in css
    assert css.rindex(".header-actions { flex: 0 1 auto") > css.index(".header-actions { margin-left: auto")


def test_the_team_page_explainer_does_not_name_the_team():
    strings = _read("i18n/strings.ts")
    for line in re.findall(r"^\s*teamPerfIntro: .*$", strings, re.M):
        assert "{team}" not in line
    assert "team:" not in re.search(r'"teamPerfIntro", \{(.*?)\}', _read("pages/[lang]/[teams]/[team].astro")).group(1)


def test_no_template_or_stylesheet_writes_a_separator_dot():
    middot = chr(0xB7)
    offenders = [
        str(p.relative_to(SRC))
        for ext in ("*.astro", "*.ts", "*.mjs", "*.css")
        for p in SRC.rglob(ext)
        if middot in p.read_text(encoding="utf-8") or "&middot;" in p.read_text(encoding="utf-8")
    ]
    assert offenders == []
    assert "dotEdges" not in _read("layouts/Layout.astro")


def test_a_facts_line_has_a_gap_and_every_aligned_host_sets_its_justify():
    css = _read("styles/system.css")
    assert ".facts-line { display: inline-flex; flex-wrap: wrap; column-gap: 12px; row-gap: 0;" in css
    assert ".facts-line > * { max-width: 100%; min-width: 0; }" in css
    lines = css.splitlines()
    for host in (".rmeta {", ".pstat {", ".fmeta {", ".mast .kick {", ".stand {", ".tc-nums {"):
        rules = [ln for ln in lines if host in ln and ln.lstrip().startswith((".", "@")) or host in ln and ln.startswith("  .")]
        assert rules, host
        for ln in rules:
            if host == ".rmeta {" and "text-align" not in ln:
                continue
            assert "--facts-justify" in ln, ln
            if "text-align: left" in ln:
                assert "--facts-justify: flex-start" in ln, ln
            if "text-align: right" in ln:
                assert "--facts-justify: flex-end" in ln, ln


def test_the_scatter_axis_title_has_room_inside_the_drawing():
    theme = _read("lib/chartTheme.ts")
    title_x = int(re.search(r"yTitleX:\s*(\d+)", theme).group(1))
    lefts = [int(n) for n in re.findall(r"left:\s*(\d+)", theme)]
    assert title_x >= 15
    assert all(left - title_x >= 33 for left in lefts)
