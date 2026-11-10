"""Render the two Matches pages, /{locale}/matches/ and /{locale}/matches/results/, as mock files.

Every kickoff and score is placeholder data; the match row comes from `rows.py`.
"""
import html
import sys
from pathlib import Path

from gen_block_standard import ACTIVE, ZONE, short, slug
from rows import date_head, group_head, result_row, upcoming_row

REPO = Path(__file__).resolve().parent.parent
SYSTEM_CSS = REPO / "site_v2/src/styles/system.css"
OUT_NEXT = Path(__file__).with_name("matches_next_mock.html")
OUT_PAST = Path(__file__).with_name("matches_past_mock.html")

# production URL -> local mock file, so the tab bar works when opened from disk
LOCAL = {"next": OUT_NEXT.name, "past": OUT_PAST.name}
PROD = {"next": "/en/matches/", "past": "/en/matches/results/"}

E = html.escape

# --------------------------------------------------------------- sample data

# Real club names, because their width is what is being tested; kickoffs are placeholders.
# Each competition is one group per round, with the date as a level inside it.
# (league_code, kind, [(date, [(home, away, kickoff)])])
NEXT_ROUNDS = [
    ("BL1", "club", [
        ("Sat 1 March", [("Borussia M\u00f6nchengladbach", "SC Freiburg", "15:30"),
                         ("Union Berlin", "Bayer 04 Leverkusen", "15:30"),
                         ("FC Augsburg", "Werder Bremen", "15:30"),
                         ("VfL Bochum", "RB Leipzig", "18:30")]),
        ("Sun 2 March", [("Eintracht Frankfurt", "TSG Hoffenheim", "15:30"),
                         ("1. FSV Mainz 05", "Borussia Dortmund", "17:30")]),
    ]),
    ("PL", "club", [
        ("Sat 1 March", [("Nottingham Forest", "Manchester City", "12:30"),
                         ("Brighton & Hove Albion", "Aston Villa", "15:00"),
                         ("Tottenham Hotspur", "Everton", "17:30")]),
    ]),
    ("PD", "club", [
        ("Sat 1 March", [("Real Sociedad", "Real Madrid", "16:15"),
                         ("Athletic Club", "Atl\u00e9tico Madrid", "21:00")]),
    ]),
    # MLS spans four US zones, so its rows render a dash: the registry's country cannot supply one.
    ("MLS", "club", [
        ("Sat 1 March", [("New York City FC", "Inter Miami", "19:30"),
                         ("LA Galaxy", "Seattle Sounders", "19:30")]),
    ]),
    ("VL", "club", [
        ("Mon 3 March", [("HJK Helsinki", "SJK", "18:30")]),
    ]),
]

# Each competition's last finished matchday; a played match carries no kick-off.
# (league_code, kind, [(date, [(home, hg, away, ag)])])
PAST_ROUNDS = [
    ("BL1", "club", [
        ("Sat 22 February", [("Bayern M\u00fcnchen", 4, "SC Freiburg", 1),
                             ("RB Leipzig", 1, "FC Augsburg", 0),
                             ("Werder Bremen", 2, "VfL Bochum", 2)]),
        ("Sun 23 February", [("Borussia Dortmund", 3, "Union Berlin", 1),
                             ("TSG Hoffenheim", 1, "FC St. Pauli", 1)]),
    ]),
    ("PL", "club", [
        ("Sat 22 February", [("Manchester City", 2, "Liverpool", 2),
                             ("Arsenal", 3, "Everton", 0)]),
    ]),
    ("L1", "club", [
        ("Sat 22 February", [("Paris Saint-Germain", 2, "Olympique Lyonnais", 0),
                             ("Olympique de Marseille", 1, "Stade Rennais", 1)]),
    ]),
    ("ED", "club", [
        ("Sun 23 February", [("PSV", 4, "Feyenoord", 2),
                             ("Ajax", 0, "AZ Alkmaar", 0)]),
    ]),
]

COPY = {
    "crumbHome": ("Home", "Etusivu", False),
    "h1":        ("Matches", "Ottelut", False),
    "tabNext":   ("Next matches", "Seuraavat ottelut", True),
    "tabPast":   ("Past matches", "Menneet ottelut", True),
}

