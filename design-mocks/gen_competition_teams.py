"""Render the COMPETITION PAGE, Rankings tab, as a standalone mock for the review on GitLab #129.

Real data: every Bundesliga 2026/27 club's season metrics from prod mart_team_profile, its
season card totals summed from fct_fixture_team_stats, and every player's season metrics from
prod mart_player_profile, pulled read-only. The README dates the pulls. The boards are ranked
here the way mart_team_leaderboards ranks (dense rank by the catalogue's direction).

Imports the shared pieces from design-mocks so nothing here is drawn fresh.
"""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
sys.path.insert(0, str(HERE))

from gen_competition_hub import COPY, E, MOCK_CSS, SYSTEM_CSS, loc, slugify, team_cell  # noqa: E402
from gen_top_teams import FI, board_title, label  # noqa: E402
from interaction import CHEVRON, INTERACTION_CSS  # noqa: E402
from rows import CREST, ROW_CSS  # noqa: E402

COPY.update({
    "tabTeamsHere":   ("Rankings", "Rankingit", True),
    "tabPlayers":     ("Players", "Pelaajat", False),
    "secDeservedFull": ("Deserved points", "Ansaitut pisteet", False),
    "colTablePos":    ("Table", "Sija", True),
    "secTopTeams":    ("Top teams", "Parhaat joukkueet", True),
    "boardMore":      ("Full list", "Koko lista", True),
    "grpGoals":       ("Goals", "Maalit", True),
    "grpShooting":    ("Shooting", "Laukominen", True),
    "grpPassing":     ("Passing", "Syöttäminen", True),
    "grpDefending":   ("Defending", "Puolustaminen", True),
    "grpDuels":       ("One-on-one", "Yksi vastaan yksi", False),
    "fewestFirst":    ("fewest first", "vähiten ensin", True),
    "grpDiscipline":  ("Discipline", "Kurinpito", True),
    "grpGoalkeeping": ("Goalkeeping", "Maalivahtipeli", True),
    "secTeamRankings": ("Team rankings", "Tiimirankingit", False),
    "secPlayerRankings": ("Player rankings", "Pelaajarankingit", False),
})

METRICS_FILE = HERE / "bl1_team_metrics.json"
# the approved board set, in its groups and order; the mock ranks from mart_team_profile
# the way mart_team_leaderboards would (dense rank by the catalogue's direction, first three by
# value then name)
GROUPS = [
    ("grpGoals",     ["goals_per_match", "goals_against_per_match"]),
    ("grpShooting",  ["shots_on_goal_per_match", "shots_on_goal_against_per_match",
                      "shots_on_goal_difference_per_match"]),
    ("grpPassing",   ["passes_per_match", "passes_accuracy_pct"]),
    ("grpDefending", ["defensive_actions_per_match"]),
    ("grpDuels",     ["duels_per_match", "duels_won_pct"]),
    ("grpDiscipline", ["cards_yellow", "cards_red"]),
]
TOP = 5

# NOT IN THE CATALOGUE YET: two team metrics the approved design calls for (season totals,
# ranked most first). Their catalogue rows are a build item; the mock carries the proposed
# label and format so the boards can be seen. Source: fct_fixture_team_stats summed over FT.
PROPOSED = {
    "cards_yellow": {"label_en": "Yellow cards", "label_fi": "Keltaiset kortit", "format": "integer",
                     "direction": "higher_better"},
    "cards_red":    {"label_en": "Red cards", "label_fi": "Punaiset kortit", "format": "integer",
                     "direction": "higher_better"},
}
CARDS_FILE = HERE / "bl1_team_cards.json"


def header_html(name):
    return """
      <nav class="crumb">
        <a class="lnk" href="/en/">%s</a>
        <span class="sep">&rsaquo;</span>
        <a class="lnk" href="/en/competitions/">%s</a>
        <span class="sep">&rsaquo;</span>
        <a class="lnk" href="/en/bundesliga/">%s</a>
        <span class="sep">&rsaquo;</span>
        <span class="here">%s</span>
      </nav>

      <header class="thead">
        <div class="crest">%s</div>
        <div class="tid">
          <h1>%s</h1>
          <div class="meta">%s &middot; %s &middot; %s</div>
        </div>
      </header>

      <nav class="tabs comp-tabs" aria-label="Competition sections">
        <a class="tab" href="/en/bundesliga/">%s</a>
        <a class="tab" href="/en/bundesliga/fixtures/">%s</a>
        <span class="tab on" aria-current="page">%s</span>
      </nav>

""" % (loc("crumbHome"), loc("navCompetitions"), E(name), loc("tabTeamsHere"), CREST, E(name),
       "Germany", "Season 2026/27", "Matchday 4",
       loc("tabOverview"), loc("tabMatchdays"), loc("tabTeamsHere"))


