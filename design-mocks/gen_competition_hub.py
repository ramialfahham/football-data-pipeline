"""Render the COMPETITION HUB page -- /{locale}/{competition-slug}/ -- as a standalone mock.

Design-only. Reads nothing from BigQuery; every number is PLACEHOLDER.

The page does not exist. site_v2/src/pages holds home, [competition]/matches/[fixture] and
teams/[team]; the competition itself has no page, which is why the browse chips on the home
page are inert <span> and why BOTH shipped entity specs declare an inbound_hub that resolves
to nothing:

    teams/team.spec.json                    "inbound_hub": "competition"
    competition/matches/fixture.spec.json   "inbound_hub": "competition"

So this page's first job is structural: it is the hub those two declarations already promise.

TWO BLOCKS, in the CPO's order (2026-08-10): next matches, then the table.

⚠ A top-scorers board was in the first draft and was CUT. Leaderboards are not homeless --
site_architecture.md reserves /{competition-slug}/top-scorers/ and content_architecture.md's
competition tab set has a Scorers tab -- so a 7-row board on the hub was a teaser for a page
that does not exist, which is the browse-chip 404 one layer up. It also picked ONE of the nine
boards mart_leaderboards already produces per competition-season, with no ruling behind the
pick. The hub links to that page when it is built; it does not preview it.

⚠ Consequence worth knowing: with the board gone this page renders NO metric_catalogue metric
at all. The table's column headers are page chrome (the catalogue has no played/wins/draws/
losses/goal-difference row, and its one `points_won` row is the SYNTHETIC 3-1-0 tally, a
different number from the provider standings points this table shows). So there is deliberately
no catalogue lookup in this file -- not an omission, and nothing to leave scaffolded for it.

site_v2/src/styles/system.css is inlined verbatim, so the mock uses the shipped design system
rather than a lookalike.

No JavaScript: the review surface is a static snapshot, so script never runs. The three toggles
are :checked + sibling combinators.
"""
import html
import re
from pathlib import Path

# ⚠ `result_row` is deliberately NOT imported. The hub carries no played fixtures any more
# (CPO 2026-08-10) — importing it "in case" is the scaffolding that reads as a live feature.
from gen_block_standard import short
from interaction import INTERACTION_CSS
from rows import CREST, ROW_CSS, date_head, upcoming_row

REPO = Path(__file__).resolve().parent.parent
SYSTEM_CSS = REPO / "site_v2/src/styles/system.css"
OUT = Path(__file__).with_name("competition_hub_mock.html")

# --------------------------------------------------------------- sample data
#
# PLACEHOLDER. Bundesliga 2024-25 shape at matchday 24: real club names (their WIDTH is the
# thing being tested -- "Borussia Monchengladbach" is the longest team name in the twelve
# active competitions' top flights) with invented but internally consistent numbers.
# check_competition_hub.py asserts the invariants: W+D+L == played, points == 3W+D, and the
# goal differences sum to zero.

COMPETITION = {
    # \u26a0 the SHORT name, from the one source the block standard uses -- not the registry's legal
    # form ("1. Fu\u00dfball-Bundesliga"), which the CPO rejected on 2026-08-10.
    "name": short("BL1"),
    "country": "Germany",
    "tier": 1,
    "season_label": "2024-25",
    "slug": "bundesliga",
    # venue-local (CPO 2026-08-10). A single-country domestic league has ONE zone, so it is
    # declared once in the header and never repeated on a row. ⚠ Not true for every
    # competition: MLS spans four US zones and Liga MX three, and a national-team competition
    # is played in whichever nation is at home -- those declare the zone per row instead.
    "zone": "CET",
}

# team, played, W, D, L, GD, points
TABLE = [
    ("Bayern M\u00fcnchen",            24, 18, 4,  2,  51, 58),
    ("Bayer 04 Leverkusen",            24, 15, 6,  3,  30, 51),
    ("Eintracht Frankfurt",            24, 13, 6,  5,  19, 45),
    ("Borussia Dortmund",              24, 11, 5,  8,  12, 38),
    ("RB Leipzig",                     24, 10, 7,  7,   6, 37),
    ("SC Freiburg",                    24, 10, 6,  8,  -2, 36),
    ("1. FSV Mainz 05",                24, 10, 5,  9,   4, 35),
    ("Werder Bremen",                  24,  9, 6,  9,  -5, 33),
    ("VfB Stuttgart",                  24,  9, 5, 10,   2, 32),
    ("Borussia M\u00f6nchengladbach",  24,  8, 7,  9,  -3, 31),
    ("VfL Wolfsburg",                  24,  8, 6, 10,   1, 30),
    ("FC Augsburg",                    24,  8, 5, 11,  -8, 29),
    ("Union Berlin",                   24,  7, 6, 11, -12, 27),
    ("FC St. Pauli",                   24,  7, 4, 13, -13, 25),
    ("TSG Hoffenheim",                 24,  6, 6, 12, -18, 24),
    ("1. FC Heidenheim",               24,  5, 5, 14, -21, 20),
    ("VfL Bochum",                     24,  4, 6, 14, -20, 18),
    ("Holstein Kiel",                  24,  4, 5, 15, -23, 17),
]

