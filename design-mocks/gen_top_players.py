"""Render the Top players home-page block as a standalone HTML mock with placeholder numbers.

Metric names come from the catalogue by (metric_id, entity), and the page uses no JavaScript.
"""
import csv
import html
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
CATALOGUE = REPO / "dbt_project/seeds/metric_catalogue.csv"
SYSTEM_CSS = REPO / "site_v2/src/styles/system.css"
OUT = Path(__file__).with_name("top_players_mock.html")

# ---------------------------------------------------------------- catalogue

_ROWS = list(csv.DictReader(CATALOGUE.open(encoding="utf-8")))
_BY_KEY = {(r["metric_id"], r["entity"]): r for r in _ROWS}
_STRINGS = (REPO / "site_v2/src/i18n/strings.ts").read_text(encoding="utf-8")
_WORD = dict(re.findall(r'(?<![A-Za-z0-9_])([A-Za-z0-9_]+):\s*"([^"]*)"',
                        re.search(r"\nconst EN: Dict = \{([\s\S]*?)\n\};", _STRINGS).group(1)))
_EN = {key: _WORD[term]
       for key, term in re.findall(r'"([A-Za-z0-9_]+(?:\.[A-Za-z0-9_]+)+)":\s*"([A-Za-z0-9_]+)"', re.search(
           r"const METRIC_TERMS: Record<string, string> = \{([\s\S]*?)\n\};", _STRINGS).group(1))
       if term in _WORD}


def label(metric_id, entity="player"):
    """The English name of one metric. Hard-fails on an unknown id -- never invent a label."""
    row = _BY_KEY.get((metric_id, entity))
    if row is None:
        known = sorted(m for (m, e) in _BY_KEY if e == entity)
        sys.exit(
            "FATAL: no '%s' row for metric_id '%s' in %s\n"
            "The board name and every column header are GOVERNED values.\n"
            "Known %s ids: %s" % (entity, metric_id, CATALOGUE.name, entity, ", ".join(known))
        )
    lab = _EN.get(row["label_i18n_key"], "").strip()
    if not lab:
        sys.exit("FATAL: metric '%s' (%s) has no English name in strings.ts." % (metric_id, entity))
    return lab


# ------------------------------------------------------- Finnish width probe
#
# The second element is unused: the renderer marks every Finnish title as a probe.
FI = {
    "goals_player": ("Maalit", False),
    "assists_player": ("Maalisyötöt", False),
    "passes_player": ("Syötöt", False),
    "passes_key_player": ("Avainsyötöt", False),
}

# --------------------------------------------------------------- sample data
#
# Placeholder data: the player names are real, the numbers are invented.
BOARDS = [
    {
        "rank_metric": "goals_player",
        "rows": [
            ("RMA", "Kylian Mbappé", "Real Madrid · La Liga", "21"),
            ("BAY", "Harry Kane", "Bayern München · Bundesliga", "20"),
            ("MCI", "Erling Haaland", "Manchester City · Premier League", "19"),
            ("PSG", "Ousmane Dembélé", "Paris Saint-Germain · Ligue 1", "16"),
            ("INT", "Lautaro Martínez", "Inter · Serie A", "15"),
            ("SCP", "Luis Suárez", "Sporting CP · Liga Portugal", "14"),
            ("PSV", "Luuk de Jong", "PSV · Eredivisie", "13"),
        ],
    },
    {
        "rank_metric": "assists_player",
        "rows": [
            ("LIV", "Mohamed Salah", "Liverpool · Premier League", "14"),
            ("BAY", "Michael Olise", "Bayern München · Bundesliga", "13"),
            ("BAR", "Lamine Yamal", "Barcelona · La Liga", "12"),
            ("PSG", "Vitinha", "Paris Saint-Germain · Ligue 1", "11"),
            ("INT", "Hakan Çalhanoğlu", "Inter · Serie A", "10"),
            ("FEY", "Igor Paixão", "Feyenoord · Eredivisie", "9"),
            ("SCP", "Francisco Trincão", "Sporting CP · Liga Portugal", "9"),
        ],
    },
    {
        "rank_metric": "passes_player",
        "rows": [
            ("MCI", "Rodri", "Manchester City · Premier League", "1842"),
            ("BAY", "Joshua Kimmich", "Bayern München · Bundesliga", "1791"),
            ("BAR", "Frenkie de Jong", "Barcelona · La Liga", "1720"),
            ("PSG", "Vitinha", "Paris Saint-Germain · Ligue 1", "1688"),
            ("INT", "Hakan Çalhanoğlu", "Inter · Serie A", "1604"),
            ("AJA", "Jorrel Hato", "Ajax · Eredivisie", "1521"),
            ("SCP", "Morten Hjulmand", "Sporting CP · Liga Portugal", "1498"),
        ],
    },
    {
        "rank_metric": "passes_key_player",
        "rows": [
            ("MUN", "Bruno Fernandes", "Manchester United · Premier League", "62"),
            ("BAR", "Lamine Yamal", "Barcelona · La Liga", "58"),
            ("BAY", "Michael Olise", "Bayern München · Bundesliga", "55"),
            ("PSG", "Vitinha", "Paris Saint-Germain · Ligue 1", "51"),
            ("INT", "Hakan Çalhanoğlu", "Inter · Serie A", "47"),
            ("FEY", "Igor Paixão", "Feyenoord · Eredivisie", "43"),
            ("SCP", "Geovany Quenda", "Sporting CP · Liga Portugal", "40"),
        ],
    },
]

