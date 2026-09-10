"""THE "NEXT MATCHES" CONTENT BLOCK — the standard.

Not a page mock. This defines the block once, so every surface that shows upcoming matches uses
it unchanged: the home page, the Matches page, a competition page, and later a club page.

WHY IT EXISTS: the same content was rendered four different ways. `home/HeroFixtures.astro` used
`.fxrow` grouped by competition; `team/TeamFixtures.astro` used a bespoke `.nextfx` card;
`fixture/RecentMatch.astro` and `team/TeamFixtureRow.astro` used `.rmatch`; and the two mocks
built this week added a fifth. Then within that, the Matches page grouped by DAY and the
competition page by MATCHDAY.

⚠ NOTHING IS HARD-CODED (CPO 2026-08-10). Every value on the block comes from the data model,
and the ANATOMY table below names the column for each one. The competition set here is read out
of `docs/competition_registry.yml` at render time; the only typed values are the short display
names, which have no readable source yet — `dim_league` needs the warehouse — and they are
GUARDED: a registry competition with no short name is a hard failure, so the two cannot drift.
"""
import html
import sys
from pathlib import Path

import yaml

from interaction import INTERACTION_CSS
from rows import ROW_CSS, date_head, group_head, upcoming_row

REPO = Path(__file__).resolve().parent.parent
REGISTRY = REPO / "docs/competition_registry.yml"
SYSTEM_CSS = REPO / "site_v2/src/styles/system.css"
OUT = Path(__file__).with_name("block_standard.html")

E = html.escape

# ------------------------------------------------------- the competition set
#
# READ, not typed. Whatever the registry marks active is what this block has to survive.

_REG = yaml.safe_load(REGISTRY.read_text(encoding="utf-8"))
ACTIVE = [c for c in _REG["competitions"] if c.get("status") == "active"]

# ⚠ STAND-IN ONLY, and guarded below. In production the display name comes from
# `dim_league.league_name` — one source of truth, per the CPO on 2026-08-10. Today the export
# takes it from TWO places (`export_site_data.py:821` uses dim_league for the fixture page,
# `:609` uses the registry for everything else), and the registry's is the long legal form
# ("1. Fußball-Bundesliga"), which the CPO rejected. There is no readable short name in the repo,
# so these are typed here and DELETED when the warehouse is reachable.
SHORT_NAME = {
    "BL1": "Bundesliga", "BL2": "2. Bundesliga", "PL": "Premier League", "PD": "La Liga",
    "SA": "Serie A", "L1": "Ligue 1", "LP": "Liga Portugal", "ED": "Eredivisie",
    "VL": "Veikkausliiga", "LMX": "Liga MX", "MLS": "MLS", "SPL": "Saudi Pro League",
}

# ⚠ ALSO A STAND-IN. `fct_fixture.kickoff_timezone` exists but every kickoff in the committed
# data is +00:00, so it is the provider's REQUEST zone, not the venue's. For a single-country
# league the registry's `country` gives it; MLS and Liga MX span several zones and need the
# venue. Until that is resolved the block cannot render an honest local time.
ZONE = {"BL1": "CET", "BL2": "CET", "PL": "GMT", "PD": "CET", "SA": "CET", "L1": "CET",
        "LP": "WET", "ED": "CET", "VL": "EET", "LMX": None, "MLS": None, "SPL": "AST"}

MULTI_ZONE = [c["league_code"] for c in ACTIVE if ZONE.get(c["league_code"]) is None]


def guard():
    """The typed maps must cover exactly what the registry marks active — no more, no less."""
    codes = {c["league_code"] for c in ACTIVE}
    for label, mapping in (("SHORT_NAME", SHORT_NAME), ("ZONE", ZONE)):
        missing = sorted(codes - set(mapping))
        extra = sorted(set(mapping) - codes)
        if missing:
            sys.exit("FATAL: %s has no entry for active competition(s): %s\n"
                     "The registry is the source of the SET; this map may not lag behind it."
                     % (label, ", ".join(missing)))
        if extra:
            sys.exit("FATAL: %s carries competition(s) the registry does not mark active: %s"
                     % (label, ", ".join(extra)))
    print("  registry drives the set: %d active competitions, both maps cover exactly them"
          % len(ACTIVE))