def catalogue_row(key):
    from gen_top_teams import _BY_KEY
    if key in PROPOSED:
        return PROPOSED[key]
    return _BY_KEY[(key, "team")]


def fmt(key, v):
    f = catalogue_row(key)["format"]
    if f == "percent":
        return "%.0f%%" % (v * 100)
    if f == "decimal_1":
        return "%.1f" % v
    if f == "count_fraction":
        return "%d" % v
    return "%.0f" % v


def load_boards():
    """Rank all 18 on each board from mart_team_profile: dense rank by the catalogue's direction,
    the first three by value then name (the tie-broken order the leaderboard mart carries)."""
    teams = json.loads(METRICS_FILE.read_bytes().decode("utf-8"))
    cards = {c["team_slug"]: c for c in json.loads(CARDS_FILE.read_bytes().decode("utf-8"))}
    for t in teams:
        t.update({k: cards[t["team_slug"]][k] for k in PROPOSED})
    out = {}
    for _grp, keys in GROUPS:
        for key in keys:
            lower = catalogue_row(key)["direction"] == "lower_better"
            vals = [(float(t[key]), t["team_name"], t["team_slug"]) for t in teams if t[key] is not None]
            vals.sort(key=lambda x: ((x[0] if lower else -x[0]), x[1]))
            distinct = sorted({v for v, _n, _s in vals}, reverse=not lower)
            rank = {v: i + 1 for i, v in enumerate(distinct)}
            if not lower:
                vals = [x for x in vals if x[0] > 0]
            out[key] = [(rank[v], n, s, v) for v, n, s in vals[:TOP]]
    return out


def board_html(key, boards):
    if key in PROPOSED:
        title_en, title_fi = PROPOSED[key]["label_en"], PROPOSED[key]["label_fi"]
    else:
        lab = label(key)
        title_en = board_title(key, lab, "en")
        fi_lab = FI.get(key, (lab, True))[0]
        title_fi = board_title(key, fi_lab, "fi") if fi_lab.startswith("Ø ") == lab.startswith("Ø ") else fi_lab
    lower = catalogue_row(key)["direction"] == "lower_better"
    note = ' <span class="bnote">(%s)</span>' % loc("fewestFirst") if lower else ""
    rows = []
    for rank, name, slug, value in boards[key]:
        rows.append('<a class="ctab-row" href="/en/teams/%s/"><span class="rk num">%d</span>%s'
                    '<span class="n num pts">%s</span></a>'
                    % (slug, rank, team_cell(name), fmt(key, value)))
    return ('<div class="board"><div class="ctab rkt"><div class="ctab-head"><span class="h rk"></span>'
            '<span class="h nmh"><a class="bt cnm" href="/en/leaderboards/bundesliga/%s/">'
            '<span class="nm"><span class="en">%s</span><span class="fi probe" lang="fi">%s</span></span>%s</a>%s</span>'
            '<span class="h"></span></div>%s</div></div>'
            % (key.replace("_", "-"), E(title_en), E(title_fi), CHEVRON, note, "".join(rows)))


def boards_html(boards):
    """Block 1, Team rankings: the groups inside the block under the Table block's group heading
    (the one over "Group A"), every board's name a link to the full list (#140)."""
    parts = []
    for grp, keys in GROUPS:
        parts.append('<div class="fxgroup rkgroup"><div class="gh"><span class="nm">%s</span></div>%s</div>'
                     % (loc(grp), "\n".join(board_html(k, boards) for k in keys)))
    return """
      <section>
        <div class="sechead"><span class="eyebrow">%s</span></div>
%s
      </section>
""" % (loc("secTeamRankings"), "\n".join(parts))