# --------------------------------------------------------------------- build

E = html.escape

# A neutral inline-SVG crest: the mock must not hotlink the provider's images.
CREST = (
    '<svg viewBox="0 0 24 24" aria-hidden="true" focusable="false">'
    '<path d="M12 3.2l6.6 2.35v5.65c0 3.95-2.73 7.15-6.6 8.95'
    '-3.87-1.8-6.6-5-6.6-8.95V5.55L12 3.2z"'
    ' fill="none" stroke="currentColor" stroke-width="1.6" opacity=".42"/></svg>'
)


def board_title(metric_id, lab, loc="en", entity="player"):
    """A board name, plus "per match" for per-match averages, as the site's boardTitle() builds it."""
    row = _BY_KEY[(metric_id, entity)]
    if row["denominator_expr"].strip() == "count(*)" and row["format"] != "percent":
        return "%s %s" % (lab, {"en": "per match", "fi": "ottelua kohden"}[loc])
    return lab


def direction(metric_id, entity="player"):
    """The metric's own direction, from the catalogue."""
    return _BY_KEY[(metric_id, entity)]["direction"]


def check_order(board):
    """Every board ranks descending, and a lower-is-better metric must be explicitly allowed."""
    rank_id = board["rank_metric"]
    vals = [float(r[3]) for r in board["rows"]]
    assert vals == sorted(vals, reverse=True), (
        "%s must run high->low; got %s" % (rank_id, vals))
    if direction(rank_id) != "higher_better":
        # Descending on a lower-is-better metric puts the worst first.
        assert board.get("allow_desc_against_direction"), (
            "%s is %s -- ranking it descending surfaces the worst players first. Either drop "
            "the board or record the ruling in allow_desc_against_direction."
            % (rank_id, direction(rank_id)))
    return direction(rank_id)


def board_html(board):
    rank_id = board["rank_metric"]
    title_en = board_title(rank_id, label(rank_id), "en")
    fi_raw, _ = FI[rank_id]
    title_fi = board_title(rank_id, fi_raw, "fi")

    parts = ['<div class="board">']
    parts.append(
        '<div class="bhd"><span class="bt">'
        '<span class="en">%s</span>'
        '<span class="fi probe" lang="fi">%s</span>'
        "</span></div>" % (E(title_en), E(title_fi))
    )
    # One metric per board, so the title is the only label and there is no column-header row.
    parts.append('<div class="bgrid">')
    for i, (abbr, team, league, value) in enumerate(board["rows"], start=1):
        parts.append(
            '<a class="brow" href="#">'
            '<span class="rk num">%d</span>'
            '<span class="crest xs">%s</span>'
            '<span class="ent"><span class="nm">%s</span>'
            '<span class="sub">%s</span></span>'
            '<span class="v"><b>%s</b></span></a>'
            % (i, CREST, E(team), E(league), E(value))
        )
    parts.append("</div></div>")
    return "\n".join(parts)


