"""Render the INTERACTION STANDARD — what is clickable, where the click boundary is, how it
signals. Every example below is live: hover them, tab through them, tap them.

Built from the same `interaction.py` the four page mocks import, so this page cannot describe
one thing while the pages do another.
"""
import html
from pathlib import Path

from interaction import INTERACTION_CSS
from rows import ROW_CSS, date_head, group_head, result_row, upcoming_row

REPO = Path(__file__).resolve().parent.parent
SYSTEM_CSS = REPO / "site_v2/src/styles/system.css"
OUT = Path(__file__).with_name("interaction_standard.html")

E = html.escape

PRINCIPLES = [
    ("Clickability is visible at rest. Hover only confirms it.",
     "An affordance that exists only on hover does not exist on a phone &mdash; and that is most "
     "readers. Underline-on-hover failed this twice: you could not discover the link without a "
     "mouse, and when you did it pointed at a word rather than the row."),
    ("The thing that responds is the thing you click.",
     "A row target makes the ROW respond. A chip target makes the CHIP respond. Never the text "
     "inside something larger &mdash; the match row is the link, and it has two club names in it."),
]

STATES = [
    ("Row", "list structure and separators", "background lift", "deeper lift", "outline"),
    ("Chip / button", "its own border", "border + text colour", "fill", "outline"),
    ("Heading link", "a chevron, always present", "chevron slides + brightens", "&mdash;", "outline"),
    ("Prose link", "a real underline, always present", "underline brightens", "&mdash;", "outline"),
]

RULES = [
    "<b>Never nest a link inside a link.</b> A row that is a link may not contain a team link &mdash; "
    "browsers do not parse it reliably and the reader cannot tell which target they hit.",
    "<b>One element, one destination.</b> If a row leads to the fixture, nothing inside it leads "
    "anywhere else. That ambiguity is exactly what the old underline created.",
    "<b>Green is not available.</b> <code>--accent</code> is reserved for &ldquo;better value&rdquo; "
    "and <code>--loss</code> for a Loss pill. Every state moves along the neutral ramp, which is "
    "also why it needs no separate rules for light and dark.",
    "<b>Keyboard focus is a separate signal</b> and survives every choice above. A decision that "
    "changes <code>:hover</code> must never remove the focus outline.",
    "<b>Hover is gated behind <code>@media (hover: hover)</code>.</b> On a touch device "
    "<code>:hover</code> can stick after a tap and leave a row looking permanently selected; "
    "<code>:active</code> is the touch feedback instead.",
]

PAGE_CSS = """
body { margin: 0; background: #0d0f13; }
.wrap { max-width: 760px; margin: 0 auto; padding: 28px clamp(16px,4vw,26px) 70px; }
h1 { font-size: 25px; margin: 0 0 6px; }
h2 { font-size: 16px; margin: 40px 0 12px; padding-bottom: 8px; border-bottom: 1px solid var(--div); }
.sub { font-size: 13.5px; color: var(--ink-2); line-height: 1.7; margin: 0 0 10px; }
.sub b { color: var(--ink); font-weight: 600; }
.pr { margin-top: 14px; padding-left: 15px; border-left: 3px solid var(--accent); }
.pr .t { font-size: 15px; font-weight: 700; color: var(--ink); }
.pr .b { font-size: 13px; color: var(--ink-2); line-height: 1.65; margin-top: 4px; }
.demo { margin-top: 14px; padding: 4px 18px 14px; background: var(--surface);
        border: 1px solid var(--line); border-radius: 12px; }
.demo.onpage { background: var(--page); }
.dl { font: 700 10.5px/1 ui-monospace, monospace; letter-spacing: .09em; text-transform: uppercase;
      color: var(--muted); padding: 16px 0 9px; }
table { width: 100%; border-collapse: collapse; margin-top: 10px; }
th { text-align: left; font-size: 10.5px; letter-spacing: .07em; text-transform: uppercase;
     color: var(--muted); padding: 0 10px 8px 0; border-bottom: 1px solid var(--div); }
td { font-size: 13px; color: var(--ink-2); padding: 10px 10px 10px 0;
     border-bottom: 1px solid var(--line); vertical-align: top; }
td.k { color: var(--ink); font-weight: 600; white-space: nowrap; }
ol.rules { margin: 10px 0 0; padding-left: 20px; }
ol.rules li { font-size: 13.5px; color: var(--ink-2); line-height: 1.7; padding: 5px 0; }
.try { font-size: 12px; color: var(--muted); font-style: italic; margin: 10px 0 0; }
.crest.xs svg { width: 15px; height: 15px; display: block; color: var(--muted); }
.clogo svg { color: var(--muted); }
"""