# home, away, kickoff day, kickoff time -- the NEXT round, so every row has a fixture page
NEXT_ROUND = ("Matchday 25", "25. kierros", [
    ("Bayern M\u00fcnchen", "VfB Stuttgart", "Fri 28 Feb", "20:30"),
    ("Borussia M\u00f6nchengladbach", "SC Freiburg", "Sat 1 Mar", "15:30"),
    ("Union Berlin", "Bayer 04 Leverkusen", "Sat 1 Mar", "15:30"),
    ("FC Augsburg", "Werder Bremen", "Sat 1 Mar", "15:30"),
    ("1. FC Heidenheim", "Holstein Kiel", "Sat 1 Mar", "15:30"),
    ("VfL Bochum", "RB Leipzig", "Sat 1 Mar", "18:30"),
    ("Eintracht Frankfurt", "TSG Hoffenheim", "Sun 2 Mar", "15:30"),
    ("1. FSV Mainz 05", "Borussia Dortmund", "Sun 2 Mar", "17:30"),
    ("FC St. Pauli", "VfL Wolfsburg", "Sun 2 Mar", "19:30"),
])

# \u26a0 A LAST_ROUND results block was here and is GONE (CPO 2026-08-10). Past matches belong on
# the competition's own results page, the same ruling that gives the Matches page a separate
# Past view. Kept as a note rather than commented-out data: dead data left in place is what a
# later reader restores by accident.

# --------------------------------------------------------------------- copy
#
# EN is the proposal. FI is a WIDTH PROBE: none of these keys exists in strings.ts yet, so
# every Finnish string below is a plausible worst case for measuring, NOT approved copy --
# rendered with a dotted underline. `crumbHome` / `crumbMatches` DO exist ("Etusivu",
# "Ottelut") and are marked as real.

COPY = {
    #  key            en                 fi                            fi_is_probe
    "crumbHome":     ("Home",            "Etusivu",                    False),
    "secMatches":    ("Next matches",    "Seuraavat ottelut",          True),
    "secTable":      ("Table",           "Sarjataulukko",              True),
    "colPos":        ("#",               "#",                          False),
    "colPlayed":     ("P",               "O",                          True),
    "colWins":       ("W",               "V",                          True),
    "colDraws":      ("D",               "T",                          True),
    "colLosses":     ("L",               "H",                          True),
    "colGoalDiff":   ("GD",              "ME",                         True),
    "colPoints":     ("Pts",             "P",                          True),
}

# The narrative line. site_architecture.md section 6 REQUIRES a data-to-text sentence per page
# (anti-thin-content, generated in the export from real mart values) -- it is not decoration
# invented to fill the top of the page. Every fact in it is a mart_standings column.
LEDE_EN = ("<b>{leader}</b> lead after {played} matches, "
           "{gap} points clear of <b>{second}</b>.")
LEDE_FI = ("<b>{leader}</b> johtaa {played} ottelun j\u00e4lkeen, "
           "{gap} pistett\u00e4 edell\u00e4 joukkuetta <b>{second}</b>.")

# --------------------------------------------------------------------- build

E = html.escape

# ⚠ CREST and both match-row builders are IMPORTED from `rows.py`, not defined here. The CPO
# ruled on 2026-08-10 that a match must display identically on every page, and four different
# treatments were in the tree. One module, imported by every mock, is what makes that true by
# construction; `check_row_consistency.py` proves the rendered markup matches.


def slugify(name):
    """The mock's stand-in for the team slug published on dim_team. Good enough for an href
    in a static mock; the real one folds to the base letter per site_architecture.md section 3
    and is ASSIGNED in the warehouse, not derived here (#852)."""
    s = (name.replace("\u00fc", "u").replace("\u00f6", "o").replace("\u00e4", "a")
             .replace("\u00df", "ss").replace(".", "").lower())
    return re.sub(r"[^a-z0-9]+", "-", s).strip("-")


