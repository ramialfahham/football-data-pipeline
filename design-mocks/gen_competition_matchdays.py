"""Render the COMPETITION PAGE, Matchdays tab, as a standalone mock for the review on GitLab #129.

Real data: every Bundesliga 2026/27 fixture as prod `core.fct_fixture` held it when pulled
(306 rows, 3 matchdays played, matchday 4 next -- the same nine rows the Overview's Next matches
block shows). Kick-off shown in the venue's clock (Europe/Berlin) with the zone the clock gives.

Imports the shared pieces from design-mocks (rows, interaction, the Overview generator's header
copy) so the tab cannot drift from the rows the site already has.
"""
import json
import sys
from collections import OrderedDict
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
sys.path.insert(0, str(HERE))

from gen_competition_hub import COPY, E, MOCK_CSS, SYSTEM_CSS, loc, slugify  # noqa: E402
from rows import CREST, date_head, result_row, upcoming_row  # noqa: E402

COPY.update({
    "tabMatchdaysHere": ("Matchdays", "Kierrokset", False),
    "nextTag":          ("Next", "Seuraava", False),
    "jumpLabel":        ("Schedule", "Otteluohjelma", True),
    "mdWord":           ("Matchday", "Kierros", False),
    "secLucky":         ("Lucky and unlucky", "Onnekkaat ja epäonnekkaat", True),
    "luckyExplainer":   ("Results that went against the shot balance. Shot balance is shots on goal created minus shots on goal conceded.",
                         "Tulokset, jotka menivät laukaustasetta vastaan. Laukaustase on luodut laukaukset maalia kohti miinus päästetyt.", True),
    "luckyWon":         ("Won without the shots", "Voitti ilman laukauksia", True),
    "luckyLost":        ("Lost despite the shots", "Hävisi laukauksista huolimatta", True),
    "luckyDrew":        ("Drew despite the shots", "Tasapeli laukauksista huolimatta", True),
    "shotsOnGoal":      ("shots on goal", "laukaukset maalia kohti", True),
    "secMatters":       ("The match that matters", "Avainottelu", True),
    "mattersWhy":       ("The two best-placed teams meeting this matchday", "Kierroksen kaksi parhaiten sijoittunutta joukkuetta vastakkain", True),
})

# the round's shots on goal per side, from core, matchday 3 only (the README dates the pull)
SHOTS_FILE = "bl1_md3_shots.json"
# the Overview's flag and the table, from the committed Bundesliga payload
PAYLOAD = REPO / "site_v2/src/data/competitions/BL1/2026.json"


def load_shots():
    raw = (HERE / SHOTS_FILE).read_bytes()
    rows = json.loads(raw.decode("utf-8"))
    return {int(r["fixture_sk"]): (int(r["home_sog"]), int(r["away_sog"])) for r in rows}


def load_payload():
    return json.loads(PAYLOAD.read_text(encoding="utf-8"))


