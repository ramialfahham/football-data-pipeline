"""Home as approved on #127 after the #129 review, without editing the repo's generators: the
two board blocks as single-value tables (the Table's striped rows, the board name in the head row
with the chevron). Everything else is the approved Home mock as the repo renders it; every rule
the page follows is the stylesheet's."""
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

html_ = gen_home.OUT.read_text(encoding="utf-8")
out = HERE / (sys.argv[1] if len(sys.argv) > 1 else "home_with_rules_v1.html")
out.write_text(html_, encoding="utf-8")
print("wrote", out.name)
