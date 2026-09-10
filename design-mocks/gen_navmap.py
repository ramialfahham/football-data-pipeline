"""Render HOW THE SITE IS PUT TOGETHER -- in plain language, starting at the home page.

This replaces the route-pattern map (gen_sitemap.py), which was accurate and unreadable:
it showed `/{locale}/{competition-slug}/` where what is wanted is "a competition, e.g.
Bundesliga", and it left out the site MENU entirely, which is where navigation actually
starts.

Split of responsibility:
  * DERIVED from the repo -- whether a page exists (globbing site_v2/src/pages), the menu's
    items (SiteHeader.astro + the EN strings), and whether each menu item is a link or inert
    text. Those are facts and must not be typed.
  * HAND-WRITTEN -- the plain-English description of what each page shows and where it leads.
    There is no machine-readable source for "shows the next round and the league table", and
    pretending otherwise would be worse than saying so.

gen_sitemap.py stays: the URL-pattern view is the right one for SEO and routing work. This is
the one for deciding what the site IS.
"""
import html
import re
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
PAGES = REPO / "site_v2/src/pages"
HEADER = REPO / "site_v2/src/components/chrome/SiteHeader.astro"
STRINGS = REPO / "site_v2/src/i18n/strings.ts"
SYSTEM_CSS = REPO / "site_v2/src/styles/system.css"
OUT = Path(__file__).with_name("navmap.html")

E = html.escape

# ------------------------------------------------------------- derived bits


def page_exists(*route_parts):
    """Is there an .astro template for this route shape?"""
    want = "/".join(route_parts)
    for p in PAGES.rglob("*.astro"):
        if p.relative_to(PAGES).as_posix().replace(".astro", "") == want:
            return True
    return False


def menu_items():
    """The nav labels, in order, plus whether each renders as a LINK or inert text."""
    src = HEADER.read_text(encoding="utf-8")
    keys = re.findall(r't\(lang,\s*"(nav\w+)"\)', src)
    en = {}
    body = STRINGS.read_text(encoding="utf-8")
    for k in keys:
        m = re.search(r'\b%s:\s*"([^"]*)"' % k, body)
        en[k] = m.group(1) if m else k
    # the nav block: are the items <a> or <span>?
    nav = src.split('<nav class="mainnav"', 1)[1].split("</nav>", 1)[0]
    is_link = "<a" in nav
    return [(k, en[k]) for k in keys], is_link


MENU_NOTES = {
    "navCompetitions": ("A list of all twelve competitions.",
                        "planned",
                        "A list page is in the plan. But the home page already carries a row "
                        "of competition buttons, so it is worth asking whether a separate "
                        "page earns its place."),
    "navMatches": ("Matches across every competition.",
                   "designed",
                   "DESIGNED 2026-08-10 &mdash; two pages, <b>Next matches</b> and "
                   "<b>Past matches</b>. This was the one menu item with nothing behind it that "
                   "clearly earned a page, and it is now the first thing the menu can point at."),
    "navTeams": ("Every club.",
                 "none",
                 "NOTHING IS PLANNED. Club pages exist, but the only thing that lists clubs "
                 "is a competition's table."),
    "navPlayers": ("Every player.",
                   "none",
                   "NOTHING IS PLANNED, and the player page itself is not built."),
    "navStandings": ("Tables for every competition.",
                     "none",
                     "NOTHING IS PLANNED as its own page. Each competition carries its own "
                     "table, so this menu item may simply be the competitions list again."),
    "navStats": ("Stat leaderboards and definitions.",
                 "partial",
                 "Only a page PER METRIC is planned (a glossary entry). There is no index, "
                 "and league leaderboards live under each competition."),
}

# --------------------------------------------------------------- the pages
#
# (key, plain name, example, status, shows[], go[], inside[], note)
# `status` is OVERWRITTEN below from the repo where a template can be found -- the value here
# is only the fallback for pages that do not exist yet.

