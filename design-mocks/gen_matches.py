"""Render the MATCHES pages -- /{locale}/matches/ and /{locale}/matches/results/ -- as one mock.

Design-only. Reads nothing from BigQuery; every kickoff and score is PLACEHOLDER.

WHY: the site header carries six nav items and none is a link, because none of their pages
exists. "Matches" is the one that most clearly earns a page -- it is the product's name, and it
is the natural hub for fixture pages, reachable today only from the home page's short teaser.
⚠ `/{locale}/matches/` is not in `site_architecture.md` §3 at all (#49).

Design directions for this page, all applied:
  1. short league names ("Bundesliga"), from a single source of truth;
  2. league LOGOS beside each group;
  3. grouped by competition -- club AND national-team competitions;
  4. TWO views: next matches, past matches;
  5. past matches filterable by season / competition;
  6. finished matches get stats -- this is the path on which to establish them;
  7. **the match row is ONE component on every page** -- so it lives in `rows.py` and this file
     imports it. Consistency by construction, not by rule;
  8. **kickoffs in VENUE-LOCAL time.**

⚠ (4) IS TWO PAGES, NOT TWO TABS (#46): a tab is different content, so it gets its own URL.
The bar still LOOKS like tabs; each is an `<a>` and the active
one carries `.is-on` instead of a `:checked` radio. That class is exactly the edit #46 creates.

`site_v2/src/styles/system.css` is inlined verbatim so the mock uses the shipped design system.
No JavaScript: the review surface is a static snapshot, so script never runs.
"""
import html
from pathlib import Path

from gen_block_standard import ACTIVE, ZONE, short, slug
from interaction import INTERACTION_CSS
from rows import ROW_CSS, date_head, group_head, result_row, upcoming_row

REPO = Path(__file__).resolve().parent.parent
SYSTEM_CSS = REPO / "site_v2/src/styles/system.css"
# ⚠ TWO FILES, ONE PER PAGE. A single file used to stack both views with "Page 1" / "Page 2"
# labels, and the tab bar pointed at the production URLs -- so it read as one page showing both
# lists, and clicking a tab did nothing. These are two separate pages (#46), so the mock is two
# separate files and the tabs link to each other, which makes them actually clickable.
OUT_NEXT = Path(__file__).with_name("matches_next_mock.html")
OUT_PAST = Path(__file__).with_name("matches_past_mock.html")

# production URL -> local mock file, so the tab bar works when opened from disk
LOCAL = {"next": OUT_NEXT.name, "past": OUT_PAST.name}
PROD = {"next": "/en/matches/", "past": "/en/matches/results/"}

E = html.escape

# --------------------------------------------------------------- sample data
#
# PLACEHOLDER kickoffs and scores; real club, country and competition names, because their
# WIDTH is what is being tested. Names are the SHORT form throughout (direction 1).
#
# Group tuple: (slug, name, kind, matchday, [(home, away, time, zone)])
#
# ⚠ THE WINDOW IS NOT A DATE RANGE. The rule: *"every next match (in terms of next match
# day) from the competitions we have in the data, but not the matches after that"* — the reason
# being that a match beyond the next round has nothing meaningful to send a reader to.
#
# So the rule is PER COMPETITION, not per calendar: each competition contributes exactly ONE
# matchday and nothing after it. A matchday legitimately spans days (Bundesliga 25 runs Sat and
# Sun), so a competition may appear under two day headings — but never under two matchdays.
# `check_data` enforces that. It also means the day list is RAGGED by design: Veikkausliiga's
# next round can be four days after everyone else's, and the days between it simply have no
# entry.
#
# ⚠ EVERY ROW CARRIES ITS OWN ZONE. An earlier version put it on the group head and moved it to
# the row only where a competition spans zones -- so a group-level "CET" sat above one block and
# per-row "CET"/"EET" in the next, on one screen. Rejected on sight: a reusable block must not
# change shape according to its context. Repeating "CET" down a Bundesliga list is the price.
#
# ⚠ The World Cup qualifier group is a LAYOUT PROBE for two things at once: national teams
# (flags, not crests) and a competition that SPANS TIME ZONES. WC/WCQ* are not `status: active`
# in the registry today -- twelve active competitions, all domestic leagues.

# \u26a0 FLAT. There are no day sections any more. One group per competition per round, ordered by
# the round's first kickoff -- so a competition whose matchday runs Saturday AND Sunday is ONE
# group, not two, and the date sits on each row.
#
# (slug, name, kind, matchday label, [(home, away, date, time, zone)])

