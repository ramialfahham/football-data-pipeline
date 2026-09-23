"""Render the MATCHES HUB, /{locale}/matches/, what the Matches menu item lands on, for #130.

Real data: every fixture of Saturday 19 September 2026 (the UTC kick-off date) as prod
`marts.mart_competition_fixtures` held it, joined to `marts.mart_competition_index` for the
competition's name, kind, confederation and region rank: 152 matches in 19 competitions
(`matches_2026-09-19.json`, the JSON the `bq` CLI wrote). Drawn as the page read that morning,
so every row shows its kick-off and none its score. Times in UTC with the label, as the built
site shows them until the venue's clock lands (#146).

Composed only of what the site already has: the Competitions page's breadcrumb, heading and two
filter rows (their radios and CSS unchanged, so the filters work here too); the Matchdays tab's
picker with a date as its title; its Schedule block holding the shared competition group head and
match row from `rows.py`. The block omits the date heading because the picker already names the
day: a block may omit a level the page supplies (`rows.group_head`).

    python design-mocks/render.py gen_matches_hub.py matches-hub                        every match
    MATCHES_HUB_FOLD=3 python design-mocks/render.py gen_matches_hub.py matches-hub     Home's fold
"""
import json
import os
import sys
from collections import OrderedDict
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from gen_competition_hub import COPY, E, MOCK_CSS, SYSTEM_CSS, loc  # noqa: E402
from gen_competition_matchdays import CHEV_L, CHEV_R  # noqa: E402
from rows import group_head, upcoming_row  # noqa: E402

DATA = HERE / "matches_2026-09-19.json"
# rows shown per competition before Home's fold (`.fxmore`); unset shows every row. The variant
# exists because the FA Cup plays 77 qualifying ties that Saturday and sorts second.
FOLD = int(os.environ.get("MATCHES_HUB_FOLD", "0")) or None

COPY.update({
    "navMatches":     ("Matches", "Ottelut", False),
    "filterAll":      ("All", "Kaikki", False),
    "filterClubs":    ("Clubs", "Seurat", False),
    "filterNational": ("National teams", "Maajoukkueet", False),
    "confedUefa":     ("Europe", "Eurooppa", False),
    "confedConmebol": ("South America", "Etelä-Amerikka", False),
    "confedConcacaf": ("North & Central America", "Pohjois- ja Keski-Amerikka", False),
    "confedCaf":      ("Africa", "Afrikka", False),
    "confedAfc":      ("Asia", "Aasia", False),
    "confedOfc":      ("Oceania", "Oseania", False),
    "confedFifa":     ("World", "Maailma", False),
    "day":            ("Saturday 19 September", "Lauantai 19. syyskuuta", False),
    "homeShowAll":    ("Show all {n}", "Näytä kaikki {n}", False),
    "jumpLabel":      ("Schedule", "Otteluohjelma", False),
})

SUMMARY_CHEV = ('<svg class="chev" viewBox="0 0 24 24" aria-hidden="true" focusable="false">'
                '<path d="M9 6l6 6-6 6" fill="none" stroke="currentColor" stroke-width="2.2" '
                'stroke-linecap="round" stroke-linejoin="round"></path></svg>')


def loc_n(key, n):
    en, fi, _ = COPY[key]
    return ('<span class="en">%s</span><span class="fi" lang="fi">%s</span>'
            % (E(en.format(n=n)), E(fi.format(n=n))))

ENTITY_FILTERS = [("all", "", "filterAll"), ("club", "club", "filterClubs"),
                  ("national", "national", "filterNational")]
REGION_FILTERS = [("all", "", "filterAll"), ("uefa", "UEFA", "confedUefa"),
                  ("conmebol", "CONMEBOL", "confedConmebol"), ("concacaf", "CONCACAF", "confedConcacaf"),
                  ("caf", "CAF", "confedCaf"), ("afc", "AFC", "confedAfc"), ("ofc", "OFC", "confedOfc"),
                  ("fifa", "FIFA", "confedFifa")]

PROVENANCE = [
    ("Breadcrumb, heading", "copy: crumbHome, navMatches"),
    ("Filter rows", "copy: filterAll, filterClubs, filterNational, confed*; values: mart_competition_index.entity_type, .confederation"),
    ("Day line", "the build day (a UTC date); mart_competition_fixtures.fixture_date"),
    ("Block name", "copy: compSecSchedule (the Matchdays tab's block)"),
    ("Competition head", "mart_competition_index.competition_name, .slug (link), .logo_url"),
    ("Competition order", "mart_competition_index.region_rank, then first kick-off, then league_code"),
    ("Match row", "mart_competition_fixtures: home/away_team_name, kickoff_datetime, fixture_slug (link)"),
]