# --------------------------------------------------------------------- build


def loc(key):
    en, fi, probe = COPY[key]
    cls = "fi probe" if probe else "fi"
    return ('<span class="en">%s</span><span class="%s" lang="fi">%s</span>'
            % (E(en), cls, E(fi)))


def rounds_html(rounds, played=False):
    """Group by competition, then date; all markup comes from `rows.py`."""
    groups = []
    for code, kind, dates in rounds:
        body = []
        for date, matches in dates:
            body.append(date_head(date))
            for m in matches:
                body.append(
                    result_row(kind, *m) if played
                    else upcoming_row(kind, m[0], m[1], m[2], ZONE[code] or "—"))
        groups.append('<div class="fxgroup">%s%s</div>'
                      % (group_head(slug(code), short(code)), "\n".join(body)))
    return "<section>%s</section>" % "\n".join(groups)


def tabbar(active):
    """Tab bar of links; the href is the sibling mock file so it is clickable from disk."""
    out = []
    for key, page in (("tabNext", "next"), ("tabPast", "past")):
        out.append('<a class="tab%s" href="%s" title="%s">%s</a>'
                   % (" on" if active == page else "", LOCAL[page], PROD[page], loc(key)))
    return '<nav class="tabs comp-tabs">%s</nav>' % "".join(out)


MOCK_CSS = """
/* ---------------- MOCK HARNESS ONLY -- copied from gen_top_teams.py ---------------- */
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
  --ink: #141410; --ink-2: #4c4c45; --muted: #77776e; --accent: #0a6e3a;
  --win: #157f43; --draw: #6f756d; --loss: #b23b3b; --pill-ink: #fff; --track: #e7e6e0;
}
.fi { display: none; }
#t-fi:checked ~ .stage .en { display: none; }
#t-fi:checked ~ .stage .fi { display: inline; }
#t-fi:checked ~ .stage .probe { text-decoration: underline dotted currentColor; text-underline-offset: 3px; }
.crest.xs svg { width: 15px; height: 15px; display: block; color: var(--muted); }
.blocknote { font-size: 11px; color: var(--muted); margin: 12px 0 0; font-style: italic; opacity: .8; line-height: 1.5; }
.pagelabel { max-width: 680px; margin: 34px auto 0; padding: 0 16px; color: #7c828c;
             font: 700 11px/1.6 ui-monospace, monospace; letter-spacing: .08em; text-transform: uppercase; }

/* ================================================================ *
 *  MATCHES -- page chrome. The ROW itself is in rows.py, shared     *
 *  with the competition hub, so the two cannot drift.               *
 * ================================================================ */

.mhead { padding: 16px 0 2px; }
.mhead h1 { font-size: clamp(22px, 5cqw, 28px); font-weight: 700; line-height: 1.03; margin: 0; }
/* no `.scope` rule: the line it styled is gone, and a rule kept for a deleted element is the
   trace that outlives the thing (it fired five times on one removal). `.lede` stays defined in
   system.css and is simply unused here — that one is not mine to delete. */


/* no day-heading rules: the day headings are GONE. The group is the round, on this page and on
   the competition hub alike, and the date rides on the row. A rule kept for a deleted element
   is the trace that outlives the thing. */

/* the filter block on the past page */
/* no filter rules: the control is gone, and a rule kept for a deleted element is the trace that
   outlives the thing. */
"""