def build():
    rows = (date_head("Sat 1 March")
            + upcoming_row("club", "Borussia Mönchengladbach", "SC Freiburg", "15:30", "CET")
            + upcoming_row("club", "Union Berlin", "Bayer 04 Leverkusen", "15:30", "CET"))
    played = (date_head("Sat 22 February")
              + result_row("club", "Bayern München", 4, "SC Freiburg", 1))
    chips = "".join('<a class="linkchip" href="#">%s</a>' % c
                    for c in ("Premier League", "La Liga", "Bundesliga", "Serie A"))

    return """<!doctype html>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Interaction standard</title>
<style>
%s
%s
%s
%s
</style>
<div class="wrap fx">

  <h1>Interaction standard</h1>
  <p class="sub">What is clickable, where the click boundary is, and how it says so. Everything
     below is <b>live</b> &mdash; hover it, tab through it, tap it.</p>

  <h2>Two principles</h2>
%s

  <h2>The four target types</h2>

  <div class="demo onpage">
    <div class="dl">1 &middot; Row target &mdash; the whole row is the link</div>
    <div class="fxgroup">%s%s</div>
    <p class="try">Hover a row: the row lifts, nothing underlines. The two club names are not
       separate targets &mdash; the row is one destination.</p>
  </div>

  <div class="demo onpage">
    <div class="dl">2 &middot; Heading link &mdash; a chevron, at rest</div>
    <div class="fxgroup">%s%s</div>
    <p class="try">The chevron is there before you touch anything. That is what tells a phone
       reader it leads somewhere; hover only slides it.</p>
  </div>

  <div class="demo onpage">
    <div class="dl">3 &middot; Chip target</div>
    <div class="linkrow">%s</div>
    <p class="try">The border is the affordance at rest. Hover raises it, tap fills it.</p>
  </div>

  <div class="demo onpage">
    <div class="dl">4 &middot; Prose link &mdash; the one place an underline stays</div>
    <p class="sub" style="margin:8px 0 0">Bayern München lead after 24 matches, 7 points clear of
       <a href="#">Bayer 04 Leverkusen</a>. In running text there is no structure to signal with,
       so colour alone is not an accessible signal.</p>
  </div>

  <h2>Every state, in one table</h2>
  <table>
    <tr><th>Target</th><th>At rest</th><th>Hover</th><th>Active / touch</th><th>Focus</th></tr>
%s
  </table>

  <h2>Rules that are not about looks</h2>
  <ol class="rules">%s</ol>

  <h2>What this replaces</h2>
  <p class="sub">Nine clickable element types across four surfaces carried <b>six</b> different
     hover treatments, and the row target underlined a club name inside itself. All of it now
     comes from one module (<code>interaction.py</code>) that every surface imports, so a page
     cannot invent its own.</p>
</div>
""" % (SYSTEM_CSS.read_text(encoding="utf-8"), ROW_CSS, INTERACTION_CSS, PAGE_CSS,
       "\n".join('<div class="pr"><div class="t">%s</div><div class="b">%s</div></div>' % (t, b)
                 for t, b in PRINCIPLES),
       group_head("bundesliga", "Bundesliga"), rows,
       group_head("premier-league", "Premier League"), played,
       chips,
       "\n".join("<tr><td class=\"k\">%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>"
                 % s for s in STATES),
       "".join("<li>%s</li>" % r for r in RULES))


if __name__ == "__main__":
    OUT.write_text(build(), encoding="utf-8")
    print("  wrote %s (%.0f KB)" % (OUT.name, OUT.stat().st_size / 1024))
