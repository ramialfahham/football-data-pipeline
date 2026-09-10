"""BISECT the row collapse — properly this time, as SEPARATE FILES.

⚠ The first attempt put all variants in one document and suppressed my stylesheet with
`all: revert`. That reverts EVERYTHING, system.css included, so the one variant that rendered
proved only "unstyled works" — it could not distinguish system.css from ROW_CSS. Useless.

A rule cannot be un-applied within a document, so each variant is its own FILE with a different
stylesheet built up one rule at a time. The first file that breaks names the rule.

  1  system.css only                     the shipped row, untouched by me
  2  + the .nm wrap override             stops the name truncating
  3  + the .side grid override           badge / name / score columns
  4  + full ROW_CSS                      what the mocks ship

Same markup in every file. Same width. The only difference is how much CSS is applied.
"""
import html
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SYSTEM_CSS = REPO / "site_v2/src/styles/system.css"
HERE = Path(__file__).parent

from rows import CREST, ROW_CSS   # noqa: E402

E = html.escape

HOME, AWAY, HG, AG, TIME, ZONE = "Borussia Mönchengladbach", "SC Freiburg", 3, 1, "15:30", "CET"

NM_RULE = """
.fxrow .side .nm {
  white-space: normal; overflow: visible; text-overflow: clip;
  overflow-wrap: normal; word-break: normal; hyphens: none; line-height: 1.25;
}
"""

SIDE_RULE = """
.fxrow .side { display: grid; grid-template-columns: 24px minmax(0, 1fr) auto; column-gap: 10px; }
.fxrow .side .g {
  padding-left: 14px; min-width: 1.6rem; text-align: right;
  font-size: 16px; font-weight: 700; color: var(--muted); font-variant-numeric: tabular-nums;
}
"""

STEPS = [
    ("1", "system.css ONLY — the shipped row, nothing of mine", ""),
    ("2", "+ the .nm wrap override (stops the name truncating)", NM_RULE),
    ("3", "+ the .side grid override (badge / name / score columns)", NM_RULE + SIDE_RULE),
    ("4", "+ full ROW_CSS — what the mocks ship", ROW_CSS),
]

PAGE_CSS = """
body { margin: 0; background: #0d0f13; color: #f1f3f7;
       font: 400 15px/1.5 system-ui, -apple-system, "Segoe UI", Roboto, sans-serif; }
.wrap { max-width: 620px; margin: 0 auto; padding: 22px 20px 50px; }
h1 { font-size: 17px; margin: 0 0 4px; font-family: ui-monospace, monospace; color: #3bb072; }
.lead { font-size: 13px; color: #8b9099; margin: 0 0 6px; line-height: 1.6; }
.want { font-size: 12.5px; color: #c1c6ce; margin: 0 0 18px; line-height: 1.6;
        border-left: 3px solid #3bb072; padding-left: 12px; }
.box { border: 1px solid #333844; border-radius: 10px; padding: 6px 16px 12px; }
.crest.xs svg { width: 15px; height: 15px; display: block; color: #8b9099; }
"""


def row():
    def side(name, goals):
        return ('<span class="side"><span class="crest xs">%s</span>'
                '<span class="nm">%s</span><b class="g num">%d</b></span>'
                % (CREST, E(name), goals))
    return ('<a class="fxrow played" href="#"><span class="sides">%s%s</span>'
            '<span class="when"><b class="t">%s</b><span class="rowtz">%s</span></span></a>'
            % (side(HOME, HG), side(AWAY, AG), TIME, ZONE))


def build(key, label, extra):
    return """<!doctype html>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>bisect %s</title>
<style>
%s
%s
%s
</style>
<div class="wrap">
  <h1>FILE %s &nbsp;&mdash;&nbsp; %s</h1>
  <p class="lead">Same markup in all four files. Only the stylesheet differs.</p>
  <p class="want">Correct = two lines, each a badge then the club name <b>on one line</b>, the
     score just right of the name, and <b>15:30 / CET</b> in its own column at the far right.</p>
  <div class="box fx">%s</div>
</div>
""" % (key, SYSTEM_CSS.read_text(encoding="utf-8"), extra, PAGE_CSS, key, label, row())


if __name__ == "__main__":
    for key, label, extra in STEPS:
        out = HERE / ("bisect_%s.html" % key)
        out.write_text(build(key, label, extra), encoding="utf-8")
        print("  wrote %s  (%s)" % (out.name, label))
    stale = HERE / "row_diagnostic.html"
    if stale.exists():
        stale.unlink()
        print("  removed row_diagnostic.html (the bad all:revert bisect it replaces)")