# (league_code, kind, [(date, [(home, away, kickoff)])])
NEXT_ROUNDS = [
    ("BL1", "club", [
        ("Sat 1 March", [("Borussia M\u00f6nchengladbach", "SC Freiburg", "15:30"),
                         ("Union Berlin", "Bayer 04 Leverkusen", "15:30"),
                         ("FC Augsburg", "Werder Bremen", "15:30"),
                         ("VfL Bochum", "RB Leipzig", "18:30")]),
        # \u26a0 the SAME round, two days later. A round spans a weekend, which is why the DATE is the
        # second level INSIDE the competition rather than a heading above it.
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
    # \u26a0 MLS spans four US zones, so its rows render a dash: the venue-local zone is not derivable
    # from the registry's country the way it is for a single-country league.
    ("MLS", "club", [
        ("Sat 1 March", [("New York City FC", "Inter Miami", "19:30"),
                         ("LA Galaxy", "Seattle Sounders", "19:30")]),
    ]),
    ("VL", "club", [
        ("Mon 3 March", [("HJK Helsinki", "SJK", "18:30")]),
    ]),
]

# PAST: each competition's LAST FINISHED MATCHDAY -- the exact mirror of the next view
# (superseding an earlier "whole current season" rule).
#
# \u26a0 BUILT TO TAKE MORE HISTORY LATER. Nothing about the shape assumes one round: a competition
# already holds a LIST of date groups, so a deeper window is more entries in that list and no
# redesign. Only the query changes. That is why the last round is expressed as a list of one
# rather than a special case.
#
# \u26a0 NO KICK-OFF on a played match \u2014 once it is finished, the time it started is
# not information. The date stays, as the group heading it always was.
#
# (league_code, kind, [(date, [(home, hg, away, ag)])])
PAST_ROUNDS = [
    ("BL1", "club", [
        ("Sat 22 February", [("Bayern M\u00fcnchen", 4, "SC Freiburg", 1),
                             ("RB Leipzig", 1, "FC Augsburg", 0),
                             ("Werder Bremen", 2, "VfL Bochum", 2)]),
        # the same round, the next day -- the reason DATE is a level inside the competition
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

# ⚠ READ from the registry, in its sort order -- not a typed list. Adding a competition to the
# registry adds a chip here with no edit, which is the zero-file rule applied to the frontend.
# ⚠ the competition-chip list that lived here is GONE with the filter it fed. Kept as a note, not
# as commented-out code: dead data is what a later reader restores by accident.

COPY = {
    "crumbHome": ("Home", "Etusivu", False),
    "h1":        ("Matches", "Ottelut", False),
    "tabNext":   ("Next matches", "Seuraavat ottelut", True),
    "tabPast":   ("Past matches", "Menneet ottelut", True),
    # \u26a0 TWO LINES WERE CUT HERE.
    #  1. a scope line ("Kick-off times are local to the venue \u2014 scores are not live"). Every
    #     row already carries its own zone, so the first half restated it and the second was a
    #     disclaimer nobody asked for.
    #  2. the data-to-text lede ("16 matches across 6 competitions over the next three days").
    #     site_architecture.md \u00a76 requires a generated sentence per page as ANTI-THIN-CONTENT \u2014
    #     but this page is a full match list and is not thin, and the sentence only counted the
    #     rows underneath it. \u00a76 is satisfied where it earns its place; the competition hub's
    #     lede ("Bayern lead after 24 matches, 7 points clear") does, because you would have to
    #     read the table to know it. Filling the slot because the slot exists is the failure.
}

# --------------------------------------------------------------------- build


def loc(key):
    en, fi, probe = COPY[key]
    cls = "fi probe" if probe else "fi"
    return ('<span class="en">%s</span><span class="%s" lang="fi">%s</span>'
            % (E(en), cls, E(fi)))


def rounds_html(rounds, played=False):
    """THE SHARED BLOCK — competition, then date. No markup is written here."""
    groups = []
    for code, kind, dates in rounds:
        body = []
        for date, matches in dates:
            body.append(date_head(date))
            for m in matches:
                # the SAME row either way; a played one carries the score inline per side
                body.append(
                    result_row(kind, *m) if played
                    else upcoming_row(kind, m[0], m[1], m[2], ZONE[code] or "—"))
        groups.append('<div class="fxgroup">%s%s</div>'
                      % (group_head(slug(code), short(code)), "\n".join(body)))
    return "<section>%s</section>" % "\n".join(groups)


def tabbar(active):
    """⚠ LINKS, not radios (#46). The active one carries `.is-on`; system.css's `.tab` active
    treatment is bound to `#tab-*:checked`, which no longer exists once tabs are pages.

    In the mock the href is the SIBLING FILE, so the tabs are clickable from disk. In production
    they are `PROD[...]`."""
    out = []
    for key, page in (("tabNext", "next"), ("tabPast", "past")):
        out.append('<a class="tab%s" href="%s" title="%s">%s</a>'
                   % (" is-on" if active == page else "", LOCAL[page], PROD[page], loc(key)))
    return '<nav class="tabs">%s</nav>' % "".join(out)


# ⚠ NO FILTER IS DRAWN. It was a season chip plus a row of competition chips, and it is gone:
#   * the SEASON half is ruled out -- one season only, "to reduce complexity";
#   * the COMPETITION half is UNDECIDED -- "don't know yet" -- and its chips linked AWAY to each
#     competition's own results page rather than filtering this one, so it was not a filter at
#     all. The competition heading already does that job.
# Drawing a control before the decision is the fill-the-empty-slot failure this standard exists
# to prevent.


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
.bnote { font-size: 11px; color: var(--muted); margin: 12px 0 0; font-style: italic; opacity: .8; line-height: 1.5; }
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

/* the tab bar as LINKS (#46): system.css binds `.tab`'s active look to `#tab-*:checked`, which
   no longer exists once tabs are pages, so the active state needs a class. */
.tabs { margin-top: 16px; }
.tab.is-on { color: var(--ink); font-weight: 700; border-bottom-color: var(--ink); }

/* no day-heading rules: the day headings are GONE. The group is the round, on this page and on
   the competition hub alike, and the date rides on the row. A rule kept for a deleted element
   is the trace that outlives the thing. */

/* the filter block on the past page */
/* no filter rules: the control is gone, and a rule kept for a deleted element is the trace that
   outlives the thing. */
"""


def build(page):
    """ONE page per call -- `page` is "next" or "past". Each becomes its own file, because each
    is its own URL (#46)."""
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
             '<p class="bnote">%s</p></div></div></div>' % (body, note))

    return """<!doctype html>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Matches -- %s (mock)</title>
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
""" % (PROD[page], SYSTEM_CSS.read_text(encoding="utf-8"), ROW_CSS, INTERACTION_CSS, MOCK_CSS, PROD[page], stage)


def check_data():
    # ⚠ READ from the registry via gen_block_standard, not typed. A hand-kept list of "known"
    # competitions was here and is exactly the kind of thing that goes stale the day a
    # competition is onboarded.
    known = {c["league_code"] for c in ACTIVE}
    # ⚠ ONE GROUP PER COMPETITION on each view: each competition contributes
    # its NEXT matchday and nothing after it. With the day headings gone, a competition can no
    # longer appear twice at all -- so this is now a plain duplicate check.
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
    # ⚠ EVERY PLAYED ROW CARRIES A KICK-OFF AND A ZONE, exactly like an upcoming one -- that is
    # what "the same row" means, and it is the thing that regresses if someone re-adds a bespoke
    # right column.
    for code, _kind, dates in PAST_ROUNDS:
        for _date, matches in dates:
            for m in matches:
                # ⚠ a played row carries NO kick-off and therefore no timezone.
                # Four fields exactly: home, its goals, away, its goals.
                assert len(m) == 4, "%s: a played row still carries a kick-off" % code
    blob = repr(NEXT_ROUNDS) + repr(PAST_ROUNDS)
    for bad in ("Fu\u00dfball-Bundesliga", "Major League Soccer", "Liga Profesional"):
        assert bad not in blob, "long-form league name still present: %r" % bad
    # the next view must carry NO played matches -- those are the other page's whole purpose
    assert all(len(m) == 3 for _c, _k, ds in NEXT_ROUNDS for _d, ms in ds for m in ms), \
        "a next-view row is shaped like a played row"
    print("  %d next rounds \u00b7 %d past rounds \u00b7 one per competition \u00b7 every kickoff dated and "
          "zoned \u00b7 no day headings" % (len(NEXT_ROUNDS), len(PAST_ROUNDS)))


if __name__ == "__main__":
    check_data()
    for page, out in (("next", OUT_NEXT), ("past", OUT_PAST)):
        out.write_text(build(page), encoding="utf-8")
        print("  wrote %s (%.0f KB)" % (out.name, out.stat().st_size / 1024))
    # the old single stacked file must not survive alongside them
    stale = Path(__file__).with_name("matches_mock.html")
    if stale.exists():
        stale.unlink()
        print("  removed %s (the stacked two-in-one file it replaces)" % stale.name)
