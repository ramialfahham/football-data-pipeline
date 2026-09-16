"""Home re-rendered with the page-wide rules of the #129 review, without editing the repo's generators: the two board
blocks as single-value tables (the Table's striped rows, the board name in the head row with the
chevron), block names 13px, the 14px heading gap, ordered-by numbers in the accent, hover twice
the stripe. Everything else is the approved Home mock as the repo renders it."""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import gen_top_players as P  # noqa: E402
import gen_top_teams as T  # noqa: E402
from interaction import CHEVRON  # noqa: E402
from rows import CREST  # noqa: E402

E = T.E


def table_board(mod, board):
    rank_id = board["rank_metric"]
    title_en = mod.board_title(rank_id, mod.label(rank_id), "en")
    fi_raw, _ = mod.FI[rank_id]
    title_fi = mod.board_title(rank_id, fi_raw, "fi")
    rows = []
    for i, (abbr, name, sub, value) in enumerate(board["rows"], start=1):
        rows.append('<a class="ctab-row" href="#"><span class="rk num">%d</span>'
                    '<span class="tm"><span class="crest xs">%s</span><span class="ent"><span class="nm">%s</span>'
                    '<span class="sub">%s</span></span></span><span class="n num pts">%s</span></a>'
                    % (i, CREST, E(name), E(sub), E(value)))
    return ('<div class="board"><div class="ctab rkt"><div class="ctab-head"><span class="h rk"></span>'
            '<span class="h nmh"><a class="bt cnm" href="#"><span class="nm"><span class="en">%s</span>'
            '<span class="fi probe" lang="fi">%s</span></span>%s</a></span><span class="h"></span></div>'
            '%s</div></div>' % (E(title_en), E(title_fi), CHEVRON, "".join(rows)))


P.board_html = lambda b: table_board(P, b)
T.board_html = lambda b: table_board(T, b)

import gen_home  # noqa: E402,F401  (builds and writes design-mocks/home_mock.html at import)

RULES_CSS = """
/* ---- the page-wide rules of the competition page review, applied to Home ---- */
.sechead .eyebrow { font-size: 13px; }
section > .sechead + .fxgroup { margin-top: 0; }
section > .sechead + .fxgroup > .dh:first-child { padding-top: 0; }
section > .sechead + .tt-intro { margin-top: 0; }
@media (hover: hover) { .fx a.brow:hover, .fx a.comp-row:hover, .fx a.fxrow:hover, .fx a.ctab-row:hover, .fx a.frow:hover { background: color-mix(in srgb, var(--ink) 11%, transparent); } }
/* a ranking is a table: the Table block's striped rows, the board name in the head row */
.ctab.rkt, .ctab.rkt.ctab { --cols: 2rem minmax(0, 1fr) 3.6rem; margin-top: 0; }
.ctab.rkt .ctab-row { border-bottom: 0; }
.ctab.rkt .tm .ent { display: flex; flex-direction: column; min-width: 0; }
.ctab.rkt .tm .ent .sub { font-size: 12px; color: var(--muted); line-height: 1.2; }
.ctab.rkt .ctab-head { padding-bottom: 7px; }
.ctab.rkt .ctab-head .nmh { text-align: left; padding-left: 0; grid-column: 1 / 3; }
.ctab.rkt .ctab-head .rk { display: none; }
.ctab.rkt .ctab-head .nmh .bt { display: inline-flex; align-items: center; gap: 6px; }
.ctab.rkt .ctab-head .nmh .bt .nm { font-size: 14px; font-weight: 700; color: var(--ink); letter-spacing: 0; text-transform: none; }
.board:first-of-type { margin-top: 14px; }
"""

html_ = gen_home.OUT.read_text(encoding="utf-8")
assert html_.count("</style>") == 1
html_ = html_.replace("</style>", RULES_CSS + "</style>")
out = HERE / (sys.argv[1] if len(sys.argv) > 1 else "home_with_rules_v1.html")
out.write_text(html_, encoding="utf-8")
print("wrote", out.name)
