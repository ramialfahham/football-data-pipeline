"""Render the Top teams home-page block as a standalone HTML mock.

Design-only. Reads nothing from BigQuery; the numbers are PLACEHOLDER.

Two things are read from the repo so the mock cannot drift from the product:
  1. every display name comes from `label_en` in dbt_project/seeds/metric_catalogue.csv,
     looked up by (metric_id, entity) -- the catalogue's real grain. Two of the ids used
     here carry BOTH a team and a player row, so keying on metric_id alone silently takes
     the wrong label; that is the exact bug export_metric_definitions_json.py once had.
     An unknown id is a hard failure, never a fallback string.
  2. site_v2/src/styles/system.css is inlined verbatim, so the mock uses the shipped
     design system rather than a lookalike.

No JavaScript: the review surface is a static snapshot, so script never runs. The three
toggles are :checked + sibling combinators.
"""
import csv
import html
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
CATALOGUE = REPO / "dbt_project/seeds/metric_catalogue.csv"
SYSTEM_CSS = REPO / "site_v2/src/styles/system.css"
OUT = Path(__file__).with_name("top_teams_mock.html")

# ---------------------------------------------------------------- catalogue

_ROWS = list(csv.DictReader(CATALOGUE.open(encoding="utf-8")))
_BY_KEY = {(r["metric_id"], r["entity"]): r for r in _ROWS}


def label(metric_id, entity="team"):
    """label_en for one metric. Hard-fails on an unknown id -- never invent a label."""
    row = _BY_KEY.get((metric_id, entity))
    if row is None:
        known = sorted(m for (m, e) in _BY_KEY if e == entity)
        sys.exit(
            "FATAL: no '%s' row for metric_id '%s' in %s\n"
            "The board name and every column header are GOVERNED values.\n"
            "Known %s ids: %s" % (entity, metric_id, CATALOGUE.name, entity, ", ".join(known))
        )
    lab = (row["label_en"] or "").strip()
    if not lab:
        sys.exit("FATAL: metric '%s' (%s) has an empty label_en." % (metric_id, entity))
    return lab


# ------------------------------------------------------- Finnish width probe
#
# Real shipped strings come from METRIC_LABELS_FI in site_v2/src/i18n/strings.ts.
# That dict covers ~35 of the 80 catalogue rows, so three of the labels this block
# needs do not exist yet. Those are marked PROBE and rendered with a dotted underline:
# they are plausible worst-case strings for measuring width, NOT approved copy.
FI = {
    "points_capture": ("% Kerätyt pisteet", True),
    "points_won": ("Voitetut pisteet", True),
    "deserved_points": ("Ansaitut pisteet", True),
    "goals_per_match": ("Ø Maalit", False),
    "goals_against_per_match": ("Ø Päästetyt maalit", False),
    "sot_difference_per_match": ("Ø Maalilaukauksien ero", False),
    "shots_on_goal_per_match": ("Ø Maalilaukaukset", True),
    "shots_on_goal_against_per_match": ("Ø Maalilaukaukset vastaan", False),
    "finishing_efficiency": ("% Viimeistelytehokkuus", False),
    "defensive_actions_per_match": ("Ø Puolustustoimet", False),
    "passes_per_match": ("Ø Syötöt", False),
    "pass_accuracy": ("% Syöttötarkkuus", False),
    "key_passes_per_match": ("Ø Avainsyötöt", False),
    "duels_per_match": ("Ø Kaksinkamppailut", False),
    "duels_won_pct": ("% Voitetut kaksinkamppailut", False),
}

# --------------------------------------------------------------- sample data
#
# PLACEHOLDER numbers, internally consistent but not measured. Pool 1, mid-season,
# leagues deliberately at DIFFERENT matchday counts so the points denominators differ --
# that is a real property of a pooled board and the design has to survive it.

