"""Render the COMPETITION PAGE, Overview tab -- /{locale}/{competition-slug}/ -- as standalone
mocks, one per kind of competition, to the design approved on GitLab #129.

Design-only. Reads nothing from BigQuery. The league's numbers are the Bundesliga 2026/27 after
three matchdays as the warehouse held them when the design was approved, so the page is judged
against numbers that could occur; club names are real because their WIDTH is what is tested.

FOUR KINDS, one file each (kind names as arguments, or all when none is given):
  league     a domestic league: table, next matchday, deserved points, the season in numbers
  groups     a tournament in its knockout: one table per group (the provider's ranking table
             dropped), the next round, the season in numbers; no deserved points
  cup        a knockout cup: header, next round, the season in numbers; no table
  offseason  a league between seasons: the final table, deserved points, the season in
             numbers; no next matches

Every block a page can show is here with the same class names the built components emit
(`.ctab`, `.fxrow`, `.frow`, `.comp-tabs`), and the block's CSS is system.css's own, inlined
verbatim. A block with nothing to show is absent -- no heading over nothing.

The tab bar: Overview active, the three other tabs inert labels until each page is built.

No competition crest asset: the mock draws the neutral placeholder, never a hotlink.
No JavaScript: the review surface is a static snapshot. The three toggles are :checked + sibling
combinators.
"""
import html
import re
import sys
from pathlib import Path

from gen_block_standard import short
from interaction import INTERACTION_CSS
from rows import CREST, ROW_CSS, date_head, upcoming_row

REPO = Path(__file__).resolve().parent.parent
SYSTEM_CSS = REPO / "site_v2/src/styles/system.css"

E = html.escape

# --------------------------------------------------------------- the data

# (rank, name, played, w, d, l, goals for, goals against, gd, pts, deserved, gap) -- the gap is
# actual minus deserved, the catalogue's sign.
LEAGUE_TABLE = [
    (1, "SC Freiburg", 3, 3, 0, 0, 10, 1, 9, 9, 7.2, 1.8),
    (2, "Borussia Dortmund", 3, 3, 0, 0, 8, 2, 6, 9, 6.3, 2.7),
    (3, "FC Augsburg", 3, 2, 1, 0, 9, 3, 6, 7, 5.8, 1.2),
    (4, "Bayern München", 3, 2, 1, 0, 7, 2, 5, 7, 7.4, -0.4),
    (5, "RB Leipzig", 3, 2, 0, 1, 9, 3, 6, 6, 5.8, 0.2),
    (6, "SV Elversberg", 3, 2, 0, 1, 8, 7, 1, 6, 4.4, 1.6),
    (7, "Bayer 04 Leverkusen", 3, 1, 1, 1, 8, 5, 3, 4, 6.0, -2.0),
    (8, "1. FSV Mainz 05", 3, 1, 1, 1, 6, 3, 3, 4, 6.7, -2.7),
    (9, "Eintracht Frankfurt", 3, 1, 1, 1, 7, 8, -1, 4, 2.9, 1.1),
    (10, "SV Werder Bremen", 3, 1, 1, 1, 5, 6, -1, 4, 4.0, 0.0),
    (11, "FC Schalke 04", 3, 1, 1, 1, 3, 4, -1, 4, 2.0, 2.0),
    (12, "1. FC Köln", 3, 1, 1, 1, 5, 7, -2, 4, 4.2, -0.2),
    (13, "TSG 1899 Hoffenheim", 3, 1, 0, 2, 6, 7, -1, 3, 4.9, -1.9),
    (14, "VfB Stuttgart", 3, 1, 0, 2, 6, 8, -2, 3, 3.1, -0.1),
    (15, "SC Paderborn 07", 3, 0, 1, 2, 0, 4, -4, 1, 1.1, -0.1),
    (16, "1. FC Union Berlin", 3, 0, 1, 2, 4, 10, -6, 1, 3.1, -2.1),
    (17, "Borussia Mönchengladbach", 3, 0, 0, 3, 3, 12, -9, 0, 0.0, 0.0),
    (18, "Hamburger SV", 3, 0, 0, 3, 0, 12, -12, 0, 1.5, -1.5),
]

