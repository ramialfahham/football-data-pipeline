"""The Overview re-rendered with the rulings that closed the #129 review, without editing the
repo's generator (that lands with the build): Deserved points as the FULL TABLE right after the
Table (the shot balance, Deserved, Pts, Diff), the Better / Worse boards dropped, the six fact
rows as links. Real data: the committed Bundesliga payload + mart_team_profile (the README dates
the pull)."""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
sys.path.insert(0, str(HERE))

import gen_competition_hub as g  # noqa: E402
from gen_competition_hub import E, loc, team_cell  # noqa: E402

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


def build():
    k = g.KINDS["league"]
    return """<!doctype html>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Competition page, Overview -- Bundesliga (mock)</title>
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
""" % (g.SYSTEM_CSS.read_text(encoding="utf-8"), g.MOCK_CSS,
       g.header_html(k), "", g.table_html(k), deserved_table_html(), facts_html(k))


out = HERE / (sys.argv[1] if len(sys.argv) > 1 else "competition_overview_after_teams_v2.html")
out.write_text(build(), encoding="utf-8")
print("wrote", out.name)