def ordinal(n):
    return "%d%s" % (n, "th" if 11 <= n % 100 <= 13 else {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th"))

VENUE_TZ = ZoneInfo("Europe/Berlin")
COPY["topMatch"] = ("Top match", "Huippuottelu", True)
# the flagged match of the next matchday (is_match_that_matters on the committed payload)
TOP_MATCH = {r["fixture_id"] for r in json.loads(
    (REPO / "site_v2/src/data/competitions/BL1/2026.json").read_text(encoding="utf-8"))["next_matchday"]
    if r["is_match_that_matters"]}


def load_fixtures():
    raw = (HERE / "bl1_fixtures.json").read_bytes()
    try:
        rows = json.loads(raw.decode("utf-8"))
    except UnicodeDecodeError:
        rows = json.loads(raw.decode("cp1252"))
    out = []
    for r in rows:
        utc = datetime.strptime(r["kickoff_utc"], "%Y-%m-%d %H:%M:%S+00").replace(tzinfo=ZoneInfo("UTC"))
        local = utc.astimezone(VENUE_TZ)
        out.append(dict(
            fixture_id=int(r["fixture_sk"]),
            round_no=int(r["round_name"].rsplit("-", 1)[1]),
            local=local,
            day=local.strftime("%a %d %b"),
            time=local.strftime("%H:%M"),
            zone=local.strftime("%Z"),
            status=r["status_short"],
            hg=None if r["goals_home"] is None else int(r["goals_home"]),
            ag=None if r["goals_away"] is None else int(r["goals_away"]),
            home=r["home_name"], away=r["away_name"],
        ))
    out.sort(key=lambda f: (f["round_no"], f["local"], f["fixture_id"]))
    return out


def by_round(fixtures):
    rounds = OrderedDict()
    for f in fixtures:
        rounds.setdefault(f["round_no"], []).append(f)
    return rounds


def next_round(rounds):
    """The next matchday = the lowest round with an unplayed fixture -- the rule mart_next_matchday
    already applies; the mock reads status, the warehouse would serve a flag."""
    for n, fx in rounds.items():
        if any(f["status"] in ("NS", "TBD") for f in fx):
            return n
    return None


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
        <span class="tab on" aria-current="page">%s</span>
        <span class="tab" aria-disabled="true">%s</span>
      </nav>
""" % (loc("crumbHome"), loc("navCompetitions"), E(name), loc("tabMatchdaysHere"), CREST, E(name),
       "Germany", "Season 2026/27", "Matchday 4",
       loc("tabOverview"), loc("tabMatchdays"), loc("tabTeams"))


def step_html(rounds, n, nxt):
    """One matchday's radio and picker step (CSS-only, the radio mechanism the team page's tabs
    use). Each sits in its matchday's `.md` wrapper with the schedule, so the stylesheet shows the
    checked wrapper's contents with no per-matchday rule; the next matchday is checked on load."""
    ns = list(rounds)
    i = ns.index(n)
    prev_ = ('<label class="step prev" for="md-%d" aria-label="Matchday %d">%s</label>'
             % (ns[i - 1], ns[i - 1], CHEV_L) if i > 0 else '<span class="step prev off">%s</span>' % CHEV_L)
    next_ = ('<label class="step next" for="md-%d" aria-label="Matchday %d">%s</label>'
             % (ns[i + 1], ns[i + 1], CHEV_R) if i + 1 < len(ns) else '<span class="step next off">%s</span>' % CHEV_R)
    tag = ' <span class="nexttag">%s</span>' % loc("nextTag") if n == nxt else ""
    title = ('<span class="mdtitle"><b class="num"><span class="en">Matchday %d</span>'
             '<span class="fi" lang="fi">%d. kierros</span></b>%s</span>' % (n, n, tag))
    return ('<input class="md-in" type="radio" name="md" id="md-%d"%s>\n'
            '      <nav class="mdnav" aria-label="Pick a matchday"><span class="mdstep">%s%s%s</span></nav>'
            % (n, " checked" if n == nxt else "", prev_, title, next_))


CHEV_L = ('<svg viewBox="0 0 24 24" aria-hidden="true" focusable="false">'
          '<path d="M15 5l-7 7 7 7" fill="none" stroke="currentColor" stroke-width="2.2" '
          'stroke-linecap="round" stroke-linejoin="round"/></svg>')
CHEV_R = ('<svg viewBox="0 0 24 24" aria-hidden="true" focusable="false">'
          '<path d="M9 5l7 7-7 7" fill="none" stroke="currentColor" stroke-width="2.2" '
          'stroke-linecap="round" stroke-linejoin="round"/></svg>')


def fact_row(label_key, value, context, href="#"):
    return ('<a class="frow" href="%s"><span class="fl">%s</span><span class="fv">'
            '<span class="fvv"><b>%s</b></span><span class="sub">%s</span></span></a>'
            % (href, loc(label_key), E(value), context))


def lucky_html(fx, shots):
    """Block 5 on a played matchday: results that went against the shot balance (shots on goal,
    the site's own definition). Winner with a balance of zero or worse; a draw with a balance of
    three or more either way. Absent when the round has none."""
    rows = []
    for f in fx:
        if f["hg"] is None or f["fixture_id"] not in shots:
            continue
        hs, as_ = shots[f["fixture_id"]]
        bal = hs - as_
        score = "%s %d–%d %s" % (f["home"], f["hg"], f["ag"], f["away"])
        ctx = "%s %d:%d" % (loc("shotsOnGoal"), hs, as_)
        if f["hg"] > f["ag"] and bal <= 0 or f["ag"] > f["hg"] and bal >= 0:
            rows.append(fact_row("luckyWon", score, ctx))
        elif f["hg"] == f["ag"] and abs(bal) >= 3:
            rows.append(fact_row("luckyDrew", score, ctx))
    if not rows:
        return ""
    return """
        <section class="sub-block">
          <div class="sechead"><span class="eyebrow">%s</span></div>
          <p class="bsub">%s</p>
          <div class="facts">
%s
          </div>
        </section>
""" % (loc("secLucky"), loc("luckyExplainer"), "\n".join(rows))


def matters_html(fx, payload):
    """Block 1 on the next matchday: the Overview's flag, shown as the shared row with the two
    table positions under it. Absent on every other matchday."""
    flagged = {r["fixture_id"] for r in payload["next_matchday"] if r["is_match_that_matters"]}
    rank = {s["team_name"]: s["standing_rank"] for s in payload["standings"]}
    rows = []
    for f in fx:
        if f["fixture_id"] not in flagged:
            continue
        rows.append(date_head(f["day"]))
        rows.append(upcoming_row("club", f["home"], f["away"], f["time"], f["zone"]))
        rows.append('<p class="bsub">%s: %s %s, %s %s.</p>' % (
            loc("mattersWhy"), ordinal(rank[f["home"]]), E(f["home"]),
            ordinal(rank[f["away"]]), E(f["away"])))
    if not rows:
        return ""
    return """
        <section class="sub-block">
          <div class="sechead"><span class="eyebrow">%s</span></div>
          <div class="fxgroup">
%s
          </div>
        </section>
""" % (loc("secMatters"), "\n".join(rows))


def matchday_html(n, fx, is_next, shots=None, payload=None):
    body = []
    for day in dict.fromkeys(f["day"] for f in fx):
        body.append(date_head(day))
        for f in fx:
            if f["day"] != day:
                continue
            href = "/en/bundesliga/matches/%s-%s-vs-%s/" % (
                f["local"].strftime("%Y-%m-%d"), slugify(f["home"]), slugify(f["away"]))
            if f["hg"] is not None:
                body.append(result_row("club", f["home"], f["hg"], f["away"], f["ag"], href))
            else:
                row = upcoming_row("club", f["home"], f["away"], f["time"], f["zone"], href)
                if f["fixture_id"] in TOP_MATCH:
                    row = row.replace('<span class="when">',
                                      '<span class="topmatch">%s</span><span class="when">' % loc("topMatch"), 1)
                body.append(row)
    extra = ""
    if shots and not is_next:
        extra = lucky_html(fx, shots)
    if payload and is_next:
        extra = matters_html(fx, payload)
    return """
      <section%s>
        <div class="sechead"><span class="eyebrow">%s</span></div>
        <div class="fxgroup">
%s
        </div>
%s
      </section>
""" % (' class="next"' if is_next else "", loc("jumpLabel"), "\n".join(body), extra)


def build():
    rounds = by_round(load_fixtures())
    nxt = next_round(rounds)
    matchdays = "\n".join('<div class="md" data-md="%d">%s%s</div>'
                          % (n, step_html(rounds, n, nxt), matchday_html(n, fx, n == nxt))
                          for n, fx in rounds.items())
    played = sum(1 for fx in rounds.values() for f in fx if f["hg"] is not None)
    return """<!doctype html>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Competition page, Matchdays -- Bundesliga (mock)</title>
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
  <label for="t-fi"><span class="box"></span>Finnish</label>
  <span class="hint">no JS &middot; toggles are :checked + sibling combinators</span>
</div>

<div class="stage">
  <div class="fx">
    <div class="inner">
%s
%s
    </div>
  </div>
</div>

<div class="legend">
  <b>Mock &mdash; the competition page, Matchdays tab (proposal for #129).</b>
  One matchday at a time; the picker opens on the next one. Real data: every Bundesliga 2026/27
  fixture as prod held it on 2026-09-16 &mdash; %d matches, %d played, matchday %d next (the
  Overview's Next matches rows). Kick-off in the venue's clock.
</div>
""" % (SYSTEM_CSS.read_text(encoding="utf-8"), MOCK_CSS, header_html("Bundesliga"), matchdays,
       sum(len(fx) for fx in rounds.values()), played, nxt)


if __name__ == "__main__":
    out = HERE / (sys.argv[1] if len(sys.argv) > 1 else "competition_matchdays_mock_v1.html")
    out.write_text(build(), encoding="utf-8")
    print("wrote", out, "%.0f KB" % (out.stat().st_size / 1024))