# home, away, day, time -- the next round, every row a fixture with a page
LEAGUE_ROUND = ("Matchday 4", "4. kierros", [
    ("Bayern München", "1. FC Union Berlin", "Fri 18 Sep", "20:30"),
    ("Hamburger SV", "1. FC Köln", "Sat 19 Sep", "15:30"),
    ("Borussia Mönchengladbach", "1. FSV Mainz 05", "Sat 19 Sep", "15:30"),
    ("Eintracht Frankfurt", "SC Freiburg", "Sat 19 Sep", "15:30"),
    ("SV Werder Bremen", "FC Augsburg", "Sat 19 Sep", "15:30"),
    ("VfB Stuttgart", "Borussia Dortmund", "Sat 19 Sep", "18:30"),
    ("Bayer 04 Leverkusen", "RB Leipzig", "Sun 20 Sep", "15:30"),
    ("FC Schalke 04", "SV Elversberg", "Sun 20 Sep", "17:30"),
    ("SC Paderborn 07", "TSG 1899 Hoffenheim", "Sun 20 Sep", "19:30"),
])

# label key, value, context -- the season in numbers, the fact rows of the league
LEAGUE_FACTS = [
    ("factGoalsPerMatch", "3.9", "104 goals in 27 matches"),
    ("factHomeWins", "14 of 27", "5 draws, 8 away wins"),
    ("factBiggestMargin", "0–5", "Hamburger SV vs 1. FSV Mainz 05, Matchday 2"),
    ("factMostGoals", "3–4", "Borussia Mönchengladbach vs SV Elversberg, Matchday 2"),
    ("factLongestUnbeaten", "3 matches", "FC Augsburg, Bayern München, Borussia Dortmund, SC Freiburg"),
    ("factLongestWinless", "3 matches", "Borussia Mönchengladbach, Hamburger SV, 1. FC Union Berlin, SC Paderborn 07"),
]
LEAGUE_MATTERS = ("Eintracht Frankfurt vs SC Freiburg", "Sat 19 Sep, 15:30")

# a tournament with groups (Euro 2024 as held), in its knockout
GROUP_TABLES = {
    "Group A": [("Germany", 3, 2, 1, 0, 8, 2, 6, 7), ("Switzerland", 3, 1, 2, 0, 5, 3, 2, 5),
                ("Hungary", 3, 1, 0, 2, 2, 5, -3, 3), ("Scotland", 3, 0, 1, 2, 2, 7, -5, 1)],
    "Group B": [("Spain", 3, 3, 0, 0, 5, 0, 5, 9), ("Italy", 3, 1, 1, 1, 3, 3, 0, 4),
                ("Croatia", 3, 0, 2, 1, 3, 6, -3, 2), ("Albania", 3, 0, 1, 2, 3, 5, -2, 1)],
    "Group C": [("England", 3, 1, 2, 0, 2, 1, 1, 5), ("Denmark", 3, 0, 3, 0, 2, 2, 0, 3),
                ("Slovenia", 3, 0, 3, 0, 2, 2, 0, 3), ("Serbia", 3, 0, 2, 1, 1, 2, -1, 2)],
    "Group D": [("Austria", 3, 2, 0, 1, 6, 4, 2, 6), ("France", 3, 1, 2, 0, 2, 1, 1, 5),
                ("Netherlands", 3, 1, 1, 1, 4, 4, 0, 4), ("Poland", 3, 0, 1, 2, 3, 6, -3, 1)],
    "Group E": [("Romania", 3, 1, 1, 1, 4, 3, 1, 4), ("Belgium", 3, 1, 1, 1, 2, 1, 1, 4),
                ("Slovakia", 3, 1, 1, 1, 3, 3, 0, 4), ("Ukraine", 3, 1, 1, 1, 2, 4, -2, 4)],
    "Group F": [("Portugal", 3, 2, 0, 1, 5, 3, 2, 6), ("Türkiye", 3, 2, 0, 1, 5, 5, 0, 6),
                ("Georgia", 3, 1, 1, 1, 4, 4, 0, 4), ("Czechia", 3, 0, 1, 2, 3, 5, -2, 1)],
}
GROUP_ROUND = ("Round of 16", "Neljännesvälierät", [
    ("Switzerland", "Italy", "Sat 29 Jun", "18:00"),
    ("Germany", "Denmark", "Sat 29 Jun", "21:00"),
    ("England", "Slovakia", "Sun 30 Jun", "18:00"),
    ("Spain", "Georgia", "Sun 30 Jun", "21:00"),
    ("France", "Belgium", "Mon 1 Jul", "18:00"),
    ("Portugal", "Slovenia", "Mon 1 Jul", "21:00"),
    ("Romania", "Netherlands", "Tue 2 Jul", "18:00"),
    ("Austria", "Türkiye", "Tue 2 Jul", "21:00"),
])
GROUP_FACTS = [
    ("factGoalsPerMatch", "2.3", "81 goals in 36 matches"),
    ("factBiggestMargin", "5–1", "Germany vs Scotland, Group Stage 1"),
    ("factMostGoals", "5–1", "Germany vs Scotland, Group Stage 1"),
    ("factLongestUnbeaten", "3 matches", "Germany, Spain, Switzerland, England, Denmark, Slovenia, France, Belgium, Romania, Slovakia, Ukraine"),
    ("factLongestWinless", "3 matches", "Scotland, Albania, Denmark, Slovenia, Serbia, Poland, Czechia"),
]