def short(code):
    return SHORT_NAME[code]


def slug(code):
    return next(c["slug"] for c in ACTIVE if c["league_code"] == code)


# --------------------------------------------------------------- sample data
#
# PLACEHOLDER fixtures. The competition NAMES, SLUGS and SET are read above; only kickoffs and
# club names are invented, and club names are real strings because their width is the test.

SAMPLE = {
    "BL1": [("Sat 1 March", [("Borussia Mönchengladbach", "SC Freiburg", "15:30"),
                             ("Union Berlin", "Bayer 04 Leverkusen", "15:30"),
                             ("FC Augsburg", "Werder Bremen", "15:30")]),
            ("Sun 2 March", [("Eintracht Frankfurt", "TSG Hoffenheim", "15:30"),
                             ("1. FSV Mainz 05", "Borussia Dortmund", "17:30")])],
    "PL":  [("Sat 1 March", [("Nottingham Forest", "Manchester City", "12:30"),
                             ("Brighton & Hove Albion", "Aston Villa", "15:00")])],
    "VL":  [("Mon 3 March", [("HJK Helsinki", "SJK", "18:30")])],
}

ANATOMY = [
    ("Competition logo", "level 1", "<code>dim_league.league_logo_url</code>",
     "Hot-linked from the provider today — #36, a go-live blocker with an open licence question."),
    ("Competition name", "level 1", "<code>dim_league.league_name</code>",
     "ONE source. Today the export reads it from dim_league for the fixture page and from the "
     "registry everywhere else, and they disagree."),
    ("Competition link", "level 1", "registry <code>slug</code>",
     "Plain text instead of a link on the competition's own page — a state, not a second block."),
    ("Date", "level 2", "<code>fct_fixture.kickoff_datetime</code>, venue-local",
     "A heading, not a cell. It was a per-row value and the schedule became unreadable."),
    ("Club crest / national flag", "row", "<code>dim_team.team_logo_url</code>",
     "A national side gets a flag, not a crest — a different asset, not the same one restyled."),
    ("Club or country name", "row", "<code>dim_team.team_name</code>",
     "NEVER truncates. system.css ellipsises this slot; the block overrides it."),
    ("Kick-off", "row", "<code>fct_fixture.kickoff_datetime</code>, venue-local", ""),
    ("Timezone", "row", "⚠ NOT AVAILABLE — see below",
     "On every row, always. Never on a heading: that was conditional, and a conditional block "
     "is two blocks."),
    ("Match link", "row", "registry <code>slug</code> + fixture slug", ""),
]

RULES = [
    "<b>Two levels of grouping, always, in this order: competition, then date.</b> Never day-"
    "then-competition on one surface and matchday on another.",
    "<b>No matchday.</b> It belongs on the match page, and the warehouse only holds the "
    "provider's raw <code>\"Regular Season - 25\"</code>, which shipped untranslated to all three "
    "locales once already (#866).",
    "<b>The competition heading is unmissable</b> — a 17px name, a 26px logo and a full-weight "
    "rule, because scrolling past a change of competition unnoticed is the failure this fixes.",
    "<b>One row component.</b> No page may restyle it; a machine check compares the rendered "
    "markup across surfaces.",
    "<b>The two sides stack</b>, each with its badge, and the kick-off sits in its own column.",
    "<b>Every row is a link to its match.</b> A row that cannot link is not shown here.",
    "<b>Nothing is hard-coded.</b> Every value above maps to a column.",
    "<b>A level may be OMITTED when the page already supplies it &mdash; never MOVED.</b> "
    "The competition page drops level 1, because the competition is its <code>h1</code>. What "
    "is never allowed is the same fact appearing in different slots on different surfaces: the "
    "timezone sat on a group heading for single-country leagues and on the row for the rest, "
    "and that put two shapes of one block on a single screen.",
]