PAGES_PLAIN = [
    dict(
        key="home", route=("[lang]", "index"),
        name="The home page", example="matchdaypilot.com/en/",
        status="planned", depth=0,
        shows=["The next matches across all competitions",
               "A row of buttons, one per competition"],
        go=["A match"],
        soon=["A competition &mdash; the buttons are plain text today, because there is "
              "nowhere for them to lead yet"],
        inside=[],
        note="Two more blocks are designed and unbuilt: Top players and Top teams.",
    ),
    dict(
        key="matches", route=None,
        name="All matches", example="&hellip;/en/matches/",
        status="designed", depth=1,
        shows=["Every competition's next matchday, grouped by competition then date"],
        go=["A match", "A competition &mdash; every competition heading is a link"],
        soon=[], inside=[],
        note="The product's core list. Nothing after the next round: a match further out has "
             "nothing meaningful to send a reader to.",
    ),
    dict(
        key="matches-past", route=None,
        name="&hellip; and past matches", example="&hellip;/en/matches/results/",
        status="designed", depth=2,
        shows=["Every competition's last finished matchday, with scores"],
        go=["A match report", "A competition"],
        soon=[], inside=[],
        note="A separate page, not a tab &mdash; your rule that a tab gets its own address. The "
             "match report it links to does not exist yet.",
    ),
    dict(
        key="competition", route=None,
        name="A competition", example="&hellip;/en/bundesliga/",
        status="designed", depth=1,
        shows=["The next round's matches", "The league table, every club"],
        go=["A match", "A club &mdash; every row of the table is a link"],
        soon=[],
        inside=[],
        note="The missing middle of the site: today nothing sits between the home page and a "
             "club or a match, and both the club page and the match page already claim this as "
             "the page they are reached through.",
    ),
    dict(
        key="comp-matches", route=None,
        name="&hellip; that competition's own matches",
        example="&hellip;/en/bundesliga/matches/",
        status="open", depth=2,
        shows=["The same two views as All matches, but for this competition only"],
        go=["A match"], soon=[], inside=[],
        note="OPEN. The whole season's schedule and results, which the hub does not show &mdash; "
             "the hub carries only the next round. Same block, nothing new to design. Note the "
             "match page already lives at &hellip;/bundesliga/matches/&lt;match&gt;/, so this "
             "would make its parent path a real page instead of a 404.",
    ),
    dict(
        key="comp-scorers", route=None,
        name="&hellip; that competition's top scorers",
        example="&hellip;/en/bundesliga/top-scorers/",
        status="open", depth=2,
        shows=["Leaderboards for this competition"],
        go=["A player"], soon=[], inside=[],
        note="OPEN. Genuinely new content, and the warehouse already ranks per competition, so "
             "no new data work. It was cut from the hub because a board there was a teaser for "
             "this page.",
    ),
    dict(
        key="comp-table", route=None,
        name="&hellip; a separate table page", example="&hellip;/en/bundesliga/table/",
        status="dropped", depth=2,
        shows=[], go=[], soon=[], inside=[],
        note="In the old plan, and I would DROP it: the competition page already shows the full "
             "table, in the open, not behind anything. A separate page is the same content twice.",
    ),
    dict(
        key="match", route=("[lang]", "[competition]", "matches", "[fixture]"),
        name="A match", example="&hellip;/en/bundesliga/matches/2026-03-01-bayern-munchen-vs-vfb-stuttgart/",
        status="planned", depth=3,
        shows=["Both clubs' recent form, side by side",
               "Key players", "The head-to-head record"],
        go=["Either club"],
        soon=[],
        inside=["A switch between <b>last 5 matches</b> and <b>this season</b> &mdash; the "
                "SAME sixteen stats over a different span. This is the one case the new rule "
                "does not obviously settle; see below."],
        note="Only UPCOMING matches have a page. Once a match is played its page disappears, "
             "which is a known defect, not a design choice.",
    ),
    dict(
        key="team", route=("[lang]", "teams", "[team]"),
        name="A club", example="&hellip;/en/teams/bayern-munchen/",
        status="planned", depth=1,
        shows=["Where they stand and how the season is going",
               "Whether results match the underlying play",
               "This season against last season", "Next and recent matches"],
        go=["A match", "Its competition", "Its own Performance and Squad pages"],
        soon=["A player"],
        inside=[],
        note="This is the club's Overview. Under the new rule the tab bar stays as a bar, but "
              "each tab becomes a real link instead of a CSS toggle.",
    ),
    dict(
        key="team-perf", route=None,
        name="&hellip; that club's Performance", example="&hellip;/en/teams/bayern-munchen/performance/",
        status="split", depth=2,
        shows=["Sixteen stats ranked against the rest of the league",
               "The same sixteen against last season"],
        go=["Back to the club"], soon=[], inside=[],
        note="Built today, but living inside the club page with no address of its own. "
             "Splitting it out is the work your rule creates.",
    ),
    dict(
        key="team-squad", route=None,
        name="&hellip; that club's Squad", example="&hellip;/en/teams/bayern-munchen/squad/",
        status="split", depth=2,
        shows=["Every player by position, with appearances, minutes, goals, assists"],
        go=["Back to the club", "(later) a player"],
        soon=[], inside=[],
        note="Same &mdash; built, but unreachable and unlinkable today. This is the page "
             "someone searching &ldquo;Bayern squad&rdquo; would want to land on.",
    ),
    dict(
        key="player", route=("[lang]", "players", "[player]"),
        name="A player", example="&hellip;/en/players/harry-kane-1090/",
        status="planned", depth=1,
        shows=["Season form and highlights"],
        go=["Their club", "A match", "Their Matches, Stats and Career pages"],
        soon=[],
        inside=[],
        note="Overview designed and reviewed; the rest not started. Under the new rule this "
              "is FOUR pages per player per language, not one &mdash; see the warning below.",
    ),
    dict(
        key="h2h", route=None,
        name="Two clubs' history against each other", example="&hellip;/en/h2h/bayern-munchen-vs-borussia-dortmund/",
        status="planned", depth=1,
        shows=["Every past meeting between the two"],
        go=["Either club"], soon=[], inside=[],
        note="The data exists and is already shown ON the match page. A page of its own is "
             "deferred.",
    ),
    dict(
        key="glossary", route=None,
        name="What a stat means", example="&hellip;/en/stats/shots-on-target-per-match/",
        status="planned", depth=1,
        shows=["One page per stat: what it is and how it is calculated"],
        go=[], soon=[], inside=[],
        note="",
    ),
    dict(
        key="legal", route=None,
        name="Imprint and legal", example="&hellip;/en/imprint/",
        status="planned", depth=1,
        shows=["Operator details, privacy"],
        go=[], soon=[], inside=[],
        note="Required before the site can go public, and not started.",
    ),
    dict(
        key="country", route=None,
        name="Football by country", example="&hellip;/en/football/germany/",
        status="dropped", depth=1,
        shows=[], go=[], soon=[], inside=[],
        note="Dropped on 2026-08-10: twelve competitions do not need a second way to browse.",
    ),
]