def loc(key):
    """Render one copy key in both locales; CSS shows one at a time."""
    en, fi, probe = COPY[key]
    cls = "fi probe" if probe else "fi"
    return ('<span class="en">%s</span><span class="%s" lang="fi">%s</span>'
            % (E(en), cls, E(fi)))


def team_cell(name):
    """A team name is a LINK on every row of the table -- that is the hub's whole job.
    THE NAME MUST NEVER TRUNCATE, so `.nm` here overrides system.css's ellipsis."""
    return ('<a class="tm" href="/en/teams/%s/"><span class="crest xs">%s</span>'
            '<span class="nm">%s</span></a>' % (slugify(name), CREST, E(name)))


def header_html():
    leader, second = TABLE[0], TABLE[1]
    lede = {
        "en": LEDE_EN.format(leader=E(leader[0]), played=leader[1],
                             gap=leader[6] - second[6], second=E(second[0])),
        "fi": LEDE_FI.format(leader=E(leader[0]), played=leader[1],
                             gap=leader[6] - second[6], second=E(second[0])),
    }
    return """
      <nav class="crumb">
        <a class="lnk" href="/en/">%s</a>
        <span class="sep">&rsaquo;</span>
        <span class="here">%s</span>
      </nav>

      <header class="chead">
        <h1>%s</h1>
        <p class="meta">%s <span class="dot">&middot;</span> Tier %d
           <span class="dot">&middot;</span> <b>%s</b></p>
      </header>

      <div class="lede">
        <p><span class="en">%s</span><span class="fi probe" lang="fi">%s</span></p>
      </div>
""" % (loc("crumbHome"), E(COMPETITION["name"]), E(COMPETITION["name"]),
       E(COMPETITION["country"]), COMPETITION["tier"], E(COMPETITION["season_label"]),
       lede["en"], lede["fi"])
# ⚠ NO timezone line in this header. It had one, and that plus the Matches page's per-row zone
# was two placements of one idea. The zone is on the row, everywhere (CPO 2026-08-10).


def matches_html():
    _up_en, _up_fi, upcoming = NEXT_ROUND

    # ⚠ THE SHARED BLOCK, from `rows.py` -- the same functions the home page and the Matches
    # page call. Kick-off is venue-local with the zone on every row.
    #
    # ⚠ NO `group_head` CALL. The block's level 1 is the competition, and on this page the
    # competition is the <h1> -- an earlier version rendered "Bundesliga" as a group heading
    # directly beneath "Bundesliga". A block may OMIT a level the page already supplies; it may
    # never MOVE information between slots. So here the block starts at level 2, the date.
    body = []
    for date in dict.fromkeys(day for _h, _a, day, _t in upcoming):
        body.append(date_head(date))
        for home, away, day, time in upcoming:
            if day == date:
                body.append(upcoming_row("club", home, away, time, COMPETITION["zone"]))

    return """
      <section>
        <div class="sechead"><span class="eyebrow">%s</span></div>

        <div class="fxgroup">
%s
        </div>
        <p class="bnote">The NEXT round only. ⚠ A &ldquo;latest results&rdquo; group was here
           and was cut (CPO 2026-08-10): past matches belong on the competition's own results
           page, the same ruling that gives the Matches page a separate Past view. Nothing on
           this page is a played fixture, so nothing on it is inert.</p>
      </section>
""" % (loc("secMatches"), "\n".join(body))


def table_html():
    head = ('<div class="ctab-head">'
            '<span class="h rk">%s</span><span class="h nmh"></span>'
            '<span class="h">%s</span>'
            '<span class="h wdl">%s</span><span class="h wdl">%s</span><span class="h wdl">%s</span>'
            '<span class="h">%s</span><span class="h">%s</span></div>'
            % (loc("colPos"), loc("colPlayed"), loc("colWins"), loc("colDraws"),
               loc("colLosses"), loc("colGoalDiff"), loc("colPoints")))

    rows = []
    for pos, (name, played, w, d, lost, gd, pts) in enumerate(TABLE, 1):
        rows.append(
            '<div class="ctab-row">'
            '<span class="rk num">%d</span>%s'
            '<span class="n num">%d</span>'
            '<span class="n num wdl">%d</span><span class="n num wdl">%d</span>'
            '<span class="n num wdl">%d</span>'
            '<span class="n num gd">%s</span><span class="n num pts">%d</span>'
            '</div>' % (pos, team_cell(name), played, w, d, lost,
                        ("+%d" % gd) if gd > 0 else str(gd), pts)
        )

    return """
      <section>
        <div class="sechead"><span class="eyebrow">%s</span></div>
        <div class="ctab">
%s
%s
        </div>
        <p class="bnote">&ldquo;Table&rdquo; is the display name; <code>mart_standings</code>
           is the data name. Provider standings points, not the synthetic 3-1-0 tally.
           No promotion/relegation shading: the registry does not carry the zone rules, and
           we do not invent them. No goals-for/against column exists to add &mdash; the mart
           carries <code>goals_diff</code> only.</p>
      </section>
""" % (loc("secTable"), head, "\n".join(rows))