# ---- the player half: the approved 17 boards in seven groups ----
PLAYER_GROUPS = [
    ("grpGoals",       ["goals_player", "assists_player"]),
    ("grpShooting",    ["shots_on_goal_player", "finishing_efficiency_player_pct"]),
    ("grpPassing",     ["passes_player", "passes_key_player", "passes_accuracy_player_pct"]),
    ("grpDuels",       ["dribbles_attempts_player", "duels_player"]),
    ("grpDefending",   ["defensive_actions_player"]),
    ("grpDiscipline",  ["cards_yellow_player", "cards_red_player"]),
    ("grpGoalkeeping", ["saves_player"]),
]
PLAYERS_FILE = HERE / "bl1_player_metrics.json"
# the leaderboard mart's rate rules: minutes >= 270, a shots-on-goal floor for finishing; the
# position scope (outfield / goalkeeper) is not in this pull and is noted as such
RATE_MIN_MINUTES = 270
RATE_FLOORS = {"finishing_efficiency_player_pct": ("shots_on_goal_player", 10)}
MOST_FIRST_OVERRIDE = {"cards_yellow_player", "cards_red_player"}


def player_row(key):
    from gen_top_teams import _BY_KEY
    return _BY_KEY[(key, "player")]


def load_player_boards():
    players = json.loads(PLAYERS_FILE.read_bytes().decode("utf-8"))
    out = {}
    for _grp, keys in PLAYER_GROUPS:
        for key in keys:
            row = player_row(key)
            lower = row["direction"] == "lower_better" and key not in MOST_FIRST_OVERRIDE
            pool = [p for p in players if p[key] is not None]
            if row["format"] == "percent":
                pool = [p for p in pool if int(p["minutes"]) >= RATE_MIN_MINUTES]
                if key in RATE_FLOORS:
                    col, floor = RATE_FLOORS[key]
                    pool = [p for p in pool if int(p[col]) >= floor]
            vals = [(float(p[key]), p["player_name"], p["team_name"]) for p in pool]
            vals.sort(key=lambda x: ((x[0] if lower else -x[0]), x[1]))
            distinct = sorted({v for v, _n, _t in vals}, reverse=not lower)
            rank = {v: i + 1 for i, v in enumerate(distinct)}
            if not lower:
                vals = [x for x in vals if x[0] > 0]
            out[key] = [(rank[v], n, tm, v) for v, n, tm in vals[:TOP]]
    return out


def pfmt(key, v):
    f = player_row(key)["format"]
    if f == "percent":
        return "%.0f%%" % (v * 100)
    if f == "decimal_1":
        return "%.1f" % v
    return "%.0f" % v


def player_board_html(key, boards):
    if not boards[key]:
        return ""
    lab = label(key, "player")
    rows = []
    for rank, name, team, value in boards[key]:
        rows.append('<a class="ctab-row" href="/en/players/%s/"><span class="rk num">%d</span>'
                    '<span class="tm"><span class="crest xs">%s</span><span class="ent"><span class="nm">%s</span>'
                    '<span class="sub">%s</span></span></span><span class="n num pts">%s</span></a>'
                    % (slugify(name), rank, CREST, E(name), E(team), pfmt(key, value)))
    return ('<div class="board"><div class="ctab rkt"><div class="ctab-head"><span class="h rk"></span>'
            '<span class="h nmh"><a class="bt cnm" href="/en/leaderboards/bundesliga/%s/">'
            '<span class="nm"><span class="en">%s</span><span class="fi probe" lang="fi">%s</span></span>%s</a></span>'
            '<span class="h"></span></div>%s</div></div>'
            % (key.replace("_", "-"), E(lab), E(lab), CHEVRON, "".join(rows)))


def player_boards_html(boards):
    """Block 2, Player rankings: the same structure as the team half; a board nobody qualifies
    for is absent (the nothing-renders-empty rule)."""
    parts = []
    for grp, keys in PLAYER_GROUPS:
        inner = "\n".join(player_board_html(k, boards) for k in keys)
        if inner.strip():
            parts.append('<div class="fxgroup rkgroup"><div class="gh"><span class="nm">%s</span></div>%s</div>'
                         % (loc(grp), inner))
    return """
      <section>
        <div class="sechead"><span class="eyebrow">%s</span></div>
%s
      </section>
""" % (loc("secPlayerRankings"), "\n".join(parts))