STATUS = {
    "live": ("Live", "s-live"),
    "designed": ("Designed, not built", "s-designed"),
    "planned": ("Planned", "s-planned"),
    "open": ("Open question", "s-open"),
    "dropped": ("Dropped", "s-dropped"),
    "none": ("No page planned", "s-dropped"),
    "partial": ("Partly planned", "s-open"),
    "split": ("Built &mdash; needs its own address", "s-split"),
}


def pill(state):
    text, cls = STATUS[state]
    return '<span class="pill %s">%s</span>' % (cls, text)


def build():
    items, nav_is_link = menu_items()

    menu_rows = []
    for key, label in items:
        what, state, note = MENU_NOTES[key]
        menu_rows.append(
            "<tr><td class=\"mi\">%s</td><td>%s</td><td>%s<div class=\"mn\">%s</div></td></tr>"
            % (E(label), E(what), pill(state), note)
        )

    cards = []
    for p in PAGES_PLAIN:
        state = p["status"]
        if p["route"] and page_exists(*p["route"]):
            state = "live"
        bits = []
        if p["shows"]:
            bits.append('<div class="l"><span class="k">Shows</span><ul>%s</ul></div>'
                        % "".join("<li>%s</li>" % s for s in p["shows"]))
        if p["go"]:
            bits.append('<div class="l"><span class="k">You can go to</span><ul>%s</ul></div>'
                        % "".join("<li>%s</li>" % s for s in p["go"]))
        if p["soon"]:
            bits.append('<div class="l"><span class="k">Not yet, but should</span><ul>%s</ul></div>'
                        % "".join("<li>%s</li>" % s for s in p["soon"]))
        if p["inside"]:
            bits.append('<div class="l inside"><span class="k">Inside the page '
                        '&mdash; same web address</span><ul>%s</ul></div>'
                        % "".join("<li>%s</li>" % s for s in p["inside"]))
        if p["note"]:
            bits.append('<p class="note">%s</p>' % p["note"])
        cards.append(
            '<li class="card d%d %s"><div class="hd"><span class="nm">%s</span>%s</div>'
            '<div class="ex">%s</div>%s</li>'
            % (p["depth"], state, p["name"], pill(state), p["example"], "".join(bits))
        )

    return """<!doctype html>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>How the site is put together</title>
<style>
%s
%s
</style>
<div class="fx">
<div class="wrap">

  <h1>How the site is put together</h1>
  <p class="sub">In plain language, starting where a visitor starts. Whether a page exists is
     read from the code; the descriptions are written by hand.</p>

  <h2>1. The menu, at the top of every page</h2>
  <p class="sub">Six items. <b>Not one of them is a link</b> &mdash; they render as plain
     text, because none of the pages they would lead to exists. That is honest, but it means
     the site currently has <b>no navigation at all</b>: everything is reached by clicking
     something in the page body.</p>
  <table class="menu">
    <tr><th>Menu item</th><th>What it would show</th><th>Is there a page for it?</th></tr>
%s
  </table>
  <p class="sub warn">So four of the six menu items lead nowhere <b>and have nothing planned
     behind them</b>. That is the biggest structural gap, and it is bigger than any single
     page.</p>

  <h2>2. The pages, starting at the home page</h2>
  <p class="sub">Indented by how you reach them, not by web address.</p>
  <ul class="cards">
%s
  </ul>

  <h2>3. The rule, and what it changes</h2>
  <p class="sub rule"><b>Ruled 2026-08-10:</b> every section of a page gets its own web
     address.</p>
  <p class="sub">Read as: <b>anything currently hidden behind a tab or a switch becomes a real
     page.</b> Not every stacked block &mdash; the home page's two blocks and the competition
     page's two blocks are visible together on one screen and stay that way.</p>

  <h3>What has to change</h3>
  <ul class="does">
    <li><b>The club page splits into three.</b> Overview, Performance and Squad each get an
        address. The tab bar stays &mdash; each tab becomes a link instead of a CSS toggle.</li>
    <li><b>The player page is four pages, not one</b>, before it is ever built.</li>
    <li><b>Each new page needs its own title, description and summary</b>, or the set ships
        near-identical pages that compete with each other.</li>
    <li><b>The tab pages need somewhere to be linked from</b> &mdash; the entity's Overview
        becomes their hub.</li>
  </ul>

  <h3 class="warnh">The number to watch</h3>
  <p class="sub">Splitting multiplies the page count by the number of tabs. For clubs that is
     fine. For players it is not: the plan already counts <b>154,644 player pages</b> before
     any split &mdash; four tabs and three languages turns that into roughly
     <b>1.8 million</b>. Thin pages cost the whole domain, which is what the
     minimum-data gate exists to prevent, and that gate is not built yet.</p>
  <p class="sub">So the rule is right, and the player page is where it has to be applied with
     a floor: only split a player's tabs when there is enough behind them to be worth a page.</p>

  <h3 class="warnh">The one case the rule does not settle</h3>
  <p class="sub">A <b>tab</b> is different content &mdash; a squad list is not a stats table.
     Splitting those is clearly right.</p>
  <p class="sub">A <b>switch</b> is the same content seen differently: last 5 matches versus
     this season, on the match page, is the same sixteen stats over a different span. Giving
     those two addresses creates two nearly identical pages for one match, which compete with
     each other in search rather than adding anything.</p>
  <p class="sub"><b>Recommendation:</b> split tabs, keep switches as switches. If you want
     switches split too, say so and the match page becomes two pages and the club's
     Performance becomes two more.</p>

</div>
</div>
""" % (SYSTEM_CSS.read_text(encoding="utf-8"), PAGE_CSS,
       "\n".join(menu_rows), "\n".join(cards))


