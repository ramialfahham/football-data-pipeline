"""The competition TAXONOMY as it exists in the data, and what each level produces as a page
grouping. A decision aid, not a page.

The question that reshaped this page: *"but we have a taxonomy of competitions, why don't use
it here?"* — correct.
The competitions page was grouped by `display_group`, which is the COARSEST of three levels and a
deliberate rollup. Nothing was invented, but the richest thing in the data was not used either.

THREE LEVELS, all in `dbt_project/seeds/competition_types.csv` keyed by the registry's
`competition_type`:

    competition_type   12 values   the taxonomy itself       (domestic_league, continental_club, …)
    entity_type         2 values   who competes              (club | national)
    display_group       4 values   the browse rollup         (leagues | cups | continental-club | national-teams)

⚠ Only `display_group` has i18n labels today (`groupLeagues`, `groupCups`,
`groupContinentalClub`, `groupNationalTeams`). Using a finer level means new keys — which is a
cost, not a blocker, and the English below is a PROPOSAL, not approved copy.
"""
import html
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parent.parent
SYSTEM_CSS = REPO / "site_v2/src/styles/system.css"
TYPES_SEED = REPO / "dbt_project/seeds/competition_types.csv"
OUT = Path(__file__).with_name("taxonomy_options.html")

E = html.escape

REG = [c for c in yaml.safe_load(
    (REPO / "docs/competition_registry.yml").read_text(encoding="utf-8"))["competitions"]
    if isinstance(c, dict) and "competition_type" in c]

_rows = TYPES_SEED.read_text(encoding="utf-8").strip().splitlines()
_h = _rows[0].split(",")
SEED = {r.split(",")[_h.index("competition_type")]: {
            "entity_type": r.split(",")[_h.index("entity_type")],
            "display_group": r.split(",")[_h.index("display_group")]}
        for r in _rows[1:] if r.strip()}

# ⚠ PROPOSED English for the finer levels. `display_group`'s four already exist in strings.ts;
# these do not, and inventing them is exactly the cost of using a finer level.
TYPE_LABEL = {
    "domestic_league": "Domestic leagues", "domestic_cup": "Domestic cups",
    "domestic_super_cup": "Domestic super cups", "club_qualifying": "Continental qualifying",
    "continental_club": "Continental club", "continental_super_cup": "Continental super cup",
    "qualifying": "Qualifiers", "continental_championship": "Continental championships",
    "world_championship": "World Cup",
}
ENTITY_LABEL = {"club": "Club competitions", "national": "National teams"}
GROUP_LABEL = {"leagues": "Leagues", "cups": "Cups",
               "continental-club": "European club", "national-teams": "National teams"}


def browsable():
    return [c for c in REG if SEED[c["competition_type"]]["display_group"]]


def by(keyfn, labelfn):
    out = {}
    for c in browsable():
        out.setdefault(keyfn(c), []).append(c)
    for v in out.values():
        v.sort(key=lambda c: (c.get("sort_order") or 0, c["league_code"]))
    ordered = sorted(out.items(), key=lambda kv: kv[1][0].get("sort_order") or 0)
    return [(labelfn(k), v) for k, v in ordered]


OPTIONS = [
    ("A", "display_group", "What the page does today, and what the shipped browse block uses.",
     "The only level with labels in all three locales. But it is a ROLLUP: World Cup, Euros, "
     "Nations League and qualifiers all land in one bucket, and the Champions League shares a "
     "bucket with the Club World Cup.",
     by(lambda c: SEED[c["competition_type"]]["display_group"],
        lambda k: GROUP_LABEL[k])),
    ("B", "entity_type &rarr; display_group",
     "Club competitions and national-team competitions split first.",
     "The split readers actually feel — clubs versus countries. ⚠ But the national side collapses "
     "to a single child group, so the second level does no work there.",
     None),
    ("C", "competition_type", "The taxonomy itself, unrolled.",
     "Separates World Cup from continental championships from qualifiers, and continental club "
     "from continental super cup. ⚠ Needs new i18n keys, and two groups have a single member.",
     by(lambda c: c["competition_type"], lambda k: TYPE_LABEL.get(k, k))),
]


def two_level():
    out = []
    for ent in ("club", "national"):
        members = [c for c in browsable() if SEED[c["competition_type"]]["entity_type"] == ent]
        sub = {}
        for c in members:
            sub.setdefault(SEED[c["competition_type"]]["display_group"], []).append(c)
        out.append((ENTITY_LABEL[ent], sorted(sub.items(),
                                              key=lambda kv: kv[1][0].get("sort_order") or 0)))
    return out