# a knockout cup: no table at all
CUP_ROUND = ("Round of 32", "32 parhaan kierros", [
    ("Bayer 04 Leverkusen", "1. FC Nürnberg", "Tue 27 Oct", "18:00"),
    ("Borussia Dortmund", "SV Sandhausen", "Tue 27 Oct", "20:45"),
    ("FC St. Pauli", "Hamburger SV", "Wed 28 Oct", "18:00"),
    ("Bayern München", "1. FC Heidenheim", "Wed 28 Oct", "20:45"),
])
CUP_FACTS = [
    ("factGoalsPerMatch", "4.6", "148 goals in 32 matches"),
    ("factHomeWins", "2 of 32", "4 draws, 26 away wins"),
    ("factBiggestMargin", "0–11", "SC St. Tönis vs Eintracht Frankfurt, Round of 64"),
    ("factMostGoals", "0–11", "SC St. Tönis vs Eintracht Frankfurt, Round of 64"),
]

KINDS = {
    "league": dict(name=short("BL1"), region="Germany", season="Season 2026/27",
                   round_label="Matchday 4", tab_second="tabMatchdays", zone="CET",
                   tables={"Bundesliga": LEAGUE_TABLE}, deserved=True,
                   next_round=LEAGUE_ROUND, facts=LEAGUE_FACTS, matters=LEAGUE_MATTERS),
    "groups": dict(name="Euro 2024", region="Europe", season="Season 2024",
                   round_label="Round of 16", tab_second="tabRounds", zone="CEST",
                   tables=GROUP_TABLES, deserved=False,
                   next_round=GROUP_ROUND, facts=GROUP_FACTS, matters=None),
    "cup": dict(name="DFB-Pokal", region="Germany", season="Season 2026/27",
                round_label="Round of 32", tab_second="tabRounds", zone="CET",
                tables={}, deserved=False,
                next_round=CUP_ROUND, facts=CUP_FACTS, matters=None),
    "offseason": dict(name=short("BL1"), region="Germany", season="Season 2026/27",
                      round_label="Matchday 34", tab_second="tabMatchdays", zone="CET",
                      tables={"Bundesliga": LEAGUE_TABLE}, deserved=True,
                      next_round=None, facts=LEAGUE_FACTS, matters=None),
}

# --------------------------------------------------------------------- copy