"""
FOUR boards, the locked cut (#41) in its stated order:

    goals -> shots on target -> passes -> duels

Every board is ONE shape: one metric, ONE value column, no column-header row -- matching Top
players. The rendered mock is the proof: 4 boards, 28 rows, 28 value cells.

Against §0's six, all ruled together:
  * "% Points captured" dropped as a board; `points_capture` is shown nowhere.
  * "Ø Defensive actions" dropped.
  * "Ø Key passes" dropped from the passes board.
  * deserved-vs-actual dropped: deserved points needs ONE ladder to mean anything, so it
    is a within-league number and a board pooling seven leagues cannot carry it. That
    takes `deserved_points` and `points_won` off the block entirely.
  * the shots board ranks on `shots_on_goal_per_match`, NOT on the difference, and §0's
    column order on Passes is reversed so the rank metric leads.

Consequence worth noting for the mart: `sot_difference_per_match` and `finishing_efficiency`
are no longer used by this block at all.
"""
BOARDS = [
    {
        "rank_metric": "goals_per_match",
        "rows": [
            ("BAY", "Bayern München", "Bundesliga", "3.2"),
            ("PSV", "PSV", "Eredivisie", "3.0"),
            ("RMA", "Real Madrid", "La Liga", "2.6"),
            ("PSG", "Paris Saint-Germain", "Ligue 1", "2.5"),
            ("ARS", "Arsenal", "Premier League", "2.3"),
            ("BAR", "Barcelona", "La Liga", "2.2"),
            ("INT", "Inter", "Serie A", "2.1"),
        ],
    },
    {
        "rank_metric": "shots_on_goal_per_match",
        "rows": [
            ("BAY", "Bayern München", "Bundesliga", "7.4"),
            ("ARS", "Arsenal", "Premier League", "6.8"),
            ("PSG", "Paris Saint-Germain", "Ligue 1", "6.4"),
            ("RMA", "Real Madrid", "La Liga", "6.2"),
            ("INT", "Inter", "Serie A", "5.9"),
            ("MCI", "Manchester City", "Premier League", "5.7"),
            ("BAR", "Barcelona", "La Liga", "5.5"),
        ],
    },
    {
        "rank_metric": "passes_per_match",
        "rows": [
            ("MCI", "Manchester City", "Premier League", "682"),
            ("BAY", "Bayern München", "Bundesliga", "651"),
            ("BAR", "Barcelona", "La Liga", "640"),
            ("PSG", "Paris Saint-Germain", "Ligue 1", "611"),
            ("NAP", "Napoli", "Serie A", "574"),
            ("RMA", "Real Madrid", "La Liga", "566"),
            ("BHA", "Brighton & Hove Albion", "Premier League", "559"),
        ],
    },
    {
        "rank_metric": "duels_per_match",
        "rows": [
            ("ATA", "Atalanta", "Serie A", "108"),
            ("ATH", "Athletic Club", "La Liga", "105"),
            ("BRE", "Brentford", "Premier League", "103"),
            ("BMG", "Borussia Mönchengladbach", "Bundesliga", "101"),
            ("RCL", "Lens", "Ligue 1", "99"),
            ("SCP", "Sporting CP", "Liga Portugal", "97"),
            ("FEY", "Feyenoord", "Eredivisie", "96"),
        ],
    },
]

# --------------------------------------------------------------------- build

E = html.escape

# The crest slot, TEAMS ONLY. Production renders the club crest IMAGE.
# ⚠ The mock draws a neutral placeholder instead of the design system's text-initials
# fallback: the mock must not hotlink (#36), and initials read as if the abbreviation were
# the design. Inline SVG -- no external fetch.
CREST = (
    '<svg viewBox="0 0 24 24" aria-hidden="true" focusable="false">'
    '<path d="M12 3.2l6.6 2.35v5.65c0 3.95-2.73 7.15-6.6 8.95'
    '-3.87-1.8-6.6-5-6.6-8.95V5.55L12 3.2z"'
    ' fill="none" stroke="currentColor" stroke-width="1.6" opacity=".42"/></svg>'
)


RATE_WINDOW = {"_per_match": {"en": " per match", "fi": " per ottelu"},
        "_per90": {"en": " per 90", "fi": " per 90"}}


def board_title(metric_id, lab, loc="en"):
    """A board name SPELLS OUT the format sigil instead of carrying it.

    "Ø Goals" reads badly as a heading, but plain "Goals" is WRONG -- these are per-match
    rates, and a bare noun reads as a season total. So the sigil is expanded into the words
    it stands for: "Ø Goals" -> "Goals per match". The column header underneath keeps the
    compact "Ø Goals", where a sigil is fine and space is short.

    Driven by the metric ID, not by the sigil, because "Ø" alone is ambiguous -- the
    catalogue also carries per-90 labels ("Ø Successful dribbles per 90"), and appending
    "per match" to one of those would produce nonsense. The suffix therefore comes from the
    id, and the two are asserted to agree so a future metric cannot drift past this.

    With ONE metric per board there is no column header, so this title is the ONLY label the
    number carries -- which is exactly why it has to say "per match" rather than "Goals".
    """
    suffix = next((v for k, v in RATE_WINDOW.items() if metric_id.endswith(k)), None)
    if lab.startswith("Ø "):
        assert suffix, "%r is labelled Ø but its id names no rate window" % metric_id
        stem = lab[len("Ø "):]
        # a per-90 label already ends in its own window; do not double it
        return stem if stem.endswith(suffix[loc].strip()) else stem + suffix[loc]
    assert not suffix, "%r is a rate by id but its label %r carries no Ø" % (metric_id, lab)
    return lab