MOCK_CSS = """
/* ---------------------------------------------------------------- *
 *  MOCK HARNESS ONLY -- not part of the design. Copied from          *
 *  gen_top_teams.py so the two mocks review identically.             *
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

.crest.xs svg { width: 15px; height: 15px; display: block; color: var(--muted); }
.bnote { font-size: 11px; color: var(--muted); margin: 10px 0 0; font-style: italic; opacity: .8; line-height: 1.5; }
.bnote code { font-style: normal; font-size: 10.5px; }

/* ================================================================ *
 *  COMPETITION HUB -- the actual proposal. TWO blocks:              *
 *  next matches, then the table.                                    *
 * ================================================================ */

/* ---- header. No competition crest: we hold no competition logo, and a placeholder
        would be an invented asset. `.chead` mirrors `.thead` on the team page minus the
        crest slot, so the two entity headers read as siblings. ---- */
.chead { padding: 16px 0 4px; }
.chead h1 { font-size: clamp(22px, 5cqw, 28px); font-weight: 700; line-height: 1.03; margin: 0; text-wrap: balance; }
.chead .meta { font-size: 13px; color: var(--muted); margin-top: 6px; }
.chead .meta b { color: var(--ink-2); font-weight: 600; }
.chead .meta .dot { opacity: .5; padding: 0 2px; }
/* No season selector in v1: this URL is the CURRENT season and there are no archive pages
   for a switcher to reach. Adding the control before its targets exist is the browse-chip
   404 again. */

/* ---- matches: NOTHING HERE. The row's markup and CSS both come from `rows.py`, shared with
        the Matches page (CPO 2026-08-10). A per-page copy is precisely what produced four
        different match treatments across the site. ---- */

/* ---- standings table. A NEW component: system.css has no table.
        `.rmatch` is a played-result row keyed to a W/D/L chip, `.vs-row` is a
        metric/bar/value row, `.brow` is a ranked leaderboard row with ONE value column --
        a league table is 5-8 aligned numeric columns and is none of them.

   ⚠ THE TRACK COUNT MUST EQUAL THE VISIBLE CELL COUNT AT BOTH WIDTHS, or every row after
   the overflow point silently wraps into an implicit row and the columns stop aligning.
   A row emits 8 cells (rank, team, P, W, D, L, GD, Pts) and the head emits 8 to match --
   `.nmh` is an empty header over the team column, which is the one column with no label.
   NARROW hides the three `.wdl` cells -> 5 visible against a 5-track list.
   WIDE shows all 8 against an 8-track list. The crest stays INSIDE the team link at both
   widths; giving it its own track was the first draft and it left an empty column at wide
   and no crest at all. check_competition_hub.py counts both. ---- */
.ctab { container-type: inline-size; margin-top: 4px; --gap: 8px;
        --cols: 1.25rem minmax(0, 1fr) 1.7rem 2.2rem 2rem; }
.ctab-head, .ctab-row {
  display: grid; grid-template-columns: var(--cols);
  align-items: center; column-gap: var(--gap);
}
.ctab-head { padding-bottom: 8px; border-bottom: 1px solid var(--div); }
.ctab-row { padding: 9px 0; border-bottom: 1px solid var(--line); }
.ctab-row:last-child { border-bottom: 0; }
.ctab .wdl { display: none; }
@container (min-width: 470px) {
  .ctab { --gap: 10px; --cols: 1.4rem minmax(0, 1fr) 1.9rem 1.7rem 1.7rem 1.7rem 2.4rem 2.2rem; }
  .ctab .wdl { display: block; }
}
.ctab .h { font-size: 11px; font-weight: 700; letter-spacing: .04em; color: var(--muted); text-align: right; }
.ctab .rk { font-size: 12px; font-weight: 700; color: var(--muted); text-align: right; font-variant-numeric: tabular-nums; }
.ctab .n { font-size: 13px; color: var(--muted); text-align: right; font-variant-numeric: tabular-nums; }
/* rung 1 -- the number that matters on a league table */
.ctab .n.pts { font-size: 15px; font-weight: 700; color: var(--ink); }
.ctab .n.gd { color: var(--ink-2); }

/* the team link: crest + name, name NEVER truncates (system.css ellipsises .nm) */
.ctab .tm { display: flex; align-items: center; gap: 9px; min-width: 0; }
.ctab .tm .nm {
  min-width: 0; font-size: 14px; font-weight: 600; color: var(--ink);
  white-space: normal; overflow: visible; text-overflow: clip; overflow-wrap: break-word;
  line-height: 1.25;
}
a.tm:hover .nm { text-decoration: underline; text-underline-offset: 2px; }
"""


