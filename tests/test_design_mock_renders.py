"""A review render is a file of record: `design-mocks/renders/<page>_<YYYY-MM-DD>_<nn>.html`.

The folder is held to the rule `design-mocks/render.py` writes by: every file matches the pattern,
a page's numbers run from 01 without a gap (a number counts up per page across dates and never
resets), a later number never carries an earlier date, and no render is swallowed by an ignore
rule (the folder's parent ignores `*.html`; a render that git does not see is a render lost).
The same checks run against a temporary folder built to break each rule, so the guard is seen
red before it is trusted.
"""

from __future__ import annotations

import datetime
import os
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
MOCKS = REPO / "design-mocks"
RENDERS = MOCKS / "renders"
sys.path.insert(0, str(MOCKS))
import render  # noqa: E402


def _problems(folder: Path) -> list[str]:
    """Every way the folder breaks the rule, one line each; empty when it holds."""
    out = []
    by_page: dict[str, list[tuple[int, str, str]]] = {}
    for p in sorted(folder.iterdir()):
        if p.is_dir():
            out.append("%s: a folder, not a render" % p.name)
            continue
        parsed = render.parse_name(p.name)
        if not parsed:
            out.append("%s: outside <page>_<YYYY-MM-DD>_<nn>.html" % p.name)
            continue
        page, date, nn = parsed
        by_page.setdefault(page, []).append((nn, date, p.name))
    for page, held in by_page.items():
        held.sort()
        expected = list(range(1, len(held) + 1))
        got = [nn for nn, _d, _n in held]
        if got != expected:
            out.append("%s: numbers %s, expected %s" % (page, got, expected))
        for (n1, d1, _), (n2, d2, name2) in zip(held, held[1:]):
            if d2 < d1:
                out.append("%s: number %02d carries an earlier date than %02d" % (name2, n2, n1))
    return out


def _ignored(paths: list[Path]) -> list[str]:
    if not paths:
        return []
    proc = subprocess.run(
        ["git", "check-ignore", "--no-index", *[str(p) for p in paths]],
        cwd=REPO, capture_output=True, text=True,
    )
    return [line.strip() for line in proc.stdout.splitlines() if line.strip()]


def test_the_folder_of_record_holds_the_rule():
    assert RENDERS.is_dir(), "design-mocks/renders/ is the folder of record"
    renders = sorted(RENDERS.glob("*.html"))
    assert renders, "the folder holds at least the four renders approved on #129"
    assert _problems(RENDERS) == []
    assert _ignored(renders) == [], "an ignore rule reaches into renders/ — those renders would be lost"


def test_next_name_counts_up_per_page_across_dates(tmp_path):
    assert render.next_name(tmp_path, "home", today="2026-09-17") == "home_2026-09-17_01.html"
    (tmp_path / "home_2026-09-16_01.html").write_text("", encoding="utf-8")
    (tmp_path / "home_2026-09-16_02.html").write_text("", encoding="utf-8")
    (tmp_path / "competition-overview_2026-09-16_01.html").write_text("", encoding="utf-8")
    assert render.next_name(tmp_path, "home", today="2026-09-17") == "home_2026-09-17_03.html"
    assert render.next_name(tmp_path, "competition-overview", today="2026-09-17") == "competition-overview_2026-09-17_02.html"
    assert render.next_name(tmp_path, "competition-matchdays", today="2026-09-17") == "competition-matchdays_2026-09-17_01.html"


def test_parse_name_admits_only_the_pattern():
    assert render.parse_name("competition-overview_2026-09-16_01.html") == ("competition-overview", "2026-09-16", 1)
    for bad in ("home_with_rules_v3.html", "competition_overview_final_v4.html", "home_2026-09-16_1.html",
                "Home_2026-09-16_01.html", "home_2026-09-16_01.htm", "home_20260916_01.html", "home-_2026-09-16_01.html"):
        assert render.parse_name(bad) is None, bad


@pytest.mark.parametrize("names, expected_fragment", [
    (["home_with_rules_v3.html"], "outside"),
    (["home_2026-09-16_01.html", "home_2026-09-16_03.html"], "numbers [1, 3]"),
    (["home_2026-09-16_02.html"], "numbers [2]"),
    (["home_2026-09-17_01.html", "home_2026-09-16_02.html"], "earlier date"),
])
def test_the_guard_goes_red_on_each_break(tmp_path, names, expected_fragment):
    for name in names:
        (tmp_path / name).write_text("", encoding="utf-8")
    problems = _problems(tmp_path)
    assert problems and any(expected_fragment in p for p in problems), problems


def test_the_guard_is_green_on_a_folder_that_holds(tmp_path):
    for name in ("home_2026-09-16_01.html", "home_2026-09-17_02.html", "competition-rankings_2026-09-16_01.html"):
        (tmp_path / name).write_text("", encoding="utf-8")
    assert _problems(tmp_path) == []


def test_render_writes_the_next_name_and_never_over_an_existing_file(tmp_path, monkeypatch):
    """The helper end to end against a stub generator: two runs give _01 then _02."""
    stub = tmp_path / "gen_stub.py"
    stub.write_text("import sys, pathlib\npathlib.Path(sys.argv[1]).write_text('<html></html>', encoding='utf-8')\n",
                    encoding="utf-8")
    monkeypatch.setattr(render, "HERE", tmp_path)
    monkeypatch.setattr(render, "RENDERS", tmp_path / "renders")
    assert render.main(["gen_stub.py", "stub-page"]) == 0
    assert render.main(["gen_stub.py", "stub-page"]) == 0
    written = sorted(p.name for p in (tmp_path / "renders").iterdir())
    today = datetime.date.today().isoformat()
    assert written == ["stub-page_%s_01.html" % today, "stub-page_%s_02.html" % today]
    with pytest.raises(SystemExit):
        render.main(["gen_stub.py", "Bad_Page"])
    with pytest.raises(SystemExit):
        render.main(["gen_missing.py", "stub-page"])
    assert sorted(os.listdir(tmp_path / "renders")) == written


def test_render_refuses_a_name_the_folder_already_holds(tmp_path, monkeypatch):
    """The overwrite guard, reached by making the name picker return a name that exists (what a
    second writer racing this one would produce): the existing render is left as it was."""
    stub = tmp_path / "gen_stub.py"
    stub.write_text("import sys, pathlib\npathlib.Path(sys.argv[1]).write_text('NEW', encoding='utf-8')\n",
                    encoding="utf-8")
    renders = tmp_path / "renders"
    renders.mkdir()
    existing = renders / "stub-page_2026-09-16_01.html"
    existing.write_text("OF RECORD", encoding="utf-8")
    monkeypatch.setattr(render, "HERE", tmp_path)
    monkeypatch.setattr(render, "RENDERS", renders)
    monkeypatch.setattr(render, "next_name", lambda folder, page, today=None: existing.name)
    with pytest.raises(SystemExit, match="refusing to overwrite"):
        render.main(["gen_stub.py", "stub-page"])
    assert existing.read_text(encoding="utf-8") == "OF RECORD"
    assert sorted(os.listdir(renders)) == [existing.name]