PAGE_CSS = """
body { margin: 0; background: #06070a; }
.wrap { max-width: 760px; margin: 0 auto; padding: 30px clamp(16px, 4vw, 28px) 70px; }
h1 { font-size: 27px; margin: 0 0 8px; line-height: 1.15; }
h2 { font-size: 17px; margin: 44px 0 12px; padding-bottom: 8px; border-bottom: 1px solid var(--div); }
.sub { font-size: 14px; color: var(--ink-2); line-height: 1.7; margin: 0 0 10px; }
.sub b { color: var(--ink); font-weight: 600; }
.sub.warn { border-left: 3px solid var(--loss); padding-left: 14px; margin-top: 16px; }

.pill { display: inline-block; font-size: 10.5px; font-weight: 700; letter-spacing: .05em;
        padding: 2px 8px; border-radius: 20px; border: 1px solid var(--div);
        color: var(--muted); white-space: nowrap; }
.s-live { border-color: var(--win); color: var(--win); }
.s-designed { border-color: var(--ink-2); color: var(--ink); }
.s-open { border-color: var(--draw); color: var(--ink-2); }
.s-dropped { border-color: var(--loss); color: var(--loss); }
.s-split { border-color: var(--accent); color: var(--accent); }

h3 { font-size: 14px; margin: 26px 0 8px; color: var(--ink); }
h3.warnh { color: var(--loss); }
.sub.rule { border-left: 3px solid var(--accent); padding: 8px 0 8px 14px; font-size: 15px; }
ul.does { margin: 8px 0 0; padding-left: 19px; }
ul.does li { font-size: 13.5px; color: var(--ink-2); line-height: 1.7; padding: 3px 0; }
ul.does li b { color: var(--ink); font-weight: 600; }
li.card.split { border-left: 3px solid var(--accent); }

table.menu { width: 100%; border-collapse: collapse; margin-top: 6px; }
table.menu th { text-align: left; font-size: 10.5px; letter-spacing: .07em; text-transform: uppercase;
                color: var(--muted); padding: 0 12px 8px 0; border-bottom: 1px solid var(--div); }
table.menu td { font-size: 13.5px; color: var(--ink-2); padding: 12px 12px 12px 0;
                border-bottom: 1px solid var(--line); vertical-align: top; line-height: 1.55; }
table.menu td.mi { color: var(--ink); font-weight: 700; white-space: nowrap; }
.mn { font-size: 12px; color: var(--muted); margin-top: 6px; line-height: 1.55; }

/* the pages, as nested cards -- indentation IS the hierarchy */
ul.cards { list-style: none; margin: 14px 0 0; padding: 0; }
li.card { position: relative; margin-top: 12px; padding: 15px 17px;
          background: var(--surface); border: 1px solid var(--line); border-radius: 10px; }
li.card.d1 { margin-left: clamp(14px, 4vw, 34px); }
li.card.d2 { margin-left: clamp(28px, 8vw, 68px); }
li.card.d3 { margin-left: clamp(42px, 12vw, 102px); }
li.card.d1::before, li.card.d2::before, li.card.d3::before {
  content: ""; position: absolute; left: -18px; top: -13px; bottom: 50%;
  width: 14px; border-left: 1px solid var(--div); border-bottom: 1px solid var(--div);
  border-bottom-left-radius: 5px;
}
li.card.live { border-left: 3px solid var(--win); }
li.card.designed { border-left: 3px solid var(--ink-2); }
li.card.dropped { border-left: 3px solid var(--loss); opacity: .7; }
li.card.open { border-style: dashed; }

.hd { display: flex; align-items: center; justify-content: space-between; gap: 12px; flex-wrap: wrap; }
.hd .nm { font-size: 17px; font-weight: 700; color: var(--ink); }
.ex { font-size: 11.5px; color: var(--muted); font-family: ui-monospace, monospace;
      margin-top: 4px; word-break: break-all; }

.l { margin-top: 13px; }
.l .k { display: block; font-size: 10.5px; font-weight: 700; letter-spacing: .07em;
        text-transform: uppercase; color: var(--muted); margin-bottom: 5px; }
.l ul { margin: 0; padding-left: 17px; }
.l li { font-size: 13.5px; color: var(--ink-2); line-height: 1.6; padding: 1px 0; }
.l li b { color: var(--ink); font-weight: 600; }
.l.inside { border-top: 1px dashed var(--div); padding-top: 12px; }
.l.inside .k { color: var(--loss); }
.note { font-size: 12.5px; color: var(--muted); font-style: italic; line-height: 1.6;
        margin: 13px 0 0; }
"""


if __name__ == "__main__":
    items, nav_is_link = menu_items()
    print("  menu items derived: %s" % ", ".join(lbl for _k, lbl in items))
    print("  menu renders as %s" % ("LINKS" if nav_is_link else "inert text"))
    assert len(items) == 6, "expected 6 nav items, found %d" % len(items)
    assert not nav_is_link, "the nav now emits anchors -- this page says it does not"
    for p in PAGES_PLAIN:
        if p["route"]:
            print("  %-12s template on disk: %s" % (p["key"], page_exists(*p["route"])))
    OUT.write_text(build(), encoding="utf-8")
    print("  wrote %s (%.0f KB)" % (OUT.name, OUT.stat().st_size / 1024))