CONTEXTS = [
    ("Home page", "many", "The next N across all competitions",
     "Competition heading links to its hub."),
    ("Matches page", "many", "Each competition's next matchday",
     "Same block, no cap."),
    ("Competition page", "one", "That competition's next matchday",
     "Level 1 is DROPPED — the competition is the page's h1. The block starts at the date."),
    ("Club page", "one", "That club's next match in this competition",
     "Not yet built. Open: whether one row still carries a competition heading."),
]


def block(codes, own_page=False):
    """`own_page=True` renders the variant used on a competition's OWN page: level 1 is dropped,
    because the competition is the page's <h1>. A block may OMIT a level the page supplies; it
    may never MOVE information between slots."""
    out = []
    for code in codes:
        gh = "" if own_page else group_head(slug(code), short(code))
        body = []
        for date, matches in SAMPLE[code]:
            body.append(date_head(date))
            for h, a, t in matches:
                body.append(upcoming_row("club", h, a, t, ZONE[code] or "—"))
        out.append('<div class="fxgroup">%s%s</div>' % (gh, "\n".join(body)))
    return "\n".join(out)


MOCK_CSS = """
body { margin: 0; background: #06070a; font: 400 15px/1.5 system-ui, -apple-system, "Segoe UI", Roboto, sans-serif; }
.ctl { position: sticky; top: 0; z-index: 9; display: flex; flex-wrap: wrap; gap: 18px;
       padding: 12px 16px; background: #14161c; border-bottom: 1px solid #2b2f38; color: #c7ccd4; font-size: 13px; }
.ctl label { display: inline-flex; align-items: center; gap: 7px; cursor: pointer; user-select: none; }
.toggle { position: absolute; width: 1px; height: 1px; opacity: 0; pointer-events: none; }
.ctl .box { width: 15px; height: 15px; border-radius: 4px; border: 1px solid #4a505b; background: #0d0f13; flex: 0 0 auto; }
#t-light:checked ~ .ctl label[for="t-light"] .box,
#t-phone:checked ~ .ctl label[for="t-phone"] .box { background: #3bb072; border-color: #3bb072; }
#t-light:checked ~ .wrap .fx {
  --page: #f3f3f0; --surface: #fbfbf9; --sunk: #edece7; --line: #e2e1da; --div: #cfcec5;
  --ink: #141410; --ink-2: #4c4c45; --muted: #77776e; --accent: #0a6e3a;
  --win: #157f43; --draw: #6f756d; --loss: #b23b3b; --pill-ink: #fff; --track: #e7e6e0;
}
#t-phone:checked ~ .wrap .fx .inner { max-width: 375px; box-shadow: 0 0 0 1px var(--line); }
.crest.xs svg { width: 15px; height: 15px; display: block; color: var(--muted); }

.wrap { max-width: 820px; margin: 0 auto; padding: 26px clamp(16px, 4vw, 28px) 70px; }
h1 { font-size: 25px; margin: 0 0 6px; }
h2 { font-size: 16px; margin: 40px 0 10px; padding-bottom: 8px; border-bottom: 1px solid var(--div); }
.sub { font-size: 13.5px; color: var(--ink-2); line-height: 1.7; margin: 0 0 10px; }
.sub b { color: var(--ink); font-weight: 600; }
code { font-family: ui-monospace, SFMono-Regular, Menlo, monospace; font-size: 12px; }
.spec { background: var(--surface); border: 1px solid var(--line); border-radius: 12px;
        padding: 6px 20px 22px; margin-top: 12px; }
.vlabel { font: 700 10.5px/1 ui-monospace, monospace; letter-spacing: .09em; text-transform: uppercase;
          color: var(--muted); padding: 18px 0 0; }
table { width: 100%; border-collapse: collapse; margin-top: 10px; }
th { text-align: left; font-size: 10.5px; letter-spacing: .07em; text-transform: uppercase;
     color: var(--muted); padding: 0 12px 8px 0; border-bottom: 1px solid var(--div); }
td { font-size: 13px; color: var(--ink-2); padding: 10px 12px 10px 0;
     border-bottom: 1px solid var(--line); vertical-align: top; line-height: 1.55; }
td.el { color: var(--ink); font-weight: 600; white-space: nowrap; }
td.lv { font-size: 10.5px; letter-spacing: .06em; text-transform: uppercase; color: var(--muted); white-space: nowrap; }
td .why { display: block; color: var(--muted); font-size: 12px; margin-top: 4px; }
ol.rules { margin: 10px 0 0; padding-left: 20px; }
ol.rules li { font-size: 13.5px; color: var(--ink-2); line-height: 1.7; padding: 4px 0; }
.warn { border-left: 3px solid var(--loss); padding: 10px 0 10px 14px; margin-top: 14px; }
"""