def direction(metric_id, entity="team"):
    """The metric's own direction, from the catalogue."""
    return _BY_KEY[(metric_id, entity)]["direction"]


def check_order(board):
    """EVERY board ranks DESCENDING -- most first, without exception.

    The two "against" boards were dropped in the same session, so no `lower_better` metric
    is left and descending now AGREES with every board's catalogue `direction`. The assert
    below checks both, so if a lower-is-better metric is ever added back the disagreement
    surfaces instead of quietly ranking the worst teams first.
    """
    rank_id = board["rank_metric"]
    vals = [float(r[3]) for r in board["rows"]]
    assert vals == sorted(vals, reverse=True), (
        "%s must run high->low; got %s" % (rank_id, vals))
    assert direction(rank_id) == "higher_better", (
        "%s is %s -- ranking it descending puts the WORST teams first. Either drop the board "
        "or get that ruled explicitly." % (rank_id, direction(rank_id)))
    return direction(rank_id)


def board_html(board):
    rank_id = board["rank_metric"]
    title_en = board_title(rank_id, label(rank_id), "en")
    fi_raw, _ = FI[rank_id]
    title_fi = board_title(rank_id, fi_raw, "fi")
    # ⚠ the FI title is ALWAYS a probe: even where the label exists, "per ottelu" is not
    # approved copy -- it is a plausible rendering for measuring width.

    parts = ['<div class="board">']
    parts.append(
        '<div class="bhd"><span class="bt">'
        '<span class="en">%s</span>'
        '<span class="fi probe" lang="fi">%s</span>'
        "</span></div>" % (E(title_en), E(title_fi))
    )
    # ONE metric per board, so there is NO column-header row: the title is
    # the only label the number needs, and a header would only repeat it.
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
.bnote { font-size: 11px; color: var(--muted); margin: 8px 0 0; font-style: italic; opacity: .8; }

/* ================================================================ *
 *  TOP TEAMS BLOCK -- the actual proposal.                          *
 * ================================================================ */

/* Each board is its OWN container, so every measurement below resolves against the
   board's width and not the page's. Sizing to the page is what broke when the content
   column was capped narrower than the viewport (trap 3). */
.board { margin-top: 26px; container-type: inline-size; }
.board:first-of-type { margin-top: 10px; }

/* Board head mirrors .fxgroup > .gh, which Next matches already uses on this page, so the
   two blocks read as siblings instead of introducing a per-page treatment. */
.bhd { padding-bottom: 7px; border-bottom: 1px solid var(--div); }
.bt { font-size: 14px; font-weight: 700; color: var(--ink); }

/* ONE metric per board -> ONE value column and no header row.
   The track list is still written out WHOLE and read with a single var() as the ENTIRE
   value: `repeat(var(--n), ...)` is invalid CSS, because the repeat count must be a
   literal integer and a custom property there silently invalidates the whole
   grid-template-columns declaration (trap 1).
   The value column stays a FIXED width, never auto (trap 2). With one column the trap is
   milder but not gone: auto would let a 3-digit value ("682") size its track differently
   from a 2-digit one, so the numbers would stop aligning down the board. */
.bgrid { --vw: 64px; --gap: 12px; --cols: 18px 24px minmax(0, 1fr) var(--vw); }
@container (max-width: 430px) { .bgrid { --vw: 56px; --gap: 10px; } }

.brow {
  display: grid; grid-template-columns: var(--cols);
  align-items: center; gap: var(--gap);
  padding: 10px 0; border-bottom: 1px solid var(--line);
}
.brow:last-child { border-bottom: 0; }
a.brow:hover .nm { text-decoration: underline; text-underline-offset: 2px; }

.brow .rk { font-size: 12px; font-weight: 700; color: var(--muted); text-align: right; }
/* ONE LINE IF IT FITS, STACKED IF NOT -- decided PER BOARD, never per row
   ("they all stack together or not").
   flex-wrap decided it per row, so one board rendered rows 1/5/6 inline and 2/3/4/7
   stacked: right for each row, ragged as a block. CSS cannot ask whether a SIBLING
   wrapped, so the trigger has to be something every row shares -- the board's own width.
   `.board` already declares container-type, so a container query drives all its rows at
   once. `nowrap` is what enforces it: without it one over-long row could still wrap alone
   and bring the raggedness back. */
