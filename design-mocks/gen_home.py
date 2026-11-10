"""Compose the whole home page: next matches -> Top players -> Top teams.

Top players and Top teams markup is imported from their block generators; numbers are placeholder.
"""
import html
import sys
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))

# The sys.path insert above must run before these sibling imports, hence the E402 markers.
import gen_top_players as P  # noqa: E402
import gen_top_teams as T  # noqa: E402
from gen_block_standard import ZONE, short, slug  # noqa: E402
from rows import date_head, group_head, upcoming_row  # noqa: E402

OUT = HERE / "home_mock.html"
if __name__ == "__main__" and sys.argv[1:2] == ["--out"]:
    OUT = Path(sys.argv[2]) / OUT.name
E = html.escape

# ------------------------------------------------------------ next matches

# (league_code, [(date, [(home, away, kickoff)])])
FIXTURES = [
    ("PL", [("Sat 14 Feb", [("Arsenal", "Manchester City", "17:30"),
                            ("Liverpool", "Brighton & Hove Albion", "20:00")]),
            ("Sun 15 Feb", [("Brentford", "Everton", "15:00")])]),
    ("PD", [("Sat 14 Feb", [("Real Madrid", "Athletic Club", "21:00")]),
            ("Sun 15 Feb", [("Barcelona", "Real Valladolid", "18:30")])]),
    ("BL1", [("Fri 13 Feb", [("1. FC Heidenheim", "Bayer 04 Leverkusen", "20:30")]),
             ("Sat 14 Feb", [("Bayern München", "Borussia Mönchengladbach", "15:30"),
                             ("VfL Wolfsburg", "SC Freiburg", "15:30"),
                             ("FC Augsburg", "1. FC Union Berlin", "15:30"),
                             ("VfB Stuttgart", "Borussia Dortmund", "15:30"),
                             ("Werder Bremen", "1. FSV Mainz 05", "15:30"),
                             ("RB Leipzig", "Eintracht Frankfurt", "18:30")]),
             ("Sun 15 Feb", [("TSG Hoffenheim", "1. FC Köln", "15:30"),
                             ("FC St. Pauli", "Hamburger SV", "17:30")])]),
    ("SA", [("Sat 14 Feb", [("Inter", "Atalanta", "20:45")]),
            ("Sun 15 Feb", [("Napoli", "Lecce", "18:00")])]),
    ("L1", [("Sat 14 Feb", [("Paris Saint-Germain", "Lens", "21:00")]),
            ("Sun 15 Feb", [("Le Havre", "Monaco", "17:00")])]),
    ("ED", [("Sun 15 Feb", [("PSV", "Feyenoord", "14:30")])]),
]

# Rows a competition shows before the fold; the rest sit in the site's fold, mirroring
# `components/ui/Fold.astro`.
VISIBLE_ROWS = 3

CHEV = ('<svg class="chev" viewBox="0 0 24 24" aria-hidden="true" focusable="false">'
        '<path d="M9 6l6 6-6 6" fill="none" stroke="currentColor" stroke-width="2.2" '
        'stroke-linecap="round" stroke-linejoin="round"></path></svg>')


def sechead(label):
    return '<div class="sechead"><span class="eyebrow">%s</span></div>' % E(label)


def next_matches():
    """A date head travels with the first row it applies to, so it folds with its rows."""
    out = ["<section>", sechead("Next matches")]
    for code, dates in FIXTURES:
        out.append('<div class="fxgroup">%s' % group_head(slug(code), short(code)))
        rows = []
        for date, matches in dates:
            for i, (home, away, time) in enumerate(matches):
                rows.append((date if i == 0 else None,
                             upcoming_row("club", home, away, time, ZONE[code] or "—")))
        visible, folded = rows[:VISIBLE_ROWS], rows[VISIBLE_ROWS:]
        for date, row in visible:
            if date:
                out.append(date_head(date))
            out.append(row)
        if folded:
            fid = "fold-%s" % code
            out.append('<input type="checkbox" class="fold-in" id="%s"><div class="fold-rest">' % fid)
            for date, row in folded:
                if date:
                    out.append(date_head(date))
                out.append(row)
            out.append('</div><label class="fold-ctl" for="%s"><span class="lbl">'
                       '<span class="closed">Show all %d</span><span class="opened">Show less</span>'
                       '</span>%s</label>' % (fid, len(rows), CHEV))
        out.append("</div>")
    out.append("</section>")
    return "\n".join(out)


def block(mod, eyebrow, intro):
    boards = "\n".join(mod.board_html(b) for b in mod.BOARDS)
    return ('<section>%s<p class="tt-intro">%s</p>\n%s</section>'
            % (sechead(eyebrow), intro, boards))


POOL = ("Ranked across pooled leagues: <b>Premier League, La Liga, Bundesliga, Serie A, "
        "Ligue 1, Liga Portugal, Eredivisie</b>.")

page = "\n".join([
    next_matches(),
    block(P, "Top players", "Season totals to date. " + POOL),
    block(T, "Top teams", "Season to date. " + POOL),
])

system_css = T.SYSTEM_CSS.read_text(encoding="utf-8")

OUT.write_text("""<!doctype html>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Home -- three blocks (mock)</title>
<style>
%s
%s
</style>

<input class="toggle" type="checkbox" id="t-light">
<input class="toggle" type="checkbox" id="t-phone">
<input class="toggle" type="checkbox" id="t-fi">

<div class="ctl">
  <label for="t-light"><span class="box"></span>Light</label>
  <label for="t-phone"><span class="box"></span>Phone 375px</label>
  <label for="t-fi"><span class="box"></span>Finnish (width probe)</label>
  <span class="hint">next matches &rarr; Top players &rarr; Top teams</span>
</div>

<div class="stage">
  <div class="fx">
    <div class="inner">
%s
    </div>
  </div>
</div>

<div class="legend">
  <b>Composition mock.</b> The order is the approved one: next matches &rarr; Top players &rarr;
  Top teams. <b>Top players and Top teams are generated from the same code as their own
  mocks</b>, so this page cannot drift from what was approved. Next matches is mocked but mirrors
  the shipped component class for class, including the fold: a competition shows three rows and
  the rest open under &ldquo;Show all&rdquo;. Every number is placeholder.
</div>
""" % (system_css, T.MOCK_CSS, page), encoding="utf-8")

print("wrote", OUT, OUT.stat().st_size, "bytes")
print("board rows:", sum(len(b["rows"]) for b in P.BOARDS) + sum(len(b["rows"]) for b in T.BOARDS))
print("fixtures:", sum(len(m) for _, dates in FIXTURES for _, m in dates))