def build():
    return """<!doctype html>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Competition hub -- /en/bundesliga/ (mock)</title>
<style>
%s
%s
%s
%s
</style>

<!-- The inputs are DIRECT children of body, ahead of everything they drive: `~` only
     reaches siblings, so an input nested inside its own <label> inside .ctl could never
     match .stage. Same structure system.css uses for .seg-in. -->
<input class="toggle" type="checkbox" id="t-light">
<input class="toggle" type="checkbox" id="t-phone">
<input class="toggle" type="checkbox" id="t-fi">

<div class="ctl">
  <label for="t-light"><span class="box"></span>Light</label>
  <label for="t-phone"><span class="box"></span>Phone 375px</label>
  <label for="t-fi"><span class="box"></span>Finnish (width probe)</label>
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
  <b>Mock &mdash; /en/bundesliga/, the competition hub.</b> Two blocks: next matches, then
  the table. Every number is placeholder; club names are real because their WIDTH is what is
  being tested.
  <b>The top-scorers board was cut</b> &mdash; leaderboards belong on
  /{competition-slug}/top-scorers/ and the Scorers tab, both already in the IA, so a board
  here was a teaser for a page that does not exist.
  With it gone the page renders no <b>metric_catalogue</b> metric at all: the table's column
  headers are page chrome, and the catalogue's one <b>points_won</b> row is the synthetic
  3-1-0 tally rather than the provider standings points shown here.
  Finnish is a width probe: <span class="probe" style="text-decoration: underline dotted">dotted</span>
  strings do not exist in strings.ts and are not approved copy. Only <b>Etusivu</b> is real.
  Round names render as &ldquo;Matchday 25&rdquo;; the mart stores the provider's
  <b>&ldquo;Regular Season - 25&rdquo;</b>, which has to be parsed before it can be localised.
</div>
""" % (SYSTEM_CSS.read_text(encoding="utf-8"), ROW_CSS, INTERACTION_CSS, MOCK_CSS,
       header_html(), matches_html(), table_html())


def check_data():
    """The table is placeholder, but it has to be a LEGAL table or the design is being
    judged against numbers that could not occur."""
    gd_total = 0
    prev_pts = None
    for name, played, w, d, lost, gd, pts in TABLE:
        assert w + d + lost == played, "%s: W+D+L != played" % name
        assert 3 * w + d == pts, "%s: points != 3W+D" % name
        if prev_pts is not None:
            assert pts <= prev_pts, "%s: table not ordered by points" % name
        prev_pts = pts
        gd_total += gd
    assert gd_total == 0, "goal differences sum to %d, not 0" % gd_total
    assert len({t[0] for t in TABLE}) == len(TABLE), "duplicate team in the table"
    print("  table invariants hold (%d teams, W+D+L, 3W+D, GD sums to 0)" % len(TABLE))


def check_fixture_teams_are_in_the_table():
    """Every club in either round must be one of the table's clubs -- a fixture against a
    club that is not in the league is placeholder data that could not occur."""
    known = {t[0] for t in TABLE}
    seen = {h for h, a, _d, _t in NEXT_ROUND[2]} | {a for _h, a, _d, _t in NEXT_ROUND[2]}
    stray = sorted(seen - known)
    assert not stray, "clubs in a fixture but not in the table: %s" % stray
    assert len(seen) == len(known), "%d clubs play, %d are in the table" % (len(seen), len(known))
    print("  fixtures use the table's %d clubs, all of them, none extra" % len(known))


if __name__ == "__main__":
    check_data()
    check_fixture_teams_are_in_the_table()
    OUT.write_text(build(), encoding="utf-8")
    print("  wrote %s (%.0f KB)" % (OUT.name, OUT.stat().st_size / 1024))
