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


def test_the_venue_is_not_a_no_break_unit():
    text = _read("components/fixture/Masthead.astro")
    assert "fixture.venue]" not in text
    assert re.search(r'<span class="nb">\{venue\}', text) is None
    assert re.search(r"\{venue && <>.*\{venue\}</>\}", text)


def test_the_competition_list_name_wraps_between_words():
    block = re.search(r"\.comp-name \{(.*?)\n\}", _read("styles/system.css"), re.S)
    assert block is not None
    assert "text-overflow" not in block.group(1)
    assert "nowrap" not in block.group(1)


def test_the_scatter_axis_title_has_room_inside_the_drawing():
    theme = _read("lib/chartTheme.ts")
    title_x = int(re.search(r"yTitleX:\s*(\d+)", theme).group(1))
    lefts = [int(n) for n in re.findall(r"left:\s*(\d+)", theme)]
    assert title_x >= 15
    assert all(left - title_x >= 33 for left in lefts)
