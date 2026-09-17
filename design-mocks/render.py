"""Render a design mock under its name of record: `renders/<page>_<YYYY-MM-DD>_<nn>.html`.

A render sent for review is never overwritten, so the file name is never chosen by hand: this
picks the next number for the page from what the folder already holds (the number counts up per
page across dates and never resets), runs the generator with that path as its one argument, and
refuses to write over an existing file. `tests/test_design_mock_renders.py` holds the folder to
the same pattern.

    python design-mocks/render.py gen_home_with_rules.py home
    -> design-mocks/renders/home_2026-09-17_02.html
"""
import datetime as dt
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
RENDERS = HERE / "renders"
NAME = re.compile(r"^(?P<page>[a-z0-9]+(?:-[a-z0-9]+)*)_(?P<date>\d{4}-\d{2}-\d{2})_(?P<nn>\d{2})\.html$")


def parse_name(name):
    """(page, date, nn) for a file name of record, or None when the name is outside the pattern."""
    m = NAME.match(name)
    if not m:
        return None
    return m.group("page"), m.group("date"), int(m.group("nn"))


def numbers(folder, page):
    """The numbers the folder already holds for a page, in order."""
    out = []
    for p in sorted(folder.glob("*.html")):
        parsed = parse_name(p.name)
        if parsed and parsed[0] == page:
            out.append(parsed[2])
    return out


def next_name(folder, page, today=None):
    held = numbers(folder, page)
    nn = (held[-1] if held else 0) + 1
    if nn > 99:
        raise SystemExit("%s has 99 renders; the pattern holds two digits" % page)
    today = today or dt.date.today().isoformat()
    return "%s_%s_%02d.html" % (page, today, nn)


def main(argv):
    if len(argv) != 2 or not parse_name("%s_2000-01-01_01.html" % argv[1]):
        raise SystemExit("usage: render.py <generator.py> <page>   (page: lowercase words joined by '-')")
    generator, page = HERE / argv[0], argv[1]
    if not generator.is_file():
        raise SystemExit("no such generator: %s" % generator)
    RENDERS.mkdir(exist_ok=True)
    out = RENDERS / next_name(RENDERS, page)
    if out.exists():
        raise SystemExit("refusing to overwrite %s" % out)
    subprocess.run([sys.executable, str(generator), str(out)], cwd=HERE, check=True)
    if not out.is_file():
        raise SystemExit("%s did not write %s" % (generator.name, out))
    print(out.relative_to(HERE.parent).as_posix())
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