TAB_CSS = """
/* ---- Teams tab: one new track list for the full deserved table (# · club · Table · Deserved · Pts · Diff) ---- */
.ctab.dpf, .ctab.dpf.ctab { --cols: 2rem minmax(0, 1fr) 3rem 4.6rem 2.8rem 3.4rem; }
/* the ordered-by number: bold, 15px, the accent, as the standings Pts (one rule, every block) */
.brow .v b { color: var(--accent); }
/* the block name, a step larger everywhere (was 11px): it got buried */
.sechead .eyebrow { font-size: 13px; }
/* the metric group inside a rankings block: the Matches page level-1 group heading (17px, 2px rule), unchanged */
.rkgroup .board:first-of-type { margin-top: 14px; }
/* the 14px rule: block name to its first line is the heading gap alone */
section > .sechead + .fxgroup { margin-top: 0; }
/* the page title under the tab bar: the page name in full (the tab label is the short form) */
.ptitle { font-size: 17px; font-weight: 700; color: var(--ink); line-height: 1.2; margin: 26px 0 0; }
/* the tab bar fits four tabs in one row at 375px in every language: the tabs share the width, the
   side padding is what the label needs, not 16px each side */
.comp-tabs { display: flex; }
.comp-tabs .tab { flex: 1 1 auto; text-align: center; padding-inline: clamp(6px, 2cqw, 16px); }
@container (max-width: 430px) { .comp-tabs .tab { font-size: 13px; letter-spacing: -.01em; } }
.brow .ent .nm { white-space: normal; }
/* the group heading over its boards is the standings' group heading, `.ctab-section` + `.gh`
   from system.css, unchanged: the group carries that class and no rule of its own */
.bnote { font-size: 12px; color: var(--muted); margin-left: 6px; }
.board .bhd a.cnm { display: inline-flex; align-items: center; gap: 6px; }
/* a ranking is a table: the Table block's striped rows and grid (# · crest name · value), one
   fixed track list; the board title is the table's head, its rule the only line */
.ctab.rkt, .ctab.rkt.ctab { --cols: 2rem minmax(0, 1fr) 3.6rem; margin-top: 0; }
.ctab.rkt .ctab-row { border-bottom: 0; }
.ctab.rkt .tm .ent { display: flex; flex-direction: column; min-width: 0; }
.ctab.rkt .tm .ent .sub { font-size: 12px; color: var(--muted); line-height: 1.2; }
/* the metric group keeps its size and its air, loses its rule: lines mean a table's head only */
.rkgroup > .gh { border-bottom: 0; padding-bottom: 0; }
.ctab.rkt .ctab-head { padding-bottom: 7px; }
.ctab.rkt .ctab-head .nmh { text-align: left; padding-left: 0; grid-column: 1 / 3; }
.ctab.rkt .ctab-head .rk { display: none; }
.ctab.rkt .ctab-head .nmh .bt .nm { font-size: 14px; font-weight: 700; color: var(--ink); letter-spacing: 0; text-transform: none; }
/* on a striped table the hover is twice the stripe, or it cannot be seen (the Table too) */
@media (hover: hover) { .fx a.brow:hover, .fx a.comp-row:hover, .fx a.fxrow:hover, .fx a.ctab-row:hover, .fx a.frow:hover { background: color-mix(in srgb, var(--ink) 11%, transparent); } }
"""


def build():
    boards = load_boards()
    return """<!doctype html>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Competition page, Teams -- Bundesliga (mock)</title>
<style>
%s
%s
%s
%s
%s
</style>

<input class="toggle" type="checkbox" id="t-light">
<input class="toggle" type="checkbox" id="t-phone">
<input class="toggle" type="checkbox" id="t-fi">

<div class="ctl">
  <label for="t-light"><span class="box"></span>Light</label>
  <label for="t-phone"><span class="box"></span>Phone 375px</label>
  <label for="t-fi"><span class="box"></span>Finnish</label>
  <span class="hint">no JS &middot; toggles are :checked + sibling combinators</span>
</div>

<div class="stage">
  <div class="fx">
    <div class="inner">
%s
%s
%s
    </div>
  </div>
</div>

<div class="legend">
  <b>Mock &mdash; the competition page, Teams tab (proposal for #129).</b>
  Real data: deserved points for all 18 clubs as exported 2026-09-16; the four boards from the
  warehouse the same day, top 3 with ties as the warehouse ranks them (three matchdays played).
</div>
""" % (SYSTEM_CSS.read_text(encoding="utf-8"), ROW_CSS, INTERACTION_CSS, MOCK_CSS, TAB_CSS,
       header_html("Bundesliga"), boards_html(boards), player_boards_html(load_player_boards()))


if __name__ == "__main__":
    out = HERE / (sys.argv[1] if len(sys.argv) > 1 else "competition_teams_mock_v1.html")
    out.write_text(build(), encoding="utf-8")
    print("wrote", out, "%.0f KB" % (out.stat().st_size / 1024))