# EN is the built copy (strings.ts, `comp*` keys). FI is a WIDTH PROBE where marked: a probe is a
# plausible worst case for measuring, NOT approved copy, and renders with a dotted underline.
COPY = {
    #  key                   en                              fi                                       fi_is_probe
    "crumbHome":           ("Home",                         "Etusivu",                               False),
    "navCompetitions":     ("Competitions",                 "Kilpailut",                             False),
    "tabOverview":         ("Overview",                     "Yleiskatsaus",                          False),
    "tabMatchdays":        ("Matchdays",                    "Kierrokset",                            False),
    "tabRounds":           ("Rounds",                       "Kierrokset",                            False),
    "tabTeams":            ("Teams",                        "Joukkueet",                             False),
    "tabPlayers":          ("Players",                      "Pelaajat",                              False),
    "secTable":            ("Table",                        "Sarjataulukko",                         False),
    "secMatches":          ("Next matches",                 "Seuraavat ottelut",                     False),
    "secDeserved":         ("Deserved points",              "Ansaitut pisteet",                      False),
    "secFacts":            ("The season in numbers",        "Kausi numeroina",                       False),
    "colPos":              ("#",                            "#",                                     False),
    "colPlayed":           ("P",                            "O",                                     False),
    "colWins":             ("W",                            "V",                                     False),
    "colDraws":            ("D",                            "T",                                     False),
    "colLosses":           ("L",                            "H",                                     False),
    "colGoals":            ("Goals",                        "Maalit",                                False),
    "colGoalDiff":         ("GD",                           "ME",                                    False),
    "colPoints":           ("Pts",                          "P",                                     False),
    "colDeserved":         ("Deserved",                     "Ansaitut",                              False),
    "colDiff":             ("Diff",                         "Ero",                                   False),
    "deservedExplainer":   ("Deserved points are the points a team's shot balance usually earns. Shot balance is shots on goal created minus shots on goal conceded. Teams with fewer points than deserved are better than the table says; teams with more are worse.",
                            "Ansaitut pisteet ovat pisteet, jotka joukkueen laukaustase yleensä tuottaa. Laukaustase on luodut laukaukset maalia kohti miinus päästetyt laukaukset maalia kohti. Joukkueet, joilla on vähemmän pisteitä kuin ansaittu, ovat parempia kuin taulukko kertoo; joukkueet, joilla on enemmän, ovat heikompia.", False),
    "secBetter":           ("Better than the table says",   "Parempia kuin taulukko kertoo",         False),
    "secWorse":            ("Worse than the table says",    "Heikompia kuin taulukko kertoo",        False),
    "factGoalsPerMatch":   ("Goals per match",              "Maalia per ottelu",                     False),
    "factHomeWins":        ("Home wins",                    "Kotivoitot",                            False),
    "factBiggestMargin":   ("Biggest margin",               "Suurin ero",                            False),
    "factMostGoals":       ("Most goals in a match",        "Eniten maaleja ottelussa",              False),
    "factLongestUnbeaten": ("Longest unbeaten run",         "Pisin tappioton putki",                 False),
    "factLongestWinless":  ("Longest winless run",          "Pisin voitoton putki",                  False),
    "factMatters":         ("The match that matters next",  "Seuraava avainottelu",                  False),
}

# --------------------------------------------------------------------- build


def slugify(name):
    """The mock's stand-in for the team slug published on dim_team; the real one is ASSIGNED in
    the warehouse, not derived here."""
    s = (name.replace("ü", "u").replace("ö", "o").replace("ä", "a")
             .replace("ß", "ss").replace(".", "").lower())
    return re.sub(r"[^a-z0-9]+", "-", s).strip("-")


def loc(key):
    """Render one copy key in both locales; CSS shows one at a time."""
    en, fi, probe = COPY[key]
    cls = "fi probe" if probe else "fi"
    return ('<span class="en">%s</span><span class="%s" lang="fi">%s</span>'
            % (E(en), cls, E(fi)))


def _cols(r):
    """(name, played, w, d, l, gf, ga, gd, pts) from a league row (rank first, deserved after)
    or a group row (nine fields)."""
    return tuple(r[1:10]) if len(r) > 9 else tuple(r)


def team_cell(name):
    """Crest + name inside the row; the ROW is the link, never the name alone."""
    return ('<span class="tm"><span class="crest xs">%s</span>'
            '<span class="nm">%s</span></span>' % (CREST, E(name)))


def header_html(k):
    return """
      <nav class="crumb">
        <a class="lnk" href="/en/">%s</a>
        <span class="sep">&rsaquo;</span>
        <a class="lnk" href="/en/competitions/">%s</a>
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
        <span class="tab on" aria-current="page">%s</span>
        <span class="tab" aria-disabled="true">%s</span>
        <span class="tab" aria-disabled="true">%s</span>
        <span class="tab" aria-disabled="true">%s</span>
      </nav>
""" % (loc("crumbHome"), loc("navCompetitions"), E(k["name"]), CREST, E(k["name"]),
       E(k["region"]), E(k["season"]), E(k["round_label"]),
       loc("tabOverview"), loc(k["tab_second"]), loc("tabTeams"), loc("tabPlayers"))