MOCK_CSS = """
/* ---------------------------------------------------------------- *
 *  MOCK HARNESS ONLY -- not part of the design.                     *
 *  Light tokens are copied verbatim from system.css's               *
 *  .fx[data-theme="light"] block, because CSS cannot set an         *
 *  attribute and the review surface runs no JavaScript.             *
 * ---------------------------------------------------------------- */
body { margin: 0; background: #06070a; font: 400 15px/1.5 system-ui, -apple-system, "Segoe UI", Roboto, sans-serif; }
.ctl { position: sticky; top: 0; z-index: 9; display: flex; flex-wrap: wrap; gap: 18px;
       padding: 12px 16px; background: #14161c; border-bottom: 1px solid #2b2f38; color: #c7ccd4; font-size: 13px; }
.ctl label { display: inline-flex; align-items: center; gap: 7px; cursor: pointer; user-select: none; }
.ctl .hint { color: #7c828c; font-size: 12px; }
.toggle { position: absolute; width: 1px; height: 1px; opacity: 0; pointer-events: none; }
/* the visible box, since the real input is offscreen */
.ctl .box { width: 15px; height: 15px; border-radius: 4px; border: 1px solid #4a505b; background: #0d0f13; flex: 0 0 auto; }
#t-light:checked ~ .ctl label[for="t-light"] .box,
#t-phone:checked ~ .ctl label[for="t-phone"] .box,
#t-fi:checked    ~ .ctl label[for="t-fi"]    .box { background: #3bb072; border-color: #3bb072; }
.toggle:focus-visible ~ .ctl label .box { outline: 2px solid #3bb072; outline-offset: 2px; }
.stage { margin: 0 auto; transition: max-width .15s; }
.legend { max-width: 680px; margin: 0 auto; padding: 14px 16px 0; color: #7c828c; font-size: 12px; line-height: 1.6; }
.legend b { color: #c7ccd4; }

#t-phone:checked ~ .stage { max-width: 375px; box-shadow: 0 0 0 1px #2b2f38; }

#t-light:checked ~ .stage .fx {
  --page: #f3f3f0; --surface: #fbfbf9; --sunk: #edece7; --line: #e2e1da; --div: #cfcec5;
  --ink: #141410; --ink-2: #4c4c45; --muted: #77776e;
  --accent: #0a6e3a;
  --win: #157f43; --draw: #6f756d; --loss: #b23b3b; --pill-ink: #fff;
  --track: #e7e6e0;
}

/* locale swap for the width probe */
.fi { display: none; }
#t-fi:checked ~ .stage .en { display: none; }
#t-fi:checked ~ .stage .fi { display: inline; }
/* strings that do NOT exist in strings.ts yet -- plausible worst case, not approved copy */
#t-fi:checked ~ .stage .probe { text-decoration: underline dotted currentColor; text-underline-offset: 3px; }

.crest.xs svg { width: 15px; height: 15px; display: block; color: var(--muted); }
"""


def build():
    system_css = SYSTEM_CSS.read_text(encoding="utf-8")
    boards = "\n".join(board_html(b) for b in BOARDS)

    return """<!doctype html>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Top players -- home page block (mock)</title>
<style>
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

      <section>
        <div class="sechead"><span class="eyebrow">Top players</span></div>
        <p class="tt-intro">Season totals to date. Ranked across pooled leagues:
          <b>Premier League, La Liga, Bundesliga, Serie A, Ligue 1, Liga Portugal,
          Eredivisie</b>.</p>
%s
      </section>

    </div>
  </div>
</div>

<div class="legend">
  <b>Layout mock, not a data preview.</b> The players are real people; every number beside them
  is <b>invented</b> and was never measured. Do not read a ranking off this page.
  Each board name is the English name in <b>strings.ts</b> of the <b>metric_catalogue.csv</b> key, looked up by
  (metric_id, entity=player); the generator exits on an unknown id, and it checks each board's
  sort against that metric's <b>direction</b>.
  ⚠ <b>Every Finnish string here is a probe</b> (dotted): METRIC_TERMS currently names only
  team per-match metrics, so none of these eight has approved Finnish copy.
  League names are left in English &mdash; the probe is about metric labels.
</div>
""" % (system_css, MOCK_CSS, boards)


def check_orders():
    for b in BOARDS:
        d = check_order(b)
        flag = "   <-- DESC AGAINST CATALOGUE DIRECTION" if d == "lower_better" else ""
        print("  %-32s desc | catalogue: %s%s" % (b["rank_metric"], d, flag))


def check_guards():
    """Prove the unknown-id guard fires, including for an id that exists only for teams."""
    for bad in ("goals_per_matchx", "points_capture"):
        try:
            label(bad)
        except SystemExit as exc:
            print("  unknown-id guard fired for %-18s -> %s" % (bad, str(exc).splitlines()[0]))
        else:
            sys.exit("FATAL: the unknown-id guard did NOT fire for '%s'." % bad)

    assert label("goals_player") == "Goals", label("goals_player")
    print("  known id still resolves -> %s" % label("goals_player"))


if __name__ == "__main__":
    if sys.argv[1:2] == ["--out"]:
        OUT = Path(sys.argv[2]) / OUT.name
    check_guards()
    check_orders()
    OUT.write_text(build(), encoding="utf-8")
    print("wrote", OUT, OUT.stat().st_size, "bytes")
