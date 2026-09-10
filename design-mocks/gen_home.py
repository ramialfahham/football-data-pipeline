"""Compose the whole home page: next matches -> Top players -> Top teams -> browse.

That order is §0's composition (CPO 2026-08-08). The two stats blocks slot BETWEEN the two
shipped modules, and browse holds the bottom slot deliberately so the follow-up inserts
rather than rearranges.

⚠ What is real and what is not:
  * Top players / Top teams markup is imported from the two block generators, so this page
    cannot drift from the mocks that were approved.
  * Next matches and Browse are MOCKED here, but their markup mirrors the shipped components
    (`HeroFixtures.astro`, `BrowseGrid.astro`) class for class -- `.fxgroup > .gh`, `.fxrow`
    with `.sides`/`.side`/`.when`, and `.colhead`/`.subhead`/`.linkrow`/`.linkchip`. Browse
    chips are `<span>`, not `<a>`, exactly as shipped: the competition hub does not exist
    yet, and system.css scopes the hover affordance to `a.linkchip`.
  * Every number is placeholder.

Purpose is COMPOSITION and PAGE LENGTH, which is the open item: 4+4 boards at top 7 is 56
board rows on a page that measured 4126px on mobile with only two modules built.
"""
import html
import sys
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))

# noqa: E402 x5 — this file is executed directly and imports its siblings, so the `sys.path`
# insert above must run first. What trips E402 is the `HERE =` assignment, not the insert; the
# same shim carries the same marker everywhere else in this repo.
import gen_top_players as P  # noqa: E402
import gen_top_teams as T  # noqa: E402
from gen_block_standard import ZONE, short, slug  # noqa: E402
from interaction import INTERACTION_CSS  # noqa: E402
from rows import ROW_CSS, date_head, group_head, upcoming_row  # noqa: E402

OUT = HERE / "home_mock.html"
E = html.escape

# ------------------------------------------------------------ next matches
#
# ⚠ REBUILT ON THE SHARED BLOCK, 2026-08-10. This section carried its own copy of the
# `.fxgroup`/`.fxrow` markup, which is how one piece of content ended up with four different
# treatments across the site. It now calls `rows.py` -- the same functions the Matches page and
# the competition page call -- so the three surfaces cannot drift.
#
# Grouping is COMPETITION then DATE, on every surface. Names, slugs and timezones come from
# `gen_block_standard`, which reads the registry, so nothing here is a typed label.
#
# (league_code, [(date, [(home, away, kickoff)])])
FIXTURES = [
    ("PL", [("Sat 14 Feb", [("Arsenal", "Manchester City", "17:30"),
                            ("Liverpool", "Brighton & Hove Albion", "20:00")]),
            ("Sun 15 Feb", [("Brentford", "Everton", "15:00")])]),
    ("PD", [("Sat 14 Feb", [("Real Madrid", "Athletic Club", "21:00")]),
            ("Sun 15 Feb", [("Barcelona", "Real Valladolid", "18:30")])]),
    ("BL1", [("Sat 14 Feb", [("1. FC Heidenheim", "Bayer 04 Leverkusen", "15:30"),
                             ("Bayern München", "Borussia Mönchengladbach", "18:30")])]),
    ("SA", [("Sat 14 Feb", [("Inter", "Atalanta", "20:45")]),
            ("Sun 15 Feb", [("Napoli", "Lecce", "18:00")])]),
    ("L1", [("Sat 14 Feb", [("Paris Saint-Germain", "Lens", "21:00")]),
            ("Sun 15 Feb", [("Le Havre", "Monaco", "17:00")])]),
    ("ED", [("Sun 15 Feb", [("PSV", "Feyenoord", "14:30")])]),
]

# ⚠ FLAT (CPO 2026-08-10): one row of chips, no "by competition" / "by country" axes. Both
# axes listed the SAME twelve competitions, so the second was a repeat of the first with a
# country heading above it.
#
# These are the twelve the registry marks `status: active`, names verbatim from its `name`
# field -- so the mock cannot invent a competition or a label.
BROWSE = ["Premier League", "La Liga", "1. Fußball-Bundesliga", "Serie A", "Ligue 1",
          "Liga Portugal", "Eredivisie", "2. Fußball-Bundesliga", "Liga MX",
          "Saudi Pro League", "Major League Soccer", "Veikkausliiga"]


def sechead(label):
    return '<div class="sechead"><span class="eyebrow">%s</span></div>' % E(label)


def next_matches():
    """THE SHARED BLOCK. No markup is written here — every element comes from `rows.py`."""
    out = ["<section>", sechead("Next matches")]
    for code, dates in FIXTURES:
        out.append('<div class="fxgroup">%s' % group_head(slug(code), short(code)))
        for date, matches in dates:
            out.append(date_head(date))
            for home, away, time in matches:
                out.append(upcoming_row("club", home, away, time, ZONE[code] or "—"))
        out.append("</div>")
    out.append("</section>")
    return "\n".join(out)


def browse():
    """Flat: the section head, then one row of chips.

    ⚠ Chips are rendered as ANCHORS here, per the CPO's "it's fine if they redirect to the
    leagues". The SHIPPED component emits `<span>` on purpose -- the competition hub
    (/{locale}/{slug}/) does not exist yet, so an anchor today is a guaranteed 404 behind
    every chip. system.css scopes the hover affordance to `a.linkchip`, so the tag swap is
    the whole edit when the hub lands.
    """
    chips = "".join('<a class="linkchip" href="#">%s</a>' % E(c) for c in BROWSE)
    return '<section>%s<div class="linkrow">%s</div></section>' % (sechead("Browse"), chips)


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
    browse(),
])

system_css = T.SYSTEM_CSS.read_text(encoding="utf-8")

OUT.write_text("""<!doctype html>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Home -- all four modules (mock)</title>
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
  <span class="hint">next matches &rarr; Top players &rarr; Top teams &rarr; browse</span>
</div>

<div class="stage">
  <div class="fx">
    <div class="inner">
%s
    </div>
  </div>
</div>

<div class="legend">
  <b>Composition mock.</b> The order is &sect;0's: next matches &rarr; Top players &rarr; Top teams
  &rarr; browse. <b>Top players and Top teams are generated from the same code as their own
  mocks</b>, so this page cannot drift from what was approved. Next matches and Browse are mocked,
  but mirror the shipped components class for class &mdash; browse chips are
  <b>&lt;span&gt;</b> not <b>&lt;a&gt;</b>, as shipped, because the competition hub does not exist
  yet. Every number is placeholder.
</div>
""" % (system_css, ROW_CSS, INTERACTION_CSS, T.MOCK_CSS, page), encoding="utf-8")

print("wrote", OUT, OUT.stat().st_size, "bytes")
print("board rows:", sum(len(b["rows"]) for b in P.BOARDS) + sum(len(b["rows"]) for b in T.BOARDS))
print("fixtures:", sum(len(r) for _, r in FIXTURES))