def load():
    rows = json.loads(DATA.read_text(encoding="utf-8"))
    groups = OrderedDict()
    for r in sorted(rows, key=lambda r: (r["league_code"], r["kickoff_datetime"])):
        groups.setdefault(r["league_code"], []).append(r)
    return sorted(groups.values(),
                  key=lambda g: (int(g[0]["region_rank"]), g[0]["kickoff_datetime"], g[0]["league_code"]))


def filters_html():
    radios = [('<input class="seg-in" type="radio" name="entity-filter" id="filter-entity-%s" value="%s"%s>'
               % (i, v, " checked" if not v else "")) for i, v, _ in ENTITY_FILTERS]
    radios += [('<input class="seg-in" type="radio" name="region-filter" id="filter-region-%s" value="%s"%s>'
                % (i, v, " checked" if not v else "")) for i, v, _ in REGION_FILTERS]
    entity = "".join('<label class="seg-btn" for="filter-entity-%s">%s</label>' % (i, loc(k))
                     for i, _, k in ENTITY_FILTERS)
    region = "".join('<label class="seg-btn" for="filter-region-%s">%s</label>' % (i, loc(k))
                     for i, _, k in REGION_FILTERS)
    return ("\n".join(radios)
            + '\n<div class="seg" role="group" aria-label="Filter by type">%s</div>' % entity
            + '\n<div class="seg wrap" role="group" aria-label="Filter by region">%s</div>' % region)


def day_html(groups):
    step = ('<nav class="mdnav" aria-label="Pick a day"><span class="mdstep">'
            '<a class="step prev" href="#" aria-label="Friday 18 September">%s</a>'
            '<span class="mdtitle"><b class="num">%s</b></span>'
            '<a class="step next" href="#" aria-label="Sunday 20 September">%s</a>'
            '</span></nav>' % (CHEV_L, loc("day"), CHEV_R))
    body = []
    for g in groups:
        first = g[0]
        kind = "nation" if first["entity_type"] == "national" else "club"
        rows = [upcoming_row(kind, r["home_team_name"], r["away_team_name"],
                             r["kickoff_datetime"][11:16], "UTC",
                             "/en/%s/matches/%s/" % (r["competition_slug"], r["fixture_slug"]))
                for r in g]
        if FOLD and len(rows) > FOLD:
            rows = rows[:FOLD] + [
                '<details class="fxmore"><summary><span class="lbl">%s</span>%s</summary>\n%s\n</details>'
                % (loc_n("homeShowAll", len(rows)), SUMMARY_CHEV, "\n".join(rows[FOLD:]))]
        body.append('<div class="fxgroup" data-entity-type="%s" data-confederation="%s">\n%s\n%s\n</div>'
                    % (E(first["entity_type"]), E(first["confederation"]),
                       group_head(first["competition_slug"], first["competition_name"]), "\n".join(rows)))
    return """<div class="md">
<input class="md-in" type="radio" name="day" id="day-2026-09-19" checked>
%s
<section>
  <div class="sechead"><span class="eyebrow">%s</span></div>
%s
</section>
</div>""" % (step, loc("jumpLabel"), "\n".join(body))


def provenance_html():
    rows = "".join("<tr><td>%s</td><td>%s</td></tr>" % (E(a), E(b)) for a, b in PROVENANCE)
    return '<table class="prov"><tr><th>Element</th><th>Source</th></tr>%s</table>' % rows


def build():
    groups = load()
    n_matches = sum(len(g) for g in groups)
    variant = ("One day, every competition playing it, the first %d matches of each, the rest under "
               "Home's &ldquo;Show all&rdquo;." % FOLD if FOLD else
               "One day, every competition playing it, every match.")
    return """<!doctype html>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Matches hub (mock)</title>
<style>
%s
%s
.prov { border-collapse: collapse; margin-top: 10px; }
.prov td, .prov th { text-align: left; padding: 3px 12px 3px 0; vertical-align: top; }
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
      <nav class="crumb" aria-label="Breadcrumb"><a class="lnk" href="#">%s</a><span class="sep">&rsaquo;</span><span class="here">%s</span></nav>
      <h1>%s</h1>
%s
      <div class="categories">
%s
      </div>
    </div>
  </div>
</div>

<div class="legend">
  <b>Mock: the Matches hub, what the Matches menu item lands on (proposal for #130).</b>
  %s Real data: the %d matches in %d
  competitions of Saturday 19 September 2026 as prod held them, drawn as the page read that
  morning, so rows show kick-offs, not scores. Times in UTC. The filters work; the day arrows
  lead to the days behind the hub, which are #131.
  %s
</div>
""" % (SYSTEM_CSS.read_text(encoding="utf-8"), MOCK_CSS, loc("crumbHome"), loc("navMatches"),
       loc("navMatches"), filters_html(), day_html(groups), variant, n_matches, len(groups),
       provenance_html())


if __name__ == "__main__":
    out = HERE / (sys.argv[1] if len(sys.argv) > 1 else "matches-hub.html")
    out.write_text(build(), encoding="utf-8")
    print("wrote", out, "%.0f KB" % (out.stat().st_size / 1024))