def build():
    return """<!doctype html>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Next matches — content block standard</title>
<style>
%s
%s
%s
%s
</style>
<input class="toggle" type="checkbox" id="t-light">
<input class="toggle" type="checkbox" id="t-phone">
<div class="ctl">
  <label for="t-light"><span class="box"></span>Light</label>
  <label for="t-phone"><span class="box"></span>Phone 375px</label>
</div>

<div class="wrap fx">

  <h1>&ldquo;Next matches&rdquo; &mdash; the content block</h1>
  <p class="sub">Defined once, used everywhere it appears. Two levels of grouping:
     <b>competition</b>, then <b>date</b>. The competition set below is read from the registry at
     render time.</p>

  <h2>The block</h2>
  <div class="spec">
    <div class="vlabel">Several competitions &mdash; home page, Matches page</div>
    <div class="inner">%s</div>
    <div class="vlabel">That competition's OWN page &mdash; level 1 dropped, it is the
       <code>&lt;h1&gt;</code></div>
    <div class="inner">%s</div>
  </div>

  <h2>Anatomy &mdash; every value comes from a column</h2>
  <table>
    <tr><th>Element</th><th>Level</th><th>Source</th></tr>
%s
  </table>

  <h2>Rules that never vary</h2>
  <ol class="rules">%s</ol>

  <h2>What adapts to the surface</h2>
  <table>
    <tr><th>Surface</th><th>Competitions</th><th>Which matches</th><th>Difference</th></tr>
%s
  </table>

  <h2>⚠ One value the block cannot render honestly yet</h2>
  <p class="sub warn"><b>The venue-local timezone.</b>
     <code>fct_fixture.kickoff_timezone</code> exists, but every kickoff in the committed data is
     <code>+00:00</code> &mdash; it is the provider's <b>request</b> zone, not the venue's. For a
     single-country league the registry's <code>country</code> gives it. <b>%s</b> span several
     zones and need the venue's own. Until that lands the zone slot renders a dash, which is why
     it shows one above.</p>

</div>
""" % (SYSTEM_CSS.read_text(encoding="utf-8"), ROW_CSS, INTERACTION_CSS, MOCK_CSS,
       block(["BL1", "PL", "VL"]), block(["BL1"], own_page=True),
       "\n".join('<tr><td class="el">%s</td><td class="lv">%s</td><td>%s%s</td></tr>'
                 % (E(el), E(lv), src, ('<span class="why">%s</span>' % why) if why else "")
                 for el, lv, src, why in ANATOMY),
       "".join("<li>%s</li>" % r for r in RULES),
       "\n".join('<tr><td class="el">%s</td><td class="lv">%s</td><td>%s</td><td>%s</td></tr>'
                 % (E(s), E(n), E(w), E(d)) for s, n, w, d in CONTEXTS),
       ", ".join(short(c) for c in MULTI_ZONE))


if __name__ == "__main__":
    guard()
    OUT.write_text(build(), encoding="utf-8")
    print("  wrote %s (%.0f KB)" % (OUT.name, OUT.stat().st_size / 1024))