PAGE_CSS = """
body { margin: 0; background: #0d0f13; }
.wrap { max-width: 900px; margin: 0 auto; padding: 26px clamp(16px,4vw,26px) 60px; }
h1 { font-size: 23px; margin: 0 0 6px; }
.sub { font-size: 13.5px; color: var(--ink-2); line-height: 1.7; margin: 0 0 8px; }
.sub b { color: var(--ink); font-weight: 600; }
.lv { margin-top: 14px; border-left: 3px solid var(--div); padding-left: 14px; font-size: 13px;
      color: var(--ink-2); line-height: 1.7; }
.lv code { color: var(--ink); }
.opt { margin-top: 30px; border: 1px solid var(--line); border-radius: 12px; overflow: hidden; }
.opt.rec { border-color: var(--accent); }
.oh { background: var(--sunk); padding: 12px 16px; }
.oh .k { font: 700 12px/1 ui-monospace, monospace; color: var(--accent); letter-spacing: .1em; }
.oh .t { font-size: 16px; font-weight: 700; color: var(--ink); margin-top: 6px; }
.oh .d { font-size: 12.5px; color: var(--muted); margin-top: 4px; line-height: 1.6; }
.ob { padding: 6px 16px 16px; }
.note { font-size: 12.5px; color: var(--ink-2); line-height: 1.65; margin: 10px 0 0;
        padding-top: 10px; border-top: 1px solid var(--line); }
.grp { display: flex; align-items: baseline; gap: 10px; padding: 9px 0;
       border-bottom: 1px solid var(--line); }
.grp:last-child { border-bottom: 0; }
.grp .g { font-size: 14px; font-weight: 700; color: var(--ink); min-width: 210px; }
.grp .n { font-size: 12px; color: var(--muted); font-variant-numeric: tabular-nums; min-width: 34px; }
.grp .ex { font-size: 12px; color: var(--muted); min-width: 0; }
.sub2 { padding-left: 20px; }
.ent { font-size: 13px; font-weight: 700; color: var(--accent); letter-spacing: .06em;
       text-transform: uppercase; padding: 14px 0 4px; }
.one { color: var(--loss); }
"""


def grp_rows(groups, cls=""):
    out = []
    for label, members in groups:
        ex = ", ".join(
            (c.get("name") or c["league_code"]) for c in members[:2])
        out.append('<div class="grp %s"><span class="g">%s</span>'
                   '<span class="n%s">%d</span><span class="ex">%s</span></div>'
                   % (cls, E(label), " one" if len(members) == 1 else "", len(members), E(ex)))
    return "".join(out)


def build():
    blocks = []
    for key, title, desc, note, groups in OPTIONS:
        if key == "B":
            body = "".join('<div class="ent">%s</div><div class="sub2">%s</div>'
                           % (E(ent), grp_rows([(GROUP_LABEL[g], m) for g, m in subs]))
                           for ent, subs in two_level())
        else:
            body = grp_rows(groups)
        blocks.append(
            '<div class="opt%s"><div class="oh"><div class="k">OPTION %s</div>'
            '<div class="t">%s</div><div class="d">%s</div></div>'
            '<div class="ob">%s<p class="note">%s</p></div></div>'
            % (" rec" if key == "C" else "", key, title, desc, body, note))

    return """<!doctype html>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Competition taxonomy — grouping options</title>
<style>
%s
%s
</style>
<div class="wrap fx">
  <h1>How should the competitions page group?</h1>
  <p class="sub">The taxonomy exists in the data at <b>three</b> levels. The page currently uses
     the coarsest. Counts are the real registry &mdash; 45 competitions.</p>

  <div class="lv">
    <code>competition_type</code> &mdash; 12 values, the taxonomy itself<br>
    <code>entity_type</code> &mdash; 2 values, who competes: club or national<br>
    <code>display_group</code> &mdash; 4 values, a rollup of the above for browsing
  </div>
  <p class="sub" style="margin-top:12px">All three come from
     <code>dbt_project/seeds/competition_types.csv</code>, keyed by each competition's
     <code>competition_type</code> in the registry. ⚠ Only <b>display_group</b> has i18n labels
     today; the names in options B and C are <b>proposals</b>, not approved copy. A red count
     marks a group with a single member.</p>

%s

  <p class="sub" style="margin-top:30px"><b>My recommendation: C.</b> It is the taxonomy rather
     than a summary of it, it separates the World Cup from continental championships from
     qualifiers &mdash; which readers do treat as different things &mdash; and it dissolves the
     &ldquo;European club&rdquo; bucket that is wrong for five of its nine members (#56). The cost
     is new i18n keys in three locales, and two single-member groups that will grow.</p>
</div>
""" % (SYSTEM_CSS.read_text(encoding="utf-8"), PAGE_CSS, "\n".join(blocks))


if __name__ == "__main__":
    for key, _t, _d, _n, groups in OPTIONS:
        if groups:
            print("  option %s: %d groups -- %s" % (key, len(groups),
                                                    ", ".join("%s(%d)" % (g, len(m))
                                                              for g, m in groups)))
    OUT.write_text(build(), encoding="utf-8")
    print("  wrote %s" % OUT.name)