def build(page):
    """One page per call; `page` is "next" or "past"."""
    head = """
      <nav class="crumb"><a class="lnk" href="/en/">%s</a>
        <span class="sep">&rsaquo;</span><span class="here">%s</span></nav>
      <header class="mhead"><h1>%s</h1></header>
      %s
""" % (loc("crumbHome"), COPY["h1"][0], COPY["h1"][0], tabbar(page))

    if page == "next":
        body = head + rounds_html(NEXT_ROUNDS)
        note = ("Each competition's NEXT matchday and nothing after it &mdash; a match beyond "
                "the next round has nothing meaningful to send a reader to.")
    else:
        body = head + rounds_html(PAST_ROUNDS, played=True)
        note = ("Each competition's LAST FINISHED matchday &mdash; the mirror of the next view. "
                "⚠ Rows link to the match report, which does not exist yet (#861); pages are "
                "built one at a time and the site is unpublished, so nothing is exposed "
                "meanwhile. Deeper history needs no redesign: a competition already holds a list "
                "of date groups, so a wider window is more entries in that list.")

    stage = ('<div class="stage"><div class="fx"><div class="inner">%s'
             '<p class="blocknote">%s</p></div></div></div>' % (body, note))

    return """<!doctype html>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Matches -- %s (mock)</title>
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
  <span class="hint">no JS &middot; toggles are :checked + sibling combinators</span>
</div>

<div class="pagelabel">%s &mdash; this is ONE page; the tabs above go to the other file</div>
%s

<div class="legend">
  <b>Mock of a single page.</b> Two tabs means two pages (#46), so this is one of two files and
  the tab bar links to the other &mdash; clicking it actually works from disk.
  <b>The match row is one shared component</b> (<code>rows.py</code>), used here, on the home page
  and on the competition page; <code>check_row_consistency.py</code> proves the rendered markup
  matches across all three.
  Grouping is <b>competition, then date</b>. <b>Kick-offs are venue-local</b> with the zone on
  every row &mdash; <b>MLS</b> shows a dash because it spans four US zones and the registry's
  country cannot supply one.
  The <b>World Cup qualifier</b> group on the next page proves national teams work: they get a
  flag, not a crest. Those competitions are not <code>status: active</code> today, so that group
  is a layout probe rather than a claim.
  Finnish is a width probe: <span class="probe" style="text-decoration: underline dotted">dotted</span>
  strings do not exist in strings.ts and are not approved copy.
</div>
""" % (PROD[page], SYSTEM_CSS.read_text(encoding="utf-8"), MOCK_CSS, PROD[page], stage)


def check_data():
    known = {c["league_code"] for c in ACTIVE}
    for label, rounds in (("next", NEXT_ROUNDS), ("past", PAST_ROUNDS)):
        codes = [r[0] for r in rounds]
        dupes = sorted({c for c in codes if codes.count(c) > 1})
        assert not dupes, "%s view lists a competition twice: %s" % (label, dupes)

        for code, _kind, dates in rounds:
            assert code in known, "%s: %r is not an active registry competition" % (label, code)
            seen, dseen = set(), set()
            for date, matches in dates:
                assert date, "%s/%s: a date group with no label" % (label, code)
                assert date not in dseen, "%s/%s: date %r appears twice" % (label, code, date)
                dseen.add(date)
                for m in matches:
                    home, away = (m[0], m[1]) if label == "next" else (m[0], m[2])
                    assert home != away, "%s: a side cannot play itself" % code
                    for side in (home, away):
                        assert side not in seen, "%s plays twice in %s" % (side, code)
                        seen.add(side)
    for code, _kind, dates in PAST_ROUNDS:
        for _date, matches in dates:
            for m in matches:
                assert len(m) == 4, "%s: a played row still carries a kick-off" % code
    blob = repr(NEXT_ROUNDS) + repr(PAST_ROUNDS)
    for bad in ("Fu\u00dfball-Bundesliga", "Major League Soccer", "Liga Profesional"):
        assert bad not in blob, "long-form league name still present: %r" % bad
    assert all(len(m) == 3 for _c, _k, ds in NEXT_ROUNDS for _d, ms in ds for m in ms), \
        "a next-view row is shaped like a played row"
    print("  %d next rounds \u00b7 %d past rounds \u00b7 one per competition \u00b7 every kickoff dated and "
          "zoned \u00b7 no day headings" % (len(NEXT_ROUNDS), len(PAST_ROUNDS)))


if __name__ == "__main__":
    check_data()
    out_dir = Path(sys.argv[2]) if sys.argv[1:2] == ["--out"] else None
    for page, out in (("next", OUT_NEXT), ("past", OUT_PAST)):
        if out_dir:
            out = out_dir / out.name
        out.write_text(build(page), encoding="utf-8")
        print("  wrote %s (%.0f KB)" % (out.name, out.stat().st_size / 1024))
    stale = Path(__file__).with_name("matches_mock.html")
    if not out_dir and stale.exists():
        stale.unlink()
        print("  removed %s (the stacked two-in-one file it replaces)" % stale.name)