def table_html(k):
    if not k["tables"]:
        return ""
    head = ('<div class="ctab-head">'
            '<span class="h rk">%s</span><span class="h nmh"></span>'
            '<span class="h">%s</span>'
            '<span class="h wdl">%s</span><span class="h wdl">%s</span><span class="h wdl">%s</span>'
            '<span class="h wdl">%s</span>'
            '<span class="h">%s</span><span class="h">%s</span></div>'
            % (loc("colPos"), loc("colPlayed"), loc("colWins"), loc("colDraws"),
               loc("colLosses"), loc("colGoals"), loc("colGoalDiff"), loc("colPoints")))
    blocks = []
    for section, rows_ in k["tables"].items():
        rows = []
        for pos, r in enumerate(rows_, 1):
            name, played, w, d, lost, gf, ga, gd, pts = _cols(r)
            rows.append(
                '<a class="ctab-row" href="/en/teams/%s/">'
                '<span class="rk num">%d</span>%s'
                '<span class="n num">%d</span>'
                '<span class="n num wdl">%d</span><span class="n num wdl">%d</span>'
                '<span class="n num wdl">%d</span>'
                '<span class="n num wdl">%d:%d</span>'
                '<span class="n num gd">%s</span><span class="n num pts">%d</span>'
                '</a>' % (slugify(name), pos, team_cell(name), played, w, d, lost, gf, ga,
                          ("+%d" % gd) if gd > 0 else str(gd), pts))
        heading = ('<div class="gh"><span class="nm">%s</span></div>' % E(section)
                   if len(k["tables"]) > 1 else "")
        blocks.append('<div class="ctab-section">%s<div class="ctab">%s\n%s</div></div>'
                      % (heading, head, "\n".join(rows)))
    return """
      <section>
        <div class="sechead"><span class="eyebrow">%s</span></div>
%s
      </section>
""" % (loc("secTable"), "\n".join(blocks))


def matches_html(k):
    if not k["next_round"]:
        return ""
    _en, _fi, upcoming = k["next_round"]
    body = []
    for date in dict.fromkeys(day for _h, _a, day, _t in upcoming):
        body.append(date_head(date))
        for home, away, day, time in upcoming:
            if day == date:
                body.append(upcoming_row("club", home, away, time, k["zone"]))
    return """
      <section>
        <div class="sechead"><span class="eyebrow">%s</span></div>
        <div class="fxgroup">
%s
        </div>
      </section>
""" % (loc("secMatches"), "\n".join(body))


def deserved_html(k):
    if not k["deserved"]:
        return ""
    table = next(iter(k["tables"].values()))
    ordered = sorted(table, key=lambda r: r[11])
    boards = [("secBetter", ordered[:3]), ("secWorse", list(reversed(ordered[-3:])))]
    out = []
    for key, rows_ in boards:
        rows = ['<div class="ctab-head"><span class="h nmh"></span><span class="h">%s</span>'
                '<span class="h">%s</span><span class="h">%s</span></div>'
                % (loc("colDeserved"), loc("colPoints"), loc("colDiff"))]
        for r in rows_:
            gap = r[11]
            sign = "+" if gap > 0 else ("−" if gap < 0 else "")
            rows.append('<a class="ctab-row" href="/en/teams/%s/">%s'
                        '<span class="n num">%.1f</span><span class="n num">%d</span>'
                        '<span class="n num pts">%s%.1f</span></a>'
                        % (slugify(r[1]), team_cell(r[1]), r[10], r[9], sign, abs(gap)))
        out.append('<div class="board"><div class="bhd"><span class="bt">%s</span></div>'
                   '<div class="ctab dp">%s</div></div>' % (loc(key), "".join(rows)))
    return """
      <section>
        <div class="sechead"><span class="eyebrow">%s</span></div>
        <p class="bsub">%s</p>
%s
      </section>
""" % (loc("secDeserved"), loc("deservedExplainer"), "\n".join(out))


def facts_html(k):
    rows = []
    for key, value, context in k["facts"]:
        rows.append('<div class="frow"><span class="fl">%s</span><span class="fv">'
                    '<span class="fvv"><b>%s</b></span><span class="sub">%s</span></span></div>'
                    % (loc(key), E(value), E(context)))
    if k["matters"]:
        match, when = k["matters"]
        rows.append('<a class="frow" href="#"><span class="fl">%s</span><span class="fv">'
                    '<span class="fvv"><b>%s</b></span><span class="sub">%s</span></span></a>'
                    % (loc("factMatters"), E(match), E(when)))
    if not rows:
        return ""
    return """
      <section>
        <div class="sechead"><span class="eyebrow">%s</span></div>
        <div class="facts">
%s
        </div>
      </section>
""" % (loc("secFacts"), "\n".join(rows))