.brow .ent { min-width: 0; display: flex; flex-wrap: nowrap; align-items: baseline; column-gap: 8px; }
@container (max-width: 480px) {
  /* Every row in this board stacks, together.
     ⚠ Blockify the CHILDREN, not just the container: .nm/.sub carry no `display` of their
     own (flex blockifies them in the branch above), so setting only `.ent { display: block }`
     leaves two INLINE spans that run together -- "Bayern MünchenBundesliga". */
  .brow .ent { display: block; }
  .board .nm,
  .board .sub { display: block; }
  .board .sub { margin-top: 1px; }
}
/* THE NAME MUST NEVER TRUNCATE. system.css ellipsises .nm, which is right on a fixture card
   and wrong here: a clipped name defeats a block whose whole purpose is to send people to the
   entity's page. The name wraps and the row grows.
   `min-width: 0` matters here: a flex item refuses to shrink below its min-content width by
   default, so without it a long name would push the row wide instead of wrapping inside. */
.board .nm {
  min-width: 0; font-size: 14px; font-weight: 600; color: var(--ink);
  white-space: normal; overflow: visible; text-overflow: clip; overflow-wrap: break-word;
  line-height: 1.25;
}
.board .sub { min-width: 0; font-size: 11.5px; color: var(--muted); overflow-wrap: break-word; }
/* Right-aligned, matching `.pstat` in system.css. Centring was for the header/number pairing
   that no longer exists; with a lone value, right alignment is what the system already does. */
.brow .v { font-size: 15px; color: var(--muted); text-align: right; font-variant-numeric: tabular-nums; }
.brow .v b { color: var(--ink); font-weight: 700; }

.tt-intro { font-size: 13px; color: var(--ink-2); line-height: 1.6; margin: 0 0 4px; }
.tt-intro b { color: var(--ink); font-weight: 600; }
"""


def build():
    system_css = SYSTEM_CSS.read_text(encoding="utf-8")
    boards = "\n".join(board_html(b) for b in BOARDS)

    return """<!doctype html>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Top teams -- home page block (mock)</title>
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
        <div class="sechead"><span class="eyebrow">Top teams</span></div>
        <p class="tt-intro">Season to date. Ranked across pooled leagues:
          <b>Premier League, La Liga, Bundesliga, Serie A, Ligue 1, Liga Portugal,
          Eredivisie</b>.</p>
%s
      </section>

    </div>
  </div>
</div>

<div class="legend">
  <b>Mock.</b> Numbers are placeholder, not measured &mdash; leagues are deliberately at
  different matchday counts so the points denominators differ, which a pooled board really does.
  Every board name and column header is <b>label_en</b> from
  <b>metric_catalogue.csv</b>, looked up by (metric_id, entity=team); the generator exits on an
  unknown id. Finnish comes from <b>METRIC_LABELS_FI</b> in strings.ts except the
  <span class="probe" style="text-decoration: underline dotted">dotted</span> ones, which do not
  exist yet and are plausible worst-case strings for measuring width, not approved copy.
  League names are left in English &mdash; the probe is about metric labels.
</div>
""" % (system_css, MOCK_CSS, boards)


def check_orders():
    for b in BOARDS:
        d = check_order(b)
        flag = "   <-- DESC AGAINST CATALOGUE DIRECTION" if d == "lower_better" else ""
        print("  %-32s desc | catalogue: %s%s" % (b["rank_metric"], d, flag))


def check_guards():
    """Prove the two failure paths are real rather than decorative.

    Run in-process. An earlier version shelled out to a script that imported this
    module, which -- with no __main__ guard -- re-ran the whole file on import and
    spawned itself again.
    """
    for bad in ("goals_per_matchx", "scorer_points"):
        # scorer_points is a REAL id, but a player-only one: asking for it as a team
        # metric must fail too, or the (metric_id, entity) grain is not being honoured.
        try:
            label(bad)
        except SystemExit as exc:
            print("  unknown-id guard fired for %-18s -> %s" % (bad, str(exc).splitlines()[0]))
        else:
            sys.exit("FATAL: the unknown-id guard did NOT fire for '%s'." % bad)

    # ...and a known id still resolves, so the guard is not just failing everything.
    assert label("goals_per_match") == "Ø Goals", label("goals_per_match")
    print("  known id still resolves -> %s" % label("goals_per_match"))


if __name__ == "__main__":
    check_guards()
    check_orders()
    OUT.write_text(build(), encoding="utf-8")
    print("wrote", OUT, OUT.stat().st_size, "bytes")
