"""Render the Top players home-page block as a standalone HTML mock.

Same treatment as Top teams: ONE metric per board, top 7, all ranked descending, no
column-header row. Forked from gen_top_teams.py so the two blocks cannot drift apart.

One thing differs from teams, and it comes from the catalogue rather than from choice:
player board metrics are season TOTALS (`format: integer`), not per-match rates, so no
label carries the "Ø" sigil, the per-match expansion never fires, and the board title is
the `label_en` verbatim.

Every board is `higher_better` ranked descending, so no board disagrees with its metric's
`direction`. The keeper board (`shots_on_goal_against`, lower_better, ranked most-first)
was the one exception in either block, and it was dropped on 2026-08-10. The guard that
demanded an explicit ruling for such a board is KEPT, so reintroducing one cannot pass
silently.

Design-only. Reads nothing from BigQuery; the numbers are PLACEHOLDER.

Two things are read from the repo so the mock cannot drift from the product:
  1. every display name comes from `label_en` in dbt_project/seeds/metric_catalogue.csv,
     looked up by (metric_id, entity) -- the catalogue's real grain. Two of the ids used
     here carry BOTH a team and a player row, so keying on metric_id alone silently takes
     the wrong label; that is the exact bug !27 fixed in export_metric_definitions_json.py.
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
OUT = Path(__file__).with_name("top_players_mock.html")

# ---------------------------------------------------------------- catalogue

_ROWS = list(csv.DictReader(CATALOGUE.open(encoding="utf-8")))
_BY_KEY = {(r["metric_id"], r["entity"]): r for r in _ROWS}


def label(metric_id, entity="player"):
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
# These four Finnish labels SHIPPED and are the CPO's; they live in METRIC_LABELS_FI in
# site_v2/src/i18n/strings.ts under the `playerMetrics.*` keys.
# ⚠ The second element says "this is a width probe, not approved copy" and is now False for all
# four — but the renderer discards it (`fi_raw, _ = FI[rank_id]`) and hardcodes `class="fi probe"`,
# so the mock still dots them as unapproved. Left as-is deliberately: changing it would alter the
# artifact the CPO reviewed, which is a design change and not this task's job.
FI = {
    "goals_player": ("Maalit", False),
    "assists_player": ("Maalisyötöt", False),
    "passes_player": ("Syötöt", False),
    "passes_key_player": ("Avainsyötöt", False),
}

# --------------------------------------------------------------- sample data
#
# ⚠ PLACEHOLDER. The player names are real people; the numbers attached to them are
# INVENTED and were never measured. This is a layout mock, not a data preview -- the
# legend at the foot of the page says so, and it must keep saying so.

"""
FOUR boards, the CPO's set of 2026-08-10, in his order, ALL ranked descending:

    goals -> assists -> passes -> key passes

Against #40's five two-column boards:

  * ⚠ `scorer_points` is GONE. Goals and assists are boards in their own right now, so the
    combined metric has nothing left to combine. That retires #40's "the rank metric is the
    SUM of the columns, so do not display it" rule -- Goal contributions was the only board
    it ever applied to, in either block.
  * every second column goes: `pass_accuracy_pct`, `dribbles_success_pct`, `duels_won_pct`,
    `save_pct`.
  * ⚠ `pass_accuracy_pct` leaving does NOT fix the pass-accuracy defect. That number is
    still rendered on the stats pages; it is re-filed as its own GitLab issue.
  * ⚠ THERE IS NO GOALKEEPER BOARD any more. Dribbles, duels, shots on target and shots on
    target faced were all dropped on 2026-08-10, and the last of those was the keeper's
    only representation on the home page. The four survivors are all attacking/possession
    metrics, so an outfield creator can top every board and a keeper can top none.

⚠ Every row shows CLUB AND LEAGUE (#40): a pooled board ranks across seven leagues, so the
club alone no longer implies the competition.
"""
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

# The crest slot. Production renders the club crest IMAGE -- the TEAM logo, on player rows
# as well as team rows (CPO 2026-08-10).
# ⚠ The mock draws a neutral placeholder rather than the design system's text-initials
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
    """A board name SPELLS OUT the format sigil instead of carrying it (CPO 2026-08-10).

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


def direction(metric_id, entity="player"):
    """The metric's own direction, from the catalogue."""
    return _BY_KEY[(metric_id, entity)]["direction"]


def check_order(board):
    """EVERY board ranks DESCENDING -- most first (CPO 2026-08-10), without exception.

    The two "against" boards were dropped in the same session, so no `lower_better` metric
    is left and descending now AGREES with every board's catalogue `direction`. The assert
    below checks both, so if a lower-is-better metric is ever added back the disagreement
    surfaces instead of quietly ranking the worst teams first.
    """
    rank_id = board["rank_metric"]
    vals = [float(r[3]) for r in board["rows"]]
    assert vals == sorted(vals, reverse=True), (
        "%s must run high->low; got %s" % (rank_id, vals))
    if direction(rank_id) != "higher_better":
        # A lower-is-better metric ranked descending puts the WORST first, so it needs an
        # explicit ruling recorded ON the board -- never a silent pass.
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
    # ⚠ the FI title is ALWAYS a probe: even where the label exists, "per ottelu" is not
    # approved copy -- it is a plausible rendering for measuring width.

    parts = ['<div class="board">']
    parts.append(
        '<div class="bhd"><span class="bt">'
        '<span class="en">%s</span>'
        '<span class="fi probe" lang="fi">%s</span>'
        "</span></div>" % (E(title_en), E(title_fi))
    )
    # ONE metric per board (CPO 2026-08-10), so there is NO column-header row: the title is
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

/* ONE metric per board (CPO 2026-08-10) -> ONE value column and no header row.
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
   (CPO 2026-08-10: "they all stack together or not").
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
  Each board name is <b>label_en</b> from <b>metric_catalogue.csv</b>, looked up by
  (metric_id, entity=player); the generator exits on an unknown id, and it checks each board's
  sort against that metric's <b>direction</b>.
  ⚠ <b>Every Finnish string here is a probe</b> (dotted): METRIC_LABELS_FI currently holds only
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
    """Prove the two failure paths are real rather than decorative.

    Run in-process. An earlier version shelled out to a script that imported this
    module, which -- with no __main__ guard -- re-ran the whole file on import and
    spawned itself again.
    """
    for bad in ("goals_per_matchx", "points_capture"):
        # points_capture is a REAL id, but a TEAM-only one: asking for it as a player
        # metric must fail too, or the (metric_id, entity) grain is not being honoured.
        try:
            label(bad)
        except SystemExit as exc:
            print("  unknown-id guard fired for %-18s -> %s" % (bad, str(exc).splitlines()[0]))
        else:
            sys.exit("FATAL: the unknown-id guard did NOT fire for '%s'." % bad)

    # ...and a known id still resolves, so the guard is not just failing everything.
    assert label("goals_player") == "Goals", label("goals_player")
    print("  known id still resolves -> %s" % label("goals_player"))


if __name__ == "__main__":
    check_guards()
    check_orders()
    OUT.write_text(build(), encoding="utf-8")
    print("wrote", OUT, OUT.stat().st_size, "bytes")