MOCK_CSS = """
/* ---------------------------------------------------------------- *
 *  MOCK HARNESS ONLY -- not part of the design.                      *
 * ---------------------------------------------------------------- */
body { margin: 0; background: #06070a; font: 400 15px/1.5 system-ui, -apple-system, "Segoe UI", Roboto, sans-serif; }
.ctl { position: sticky; top: 0; z-index: 9; display: flex; flex-wrap: wrap; gap: 18px;
       padding: 12px 16px; background: #14161c; border-bottom: 1px solid #2b2f38; color: #c7ccd4; font-size: 13px; }
.ctl label { display: inline-flex; align-items: center; gap: 7px; cursor: pointer; user-select: none; }
.ctl .hint { color: #7c828c; font-size: 12px; }
.toggle { position: absolute; width: 1px; height: 1px; opacity: 0; pointer-events: none; }
.ctl .box { width: 15px; height: 15px; border-radius: 4px; border: 1px solid #4a505b; background: #0d0f13; flex: 0 0 auto; }
#t-light:checked ~ .ctl label[for="t-light"] .box,
#t-phone:checked ~ .ctl label[for="t-phone"] .box,
#t-fi:checked    ~ .ctl label[for="t-fi"]    .box { background: #3bb072; border-color: #3bb072; }
.toggle:focus-visible ~ .ctl label .box { outline: 2px solid #3bb072; outline-offset: 2px; }
.stage { margin: 0 auto; transition: max-width .15s; }
.legend { max-width: 680px; margin: 0 auto; padding: 14px 16px 40px; color: #7c828c; font-size: 12px; line-height: 1.6; }
.legend b { color: #c7ccd4; }

#t-phone:checked ~ .stage { max-width: 375px; box-shadow: 0 0 0 1px #2b2f38; }

#t-light:checked ~ .stage .fx {
  --page: #f3f3f0; --surface: #fbfbf9; --sunk: #edece7; --line: #e2e1da; --div: #cfcec5;
  --ink: #141410; --ink-2: #4c4c45; --muted: #77776e;
  --accent: #0a6e3a;
  --win: #157f43; --draw: #6f756d; --loss: #b23b3b; --pill-ink: #fff;
  --track: #e7e6e0;
}

.fi { display: none; }
#t-fi:checked ~ .stage .en { display: none; }
#t-fi:checked ~ .stage .fi { display: inline; }
#t-fi:checked ~ .stage .probe { text-decoration: underline dotted currentColor; text-underline-offset: 3px; }

.crest svg { width: 26px; height: 26px; display: block; color: var(--muted); }
.crest.xs svg { width: 15px; height: 15px; }
"""


def build(kind):
    k = KINDS[kind]
    return """<!doctype html>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Competition page, Overview -- %s (mock)</title>
<style>
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
%s
%s
    </div>
  </div>
</div>

<div class="legend">
  <b>Mock &mdash; the competition page, Overview tab, kind &ldquo;%s&rdquo;.</b>
  Table &middot; Next matches &middot; Deserved points &middot; The season in numbers, each only
  where its mart serves something. The design is GitLab #129; this file renders it.
</div>
""" % (kind, SYSTEM_CSS.read_text(encoding="utf-8"), ROW_CSS, INTERACTION_CSS, MOCK_CSS,
       header_html(k), table_html(k), matches_html(k), deserved_html(k), facts_html(k), kind)


def check_data():
    """Placeholder or not, every table has to be a LEGAL table."""
    for kind, k in KINDS.items():
        for section, rows_ in k["tables"].items():
            prev_pts = None
            gd_total = 0
            for r in rows_:
                name, played, w, d, lost, gf, ga, gd, pts = _cols(r)
                assert w + d + lost == played, "%s/%s: W+D+L != played" % (kind, name)
                assert 3 * w + d == pts, "%s/%s: points != 3W+D" % (kind, name)
                assert gf - ga == gd, "%s/%s: goals do not give the goal difference" % (kind, name)
                assert prev_pts is None or pts <= prev_pts, "%s/%s: not ordered by points" % (kind, name)
                prev_pts = pts
                gd_total += gd
            assert gd_total == 0, "%s/%s: goal differences sum to %d" % (kind, section, gd_total)
    print("  table invariants hold for every kind")


def out_path(kind):
    return Path(__file__).with_name("competition_hub_mock_%s.html" % kind)


if __name__ == "__main__":
    check_data()
    wanted = sys.argv[1:] or list(KINDS)
    for kind in wanted:
        path = out_path(kind)
        path.write_text(build(kind), encoding="utf-8")
        print("  wrote %s (%.0f KB)" % (path.name, path.stat().st_size / 1024))
