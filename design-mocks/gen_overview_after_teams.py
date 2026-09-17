"""The Overview re-rendered with the rulings that closed the #129 review, without editing the repo's generator
(that lands with the build): tab bar Overview · Matchdays · Team stats · Players; Deserved
points as the FULL TABLE right after the Table (shots on goal for:against, the balance, Deserved,
Pts, Diff), the Better / Worse boards dropped; one 14px gap from every block name to its first
line. Real data: the committed Bundesliga payload + mart_team_profile (the README dates the pull)."""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
sys.path.insert(0, str(HERE))

import gen_competition_hub as g  # noqa: E402
from gen_competition_hub import E, loc, team_cell  # noqa: E402

g.COPY["tabTeams"] = ("Rankings", "Rankingit", True)
g.COPY["colSog"] = ("Shots on goal", "Laukaukset maalia kohti", True)
g.COPY["colSogDiff"] = ("Balance", "Tase", True)
g.COPY["secDeserved"] = ("Deserved points table", "Ansaittujen pisteiden taulukko", False)

PAYLOAD = REPO / "site_v2/src/data/competitions/BL1/2026.json"
METRICS = HERE / "bl1_team_metrics.json"


def deserved_table_html():
    payload = json.loads(PAYLOAD.read_text(encoding="utf-8"))
    metrics = {m["team_name"]: m for m in json.loads(METRICS.read_bytes().decode("utf-8"))}
    rows = sorted(payload["deserved"], key=lambda r: (-r["deserved_points"], r["name"]))
    head = ('<div class="ctab-head"><span class="h rk">%s</span><span class="h nmh"></span>'
            '<span class="h">%s</span><span class="h">%s</span>'
            '<span class="h">%s</span><span class="h">%s</span></div>'
            % (loc("colPos"), loc("colSogDiff"), loc("colDeserved"), loc("colPoints"), loc("colDiff")))
    body = []

    def sgn(x):
        return "+" if x > 0.05 else ("\u2212" if x < -0.05 else "")

    for i, r in enumerate(rows, 1):
        m = metrics[r["name"]]
        bal = float(m["shots_on_goal_difference_per_match"])
        gap = r["deserved_points_gap"]
        body.append('<a class="ctab-row" href="/en/teams/%s/"><span class="rk num">%d</span>%s'
                    '<span class="n num">%s%.1f</span>'
                    '<span class="n num pts">%.1f</span><span class="n num">%d</span>'
                    '<span class="n num">%s%.1f</span></a>'
                    % (r["slug"], i, team_cell(r["name"]), sgn(bal), abs(bal),
                       r["deserved_points"], r["points"], sgn(gap), abs(gap)))
    return """
      <section>
        <div class="sechead"><span class="eyebrow">%s</span></div>
        <p class="bsub">%s</p>
        <div class="ctab dpt">%s
%s</div>
      </section>
""" % (loc("secDeserved"), loc("deservedExplainer"), head, "\n".join(body))


def facts_html(k):
    """Six fact rows, every one a link to the leaderboard behind its number (#140); the match that
    matters is struck from this block."""
    rows = []
    for key, value, context in k["facts"]:
        rows.append('<a class="frow" href="/en/leaderboards/bundesliga/%s/"><span class="fl">%s</span>'
                    '<span class="fv"><span class="fvv"><b>%s</b></span><span class="sub">%s</span></span></a>'
                    % (key[4:].lower(), loc(key), E(value), E(context)))
    return """
      <section>
        <div class="sechead"><span class="eyebrow">%s</span></div>
        <div class="facts">
%s
        </div>
      </section>
""" % (loc("secFacts"), "\n".join(rows))


EXTRA_CSS = """
/* the deserved table's own track list: # · club · SoG for:against · balance · Deserved · Pts · Diff */
.ctab.dpt, .ctab.dpt.ctab { --cols: 2rem minmax(0, 1fr) 3.6rem 4.2rem 2.6rem 3.2rem; }
/* the ordered-by number: bold, 15px, the accent, as the standings Pts (one rule, every block) */
.brow .v b { color: var(--accent); }
.frow .fvv b { color: var(--accent); font-weight: 700; font-size: 15px; }
/* on a striped table the hover is twice the stripe, or it cannot be seen */
@media (hover: hover) { .fx a.brow:hover, .fx a.comp-row:hover, .fx a.fxrow:hover, .fx a.ctab-row:hover, .fx a.frow:hover { background: color-mix(in srgb, var(--ink) 11%, transparent); } }
/* the block name, a step larger everywhere (was 11px): it got buried */
.sechead .eyebrow { font-size: 13px; }
/* ONE gap from a block name to its first line: the heading's 14px, nothing added by the content */
section > .sechead + .fxgroup { margin-top: 0; }
section > .sechead + .fxgroup > .dh:first-child { padding-top: 0; }
section > .sechead + .ctab-section { margin-top: 0; }
section > .sechead + .ctab { margin-top: 0; }
section > .sechead + .bsub { margin-top: 0; }
section > .sechead + .facts { margin-top: 0; }
section > .sechead + .facts > .frow:first-child { padding-top: 0; }
"""


def build():
    k = g.KINDS["league"]
    return """<!doctype html>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Competition page, Overview -- Bundesliga (mock)</title>
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
%s
%s
    </div>
  </div>
</div>

<div class="legend">
  <b>Mock &mdash; the competition page, Overview, with the rulings of 2026-09-16.</b>
  Table &middot; Deserved points (the full table) &middot; The season in numbers; Next matches struck (the Matchdays tab opens on it).
  Shots on goal are per match, the catalogue's measure; totals are not defined.
</div>
""" % (g.SYSTEM_CSS.read_text(encoding="utf-8"), g.ROW_CSS, g.INTERACTION_CSS, g.MOCK_CSS, EXTRA_CSS,
       g.header_html(k), "", g.table_html(k), deserved_table_html(), facts_html(k))


def three_tabs(html_):
    """The repo generator draws four tabs; the fourth (Players) is gone since the three-tab ruling."""
    fourth = '        <span class="tab" aria-disabled="true">%s</span>\n' % g.loc("tabPlayers")
    assert html_.count(fourth) == 1
    return html_.replace(fourth, "")


out = HERE / (sys.argv[1] if len(sys.argv) > 1 else "competition_overview_after_teams_v2.html")
out.write_text(three_tabs(build()), encoding="utf-8")
print("wrote", out.name)
