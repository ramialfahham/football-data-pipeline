"""Mock of the competitions index page, /{locale}/competitions/, listing every competition."""
import csv
import html
import re
import sys
from pathlib import Path

import yaml

from gen_block_standard import ACTIVE, short
from interaction import CHEVRON
from rows import LEAGUE_LOGO

REPO = Path(__file__).resolve().parent.parent
REGISTRY = REPO / "docs/competition_registry.yml"
SYSTEM_CSS = REPO / "site_v2/src/styles/system.css"
OUT = Path(__file__).with_name("competitions_mock.html")

E = html.escape

# =============================================================== THE TAXONOMY SEED
# Labels are read from the seed, never typed here; DE/FI live in `strings.ts` by label_i18n_key.
TYPES_SEED = REPO / "dbt_project/seeds/competition_types.csv"
TYPES_PROPOSED = Path(__file__).with_name("competition_types.proposed.csv")

# Region labels are their own table because the region varies within one competition_type.
CONFED_PROPOSED = Path(__file__).with_name("confederations.proposed.csv")

# --------------------------------------------------------------- what the proposal changes
# Every difference from the shipped seed is declared here; check_seed_matches_shipped() enforces it.
DROPPED_COLUMNS = {"display_group"}

RENAMED_TYPES = {"continental_club": "continental_cup", "world_championship": "world_cup"}

NEW_TYPES = {"club_world_cup", "intercontinental_cup"}

# Applied in memory; check_registry_still_unedited() fails once the registry holds the new value.
RETYPED = {"CWC": "club_world_cup"}


def _read_csv(path, key):
    with open(path, encoding="utf-8", newline="") as fh:
        return {r[key]: r for r in csv.DictReader(fh)}


_TYPES = _read_csv(TYPES_PROPOSED, "competition_type")
_CONFED = _read_csv(CONFED_PROPOSED, "confederation")

ENTITY_TYPE = {k: v["entity_type"] for k, v in _TYPES.items()}
SINGLE_COUNTRY = {k: v["single_country"] == "true" for k, v in _TYPES.items()}
TYPE_EN = {k: v["label_en"] for k, v in _TYPES.items()}
TYPE_KEY = {k: v["label_i18n_key"] for k, v in _TYPES.items()}
CONFED_EN = {k: v["label_en"] for k, v in _CONFED.items()}

# Every registry competition, with no status filter, matching what the export ships.
_REGISTRY_RAW = [c for c in yaml.safe_load(REGISTRY.read_text(encoding="utf-8"))["competitions"]
                 if isinstance(c, dict) and "competition_type" in c]


def _apply_proposal(c):
    ct = RETYPED.get(c["league_code"]) or RENAMED_TYPES.get(c["competition_type"],
                                                            c["competition_type"])
    return {**c, "competition_type": ct}


REGISTRY_ALL = [_apply_proposal(c) for c in _REGISTRY_RAW]

# Short names exist only for the active competitions; the rest fall back to the registry `name`.
SHORT_CODES = {c["league_code"] for c in ACTIVE}

# The H1 reuses the nav item's key so the menu item and its page share one string.
COPY = {
    "crumbHome": ("Home", "Etusivu"),
    "navCompetitions": ("Competitions", "Kilpailut"),
}


def loc(key):
    en, fi = COPY[key]
    return '<span class="en">%s</span><span class="fi" lang="fi">%s</span>' % (E(en), E(fi))


# ================================================================= PROVENANCE
# Element | Level | Source | status | Note; `status` drives both the on-page mark and check().
#   ok        - a real, shipped source
#   proposed  - a real source that does not exist yet, proposed by this design
#   gap       - NO source; the value on the page is a stand-in and is marked as one
MART = "mart_competition_index"

PROVENANCE = [
    ("Breadcrumb \u201cHome\u201d", "chrome", "strings.ts \u2192 crumbHome", "ok",
     "an i18n label, not content \u2014 exists in en/de/fi"),
    ("H1 \u201cCompetitions\u201d", "page", "strings.ts \u2192 navCompetitions", "ok",
     "reuses the NAV item's key \u2014 one string, so the menu and its page cannot drift"),
    ("Count line", "page", "derived: len(rows), len(groups)", "ok",
     "a count of what is rendered, not a stored number"),
    ("The SET of competitions", "page", "%s \u2014 one row each" % MART, "gap",
     "\u26a0 nothing DECIDES membership. The export applies no status filter and `status` is "
     "stale. The mart moves that question; it does not answer it"),
    ("Category heading", "group", "%s.category_label" % MART, "proposed",
     "upstream competition_types.csv \u2192 label_en (#57); DE/FI via category_i18n_key"),
    ("Which group a row is in", "group", "%s.competition_type" % MART, "proposed",
     "\u26a0 upstream needs two RENAMES and CWC re-typed (#57) \u2014 applied in memory here "
     "and guarded against the real registry"),
    ("Group ORDER", "group", "%s.entity_type, then min(sort_order)" % MART, "proposed",
     "club before national. \u26a0 `sort_order` is one of the registry fields that never reach "
     "the warehouse today \u2014 that is #62"),
    ("Competition logo", "row", "%s.logo_url" % MART, "gap",
     "upstream dim_league.league_logo_url. \u26a0 33 of 45 have none, and it is hot-linked from "
     "media.api-sports.io (#36). Rendered as a neutral mark"),
    ("Competition name", "row", "%s.competition_name" % MART, "gap",
     "upstream dim_league.league_name, corrections in base (#55, the #851 pattern). \u26a0 TWO "
     "sources today and the shipped one is STALE \u2014 the Conference League dropped "
     "\u201cEuropa\u201d in 2024 and the registry still carries it"),
    ("Sub-line \u2014 the region", "row", "%s.region_label" % MART, "proposed",
     "ONE column, resolved inside the mart: the country when single_country, else the "
     "confederation's label. The page never sees the branch"),
    ("\u2003\u21b3 how the mart resolves it", "row",
     "competition_types.single_country + confederations.label_en", "proposed",
     "\u26a0 one NEW COLUMN and one NEW SEED (#57). 15 of 45 rows change"),
    ("Row ORDER within a group", "row", "%s.sort_order" % MART, "proposed",
     "authored per category \u2014 PL, PD, BL1, SA, L1 \u2026 VL last"),
    ("Row link", "row", "%s.slug" % MART, "proposed",
     "never derived from the display name (site_architecture \u00a73)"),
    ("Filter \u2014 clubs / national", "page", "%s.entity_type" % MART, "proposed",
     "the same column the group order uses"),
    ("Filter \u2014 region", "page", "%s.confederation" % MART, "proposed",
     "\u26a0 the switch SET is read too \u2014 onboarding the first OFC competition adds an "
     "Oceania switch with no edit"),
    ("Chevron", "row", "\u2014 no data \u2014", "ok",
     "the interaction standard's at-rest affordance (#52), not a value"),
]


# ------------------------------------------------------------------- the guards
def check_seed_matches_shipped():
    """The proposal must differ from the shipped seed only in what is declared above."""
    shipped = _read_csv(TYPES_SEED, "competition_type")

    expected = {RENAMED_TYPES.get(ct, ct) for ct in shipped} | NEW_TYPES
    if set(_TYPES) != expected:
        raise SystemExit("FATAL: undeclared type change — extra %s / missing %s"
                         % (sorted(set(_TYPES) - expected), sorted(expected - set(_TYPES))))

    for ct, row in shipped.items():
        proposed = _TYPES[RENAMED_TYPES.get(ct, ct)]
        if row["entity_type"] != proposed["entity_type"]:
            raise SystemExit("FATAL: %s.entity_type differs — shipped %r, proposed %r"
                             % (ct, row["entity_type"], proposed["entity_type"]))

    shipped_cols = set(next(iter(shipped.values())))
    proposed_cols = set(next(iter(_TYPES.values())))
    still_there = DROPPED_COLUMNS & proposed_cols
    if still_there:
        raise SystemExit("FATAL: column(s) declared DELETED are still in the proposal: %s"
                         % sorted(still_there))
    if shipped_cols - proposed_cols != DROPPED_COLUMNS:
        raise SystemExit("FATAL: undeclared column drop(s): %s"
                         % sorted((shipped_cols - proposed_cols) - DROPPED_COLUMNS))
    print("  taxonomy seed == shipped %d types, minus column %s, %d renamed, %d added"
          % (len(shipped), sorted(DROPPED_COLUMNS), len(RENAMED_TYPES), len(NEW_TYPES)))


def check_registry_still_unedited():
    """The in-memory rename and re-type must still be needed in the registry."""
    raw = {c["league_code"]: c["competition_type"] for c in _REGISTRY_RAW}
    for old in RENAMED_TYPES:
        if old not in raw.values():
            raise SystemExit("FATAL: no registry row still uses %r — the rename has landed, so "
                             "drop it from RENAMED_TYPES" % old)
    for code, new in RETYPED.items():
        if raw.get(code) == new:
            raise SystemExit("FATAL: %s is already typed %r in the registry — drop it from RETYPED"
                             % (code, new))
    print("  registry unedited: %d rename(s) and %d re-type(s) applied in memory"
          % (len(RENAMED_TYPES), len(RETYPED)))


def check_confederation_enum():
    """The confederation seed's keys must be exactly the enum parsed from the registry header."""
    line = next((ln for ln in REGISTRY.read_text(encoding="utf-8").splitlines()
                 if re.match(r"^#\s*confederation\s*:", ln)), None)
    if line is None:
        raise SystemExit("FATAL: the registry no longer documents the confederation enum — "
                         "this guard reads it from there and has nothing to check against")
    documented = {re.sub(r"\(.*\)", "", p).strip() for p in line.split(":", 1)[1].split("|")}
    if documented != set(CONFED_EN):
        raise SystemExit("FATAL: confederations.csv does not match the registry's documented "
                         "enum: seed-only %s, registry-only %s"
                         % (sorted(set(CONFED_EN) - documented),
                            sorted(documented - set(CONFED_EN))))
    print("  confederation seed == the enum documented at competition_registry.yml (%d)"
          % len(documented))


def region(c):
    """The sub-line: the registry country when single_country, else the confederation's label."""
    if SINGLE_COUNTRY[c["competition_type"]]:
        return c.get("country") or ""
    return CONFED_EN[c["confederation"]]


def grouped(pool):
    """Competitions by `competition_type`; groups ordered club first, then by best sort_order."""
    by = {}
    for c in pool:
        by.setdefault(c["competition_type"], []).append(c)
    for members in by.values():
        members.sort(key=lambda c: (c.get("sort_order") or 0, c["league_code"]))

    def order(kv):
        ct, members = kv
        return (0 if ENTITY_TYPE[ct] == "club" else 1,
                min(c.get("sort_order") or 0 for c in members))

    return sorted(by.items(), key=order)


def comp_row(c):
    """One competition row; `e-*` is the seed's entity_type, `r-*` the lower-cased confederation."""
    code = c["league_code"]
    name = short(code) if code in SHORT_CODES else (c.get("name") or code)
    href = "/en/%s/" % E(c.get("slug") or code.lower())
    proposed_source = not SINGLE_COUNTRY[c["competition_type"]]

    return ('<a class="crow e-%s r-%s" href="%s">'
            '<span class="clogo is-gap">%s</span>'
            '<span class="cid"><span class="nm is-gap">%s</span>'
            '<span class="sub%s">%s</span></span>'
            '%s</a>' % (ENTITY_TYPE[c["competition_type"]], c["confederation"].lower(), href,
                        LEAGUE_LOGO, E(name),
                        " is-proposed" if proposed_source else "", E(region(c)), CHEVRON))


# ------------------------------------------------------------------- the filters
# Both axes are columns: entity_type from the taxonomy seed, confederation from the registry.
# Radio inputs are a limit of pure CSS, which cannot express multi-select without JS.
TYPE_FILTERS = [("all", "All"), ("club", "Clubs"), ("national", "National teams")]


def region_filters():
    used = {c["confederation"] for c in REGISTRY_ALL}
    return [("all", "All regions")] + [
        (k.lower(), CONFED_EN[k]) for k in sorted(used, key=lambda k: CONFED_EN[k])]


def filter_css():
    """Hide rows matching neither active filter, and hide a category left with no matching row."""
    out = ["\n/* ---- FILTERS — generated from the two axes, pure CSS ---- */"]
    for key, _label in TYPE_FILTERS[1:]:
        out.append("body:has(#ty-%s:checked) .crow:not(.e-%s) { display: none; }" % (key, key))
    for key, _label in region_filters()[1:]:
        out.append("body:has(#rg-%s:checked) .crow:not(.r-%s) { display: none; }" % (key, key))
    # a group can hold club rows and UEFA rows and still hold no row that is both
    for tk, _t in TYPE_FILTERS:
        for rk, _r in region_filters():
            sel = ("" if tk == "all" else ".e-%s" % tk) + ("" if rk == "all" else ".r-%s" % rk)
            if not sel:
                continue
            out.append("body:has(#ty-%s:checked):has(#rg-%s:checked) "
                       ".cgroup:not(:has(.crow%s)) { display: none; }" % (tk, rk, sel))
    for group, opts in (("ty", TYPE_FILTERS), ("rg", region_filters())):
        for key, _label in opts:
            out.append('body:has(#%s-%s:checked) label[for="%s-%s"] '
                       '{ background: var(--ink); color: var(--page); border-color: var(--ink); }'
                       % (group, key, group, key))
    for tk, _t in TYPE_FILTERS:
        for rk, _r in region_filters():
            sel = ("" if tk == "all" else ".e-%s" % tk) + ("" if rk == "all" else ".r-%s" % rk)
            if not sel:
                continue
            if not any(("e-%s" % tk in c or tk == "all") and ("r-%s" % rk in c or rk == "all")
                       for c in [_row_classes(x) for x in REGISTRY_ALL]):
                out.append("body:has(#ty-%s:checked):has(#rg-%s:checked) .noresult "
                           "{ display: block; }" % (tk, rk))
    return "\n".join(out)


def _row_classes(c):
    return "e-%s r-%s" % (ENTITY_TYPE[c["competition_type"]], c["confederation"].lower())


def filter_bar():
    inputs, chips = [], []
    for group, opts in (("ty", TYPE_FILTERS), ("rg", region_filters())):
        row = []
        for key, label in opts:
            checked = ' checked' if key == "all" else ''
            inputs.append('<input class="toggle" type="radio" name="%s" id="%s-%s"%s>'
                          % (group, group, key, checked))
            row.append('<label class="linkchip" for="%s-%s">%s</label>' % (group, key, E(label)))
        chips.append('<div class="frow">%s</div>' % "".join(row))
    return "".join(inputs), "".join(chips)


PAGE_CSS = """
body { margin: 0; background: #06070a; font: 400 15px/1.5 system-ui, -apple-system, "Segoe UI", Roboto, sans-serif; }
.ctl { position: sticky; top: 0; z-index: 9; display: flex; flex-wrap: wrap; gap: 18px;
       padding: 12px 16px; background: #14161c; border-bottom: 1px solid #2b2f38; color: #c7ccd4; font-size: 13px; }
.ctl label { display: inline-flex; align-items: center; gap: 7px; cursor: pointer; user-select: none; }
.toggle { position: absolute; width: 1px; height: 1px; opacity: 0; pointer-events: none; }
.ctl .box { width: 15px; height: 15px; border-radius: 4px; border: 1px solid #4a505b; background: #0d0f13; flex: 0 0 auto; }
#t-light:checked ~ .ctl label[for="t-light"] .box,
#t-phone:checked ~ .ctl label[for="t-phone"] .box,
#t-src:checked   ~ .ctl label[for="t-src"]   .box,
#t-fi:checked    ~ .ctl label[for="t-fi"]    .box { background: #3bb072; border-color: #3bb072; }
.stage { margin: 0 auto; }
#t-phone:checked ~ .stage { max-width: 375px; box-shadow: 0 0 0 1px #2b2f38; }
#t-light:checked ~ .stage .fx {
  --page: #f3f3f0; --surface: #fbfbf9; --sunk: #edece7; --line: #e2e1da; --div: #cfcec5;
  --ink: #141410; --ink-2: #4c4c45; --muted: #77776e; --accent: #0a6e3a;
  --win: #157f43; --draw: #6f756d; --loss: #b23b3b; --pill-ink: #fff; --track: #e7e6e0;
}
.fi { display: none; }
#t-fi:checked ~ .stage .en { display: none; }
#t-fi:checked ~ .stage .fi { display: inline; }
.clogo svg { color: var(--muted); }

/* ---- the page ---- */
.chead { padding: 16px 0 2px; }
.chead h1 { font-size: clamp(22px, 5cqw, 28px); font-weight: 700; line-height: 1.03; margin: 0; }
.chead .meta { font-size: 13px; color: var(--muted); margin-top: 6px; }

/* the category heading: the SAME weight as a competition heading in the match block, so this page
   and the matches block read as one system. NOT a link — a category is not an entity. */
.cgroup { margin-top: 32px; }
.cgroup:first-of-type { margin-top: 16px; }
.cgroup > .gh { padding-bottom: 10px; border-bottom: 2px solid var(--div);
                font-size: 17px; font-weight: 700; color: var(--ink); }

/* ⚠ ONE WIDTH FOR EVERY PAGE: every page of the website has the same width.
   `system.css`'s 680px stands and this page does not touch it. An earlier
   version set `.inner { max-width: 1080px }` here, and a later one kept a toggle to compare a
   site-wide change — both struck. There is nothing to compare; the width is settled. */

/* the rows flow into columns when there is room. The breakpoint is the ROW's comfortable minimum
   rather than a device width, so the same rule gives 1 column on a phone and more on a desktop.
   ⚠ 290px, not 310px: inside the 680px measure the content box is ~624px, and 310px columns need
   648px — so 310 gave ONE column at the system width and the grid bought nothing. Measured. */
.cgroup .rows { display: grid; grid-template-columns: repeat(auto-fill, minmax(290px, 1fr));
                column-gap: 28px; }

/* one competition. Same grammar as the block's group head — logo, name, chevron. */
.crow { display: grid; grid-template-columns: 26px minmax(0, 1fr) auto; align-items: center;
        column-gap: 12px; padding: 13px 0; border-bottom: 1px solid var(--line); }
.crow:last-child { border-bottom: 0; }

/* ---- the filter bar ---- */
.fbar { margin: 14px 0 4px; display: flex; flex-direction: column; gap: 8px; }
.frow { display: flex; flex-wrap: wrap; gap: 8px; }
.frow .linkchip { display: inline-block; padding: 5px 12px; border-radius: 999px;
                  border: 1px solid var(--line); color: var(--ink-2); font-size: 13px;
                  cursor: pointer; user-select: none; transition: background-color .12s ease; }
@media (hover: hover) { .frow .linkchip:hover { border-color: var(--ink-2); color: var(--ink); } }
.noresult { display: none; margin: 28px 0; color: var(--muted); font-size: 14px; }
.cid { min-width: 0; }
.crow .nm { font-size: 15px; font-weight: 600; color: var(--ink); line-height: 1.25; }
.crow .sub { display: block; font-size: 12px; color: var(--muted); margin-top: 2px; }

/* ---- PROVENANCE MARKS (#58) — harness, off by default ----------------------
   ⚠ `is-*` per #51's proposed naming rule, so these cannot collide with system.css the way
   `.res` and `.win` silently did. Neither name exists in system.css. */
#t-src:checked ~ .stage .is-gap       { text-decoration: underline wavy #d08a2a;
                                        text-underline-offset: 3px; }
#t-src:checked ~ .stage .clogo.is-gap { text-decoration: none; outline: 1px dashed #d08a2a;
                                        border-radius: 4px; }
#t-src:checked ~ .stage .is-proposed  { text-decoration: underline dotted currentColor;
                                        text-underline-offset: 3px; }

/* ---- the harness below the page ---- */
.harness { max-width: 1040px; margin: 44px auto 0; padding: 0 16px 60px; color: #9aa1ab; font-size: 13px; }
/* ⚠ scroll-margin is MEASURED, not guessed. The bar is 82px at this pane's 417px width. */
.harness h2 { color: #e6e9ee; font-size: 15px; margin: 34px 0 4px; scroll-margin-top: 108px; }
.jump { margin: 10px 0 18px; }
.jump a { color: #9aa1ab; text-decoration: underline; text-underline-offset: 3px;
          text-decoration-color: #3a3f49; margin-right: 14px; white-space: nowrap; }
.jump a:hover { color: #e6e9ee; text-decoration-color: #6f7681; }
.harness p { margin: 6px 0 14px; line-height: 1.65; max-width: 82ch; }
.harness b { color: #c7ccd4; }
.harness code { font-family: ui-monospace, Consolas, monospace; font-size: 12px; color: #c7ccd4; }
table.t { border-collapse: collapse; width: 100%; font-size: 12.5px; }
table.t th { text-align: left; color: #7c828c; font-weight: 600; padding: 6px 10px 6px 0;
             border-bottom: 1px solid #2b2f38; white-space: nowrap; }
table.t td { padding: 7px 10px 7px 0; border-bottom: 1px solid #1b1e25; vertical-align: top; }
table.t td:first-child { color: #c7ccd4; white-space: nowrap; }
table.t .mono { font-family: ui-monospace, Consolas, monospace; font-size: 11.5px; color: #9aa1ab; }
.pill { display: inline-block; padding: 1px 7px; border-radius: 999px; font-size: 11px;
        border: 1px solid currentColor; white-space: nowrap; }
.s-ok       { color: #6f7681; }
.s-proposed { color: #8f9bb3; }
.s-gap      { color: #d08a2a; }
tr.r-gap td:first-child, tr.r-proposed td:first-child { color: #e6e9ee; }
.chg { color: #d08a2a; }
.new { color: #8f9bb3; }
"""


def _prov_table():
    rows = "".join(
        '<tr class="r-%s"><td>%s</td><td>%s</td><td class="mono">%s</td>'
        '<td><span class="pill s-%s">%s</span></td><td>%s</td></tr>'
        % (status, el, lvl, E(src), status, status, note)
        for el, lvl, src, status, note in PROVENANCE)
    return ('<table class="t"><tr><th>Element</th><th>Level</th><th>Source</th>'
            '<th>Status</th><th>Note</th></tr>%s</table>' % rows)


def _types_table():
    members = {}
    for c in REGISTRY_ALL:
        members.setdefault(c["competition_type"], []).append(c)
    # types with no registry competition have no example in the data, so they carry a typed one
    DOC_EXAMPLE = {
        "domestic_super_cup": "DFL-Supercup \u00b7 FA Community Shield",
        "club_qualifying": "Champions League qualifying rounds",
        "intercontinental_cup": "FIFA Intercontinental Cup",
        "club_friendly_domestic": "a pre-season friendly between two German clubs",
        "club_friendly_international": "Bayern vs Manchester United, pre-season",
        "national_team_friendly": "Germany vs Brazil, friendly",
    }
    rows = []
    for ct, row in _TYPES.items():
        ms = sorted(members.get(ct, []), key=lambda c: c.get("sort_order") or 0)
        example = (", ".join((short(m["league_code"]) if m["league_code"] in SHORT_CODES
                              else m.get("name") or m["league_code"]) for m in ms[:3])
                   if ms else DOC_EXAMPLE.get(ct, "\u2014"))
        flag = (' <span class="new">new</span>' if ct in NEW_TYPES else
                ' <span class="new">renamed</span>' if ct in RENAMED_TYPES.values() else "")
        rows.append('<tr><td class="mono">%s%s</td><td class="mono">%s</td>'
                    '<td class="mono">%s</td><td class="mono">%s</td><td>%s</td>'
                    '<td class="mono">%d</td></tr>'
                    % (E(ct), flag, E(row["entity_type"]), E(row["single_country"]),
                       E(row["label_i18n_key"]), E(row["label_en"]),
                       "%s · %d" % (E(example), len(ms))))
    return ('<table class="t"><tr><th>competition_type</th><th>entity_type</th>'
            '<th>single_country</th><th>label_i18n_key</th><th>label_en</th>'
            '<th>example / n</th></tr>%s</table>' % "".join(rows))


def _csv_table(path):
    with open(path, encoding="utf-8", newline="") as fh:
        rows = list(csv.reader(fh))
    head = "".join("<th>%s</th>" % E(h) for h in rows[0])
    body = "".join("<tr>%s</tr>" % "".join('<td class="mono">%s</td>' % E(c) for c in r)
                   for r in rows[1:])
    return '<table class="t"><tr>%s</tr>%s</table>' % (head, body)


def _region_table():
    rows = []
    for _ct, ms in grouped(REGISTRY_ALL):
        for c in ms:
            old, new = c.get("country") or "", region(c)
            rows.append('<tr><td class="mono">%s</td><td class="mono">%s</td>'
                        '<td class="mono">%s</td><td class="mono">%s</td>'
                        '<td class="mono%s">%s</td></tr>'
                        % (c["league_code"], c["confederation"],
                           str(SINGLE_COUNTRY[c["competition_type"]]).lower(),
                           E(old), " chg" if new != old else "", E(new)))
    return ('<table class="t"><tr><th>code</th><th>confederation</th><th>single_country</th>'
            '<th>sub-line today (country)</th><th>sub-line proposed</th></tr>%s</table>'
            % "".join(rows))


def build():
    gs = grouped(REGISTRY_ALL)
    body = "\n".join(
        '<div class="cgroup"><div class="gh is-proposed">%s</div>'
        '<div class="rows">%s</div></div>'
        % (E(TYPE_EN[ct]), "\n".join(comp_row(c) for c in ms))
        for ct, ms in gs)
    f_inputs, f_bar = filter_bar()
    n_comps = sum(len(m) for _g, m in gs)
    changed = sum(1 for _g, ms in gs for c in ms if region(c) != (c.get("country") or ""))

    return """<!doctype html>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Competitions -- /en/competitions/ (mock)</title>
<style>
%s
%s
%s
</style>

<input class="toggle" type="checkbox" id="t-light">
<input class="toggle" type="checkbox" id="t-phone">
<input class="toggle" type="checkbox" id="t-fi">
<input class="toggle" type="checkbox" id="t-src">
%s

<div class="ctl">
  <label for="t-light"><span class="box"></span>Light</label>
  <label for="t-phone"><span class="box"></span>Phone 375px</label>
  <label for="t-fi"><span class="box"></span>Finnish (width probe)</label>
  <label for="t-src"><span class="box"></span>Show gaps</label>
</div>

<div class="stage">
  <div class="fx">
    <div class="inner">

      <nav class="crumb">
        <a href="/en/">%s</a>
        <span class="sep">&rsaquo;</span>
        <span class="here">%s</span>
      </nav>

      <header class="chead">
        <h1>%s</h1>
        <p class="meta">%d competitions in %d categories</p>
      </header>

      <div class="fbar">%s</div>

      <p class="noresult">No competition matches both filters.</p>

%s
    </div>
  </div>
</div>

<div class="harness">

  <h2 id="s0">What this is</h2>
  <p><b>/en/competitions/ &mdash; the page the menu's first item points at.</b> Not a COMPETITION
  page (<code>/en/bundesliga/</code>), which is one league. Everything below the design is the
  review harness, not the page.</p>
  <p class="jump">Jump: <a href="#s1">1 the taxonomy seed</a> <a href="#s2">2 the new seed</a>
  <a href="#s3">3 what they produce</a> <a href="#s4">4 provenance</a></p>

  <h2 id="s1">1 &nbsp;<code>competition_types.csv</code> <span class="n">&mdash; reshaped</span></h2>
  <p><b><code>display_group</code> is deleted</b> (CPO 2026-08-11). It grouped club competitions
  by FORMAT and everything else by GEOGRAPHY, so its axis changed halfway through; it overloaded
  BLANK to mean &ldquo;not browsable&rdquo;; and once <code>club_world_cup</code> existed, none of
  its four values fitted. No dbt model reads it &mdash; all seven that join this seed read
  <code>entity_type</code> only.</p>
  <p><b>Two renames and two additions.</b> A type that holds ONE specific competition is named for
  it; a type that holds a CLASS is named generically. <code>continental_club</code> was the only
  type naming the ENTITY rather than the format. The Club World Cup and the Intercontinental Cup
  are two types, not one, because one is a tournament and the other a one-off between
  titleholders &mdash; the split the taxonomy already makes at every other level.</p>
  <p><b><code>single_country</code> is the only column added</b>, and it answers exactly one
  question: which field a row's sub-line reads.</p>
  %s

  <h2 id="s2">2 &nbsp;<code>confederations.csv</code> <span class="n">&mdash; NEW seed, 7
  rows</span></h2>
  <p>Its own table rather than more columns above, because the region varies <b>within</b> a
  <code>competition_type</code>: <code>COAM</code> and <code>EURO</code> are both
  <code>continental_championship</code>, and they are South America and Europe. Same shape as the
  taxonomy seed, which is the same shape as <code>metric_catalogue.csv</code>. The KEYS are
  guarded against the enum the registry already documents, so an invented eighth confederation
  fails instead of rendering. <b>The seven English labels are a proposal, not approved copy.</b></p>
  %s

  <h2 id="s3">3 &nbsp;What the two produce <span class="n">&mdash; the region on every row, the
  thing #54 left unresolved</span></h2>
  <p>The row printed the registry's <code>country</code>, which holds a country <b>or</b> a
  continent <b>or</b> the literal &ldquo;International&rdquo;, inconsistently and within one
  category: <code>EURO</code> said <i>Europe</i> while <code>COAM</code> and <code>AFCON</code>,
  the same <code>competition_type</code>, said <i>International</i>.</p>
  <p>One rule now, two read branches: <b>single_country=true</b> takes the registry's country;
  <b>false</b> takes its confederation's label. <b>%d of %d rows change and none break</b>
  &mdash; marked <span class="chg">amber</span>.</p>
  %s

  <h2 id="s4">4 &nbsp;Provenance <span class="n">&mdash; #58, every element declares its
  source</span></h2>
  <p><b>Every row below is a COLUMN OF ONE MART</b> &mdash; <code>mart_competition_index</code>
  &mdash; not a file. An earlier version of this table named four sources for one page: the
  registry YAML, two seed CSVs and <code>dim_league</code>. That is a story rather than a contract,
  and <code>content_architecture.md</code> &sect;1 already forbids it: <i>one block = one mart,
  nothing computes in a page</i>. <b>#62</b> carries the fix &mdash; the registry seed is projected
  down to three columns today, which is why the export reads the YAML directly.</p>
  <p>It is also what makes this rule machine-checkable. &ldquo;One element, one column&rdquo; can be
  verified by a build step; &ldquo;one element, somewhere across four files&rdquo; cannot.</p>
  <p>Turn on <b>&ldquo;Show gaps&rdquo;</b> at the top to see these on the page.
  <span class="pill s-gap">gap</span> &nbsp;no source exists &mdash; the value shown is a stand-in
  and is marked. &nbsp;<span class="pill s-proposed">proposed</span> &nbsp;a real source that does
  not exist yet, proposed by this design &mdash; which is <b>every content row</b>, because the
  mart does not exist. &nbsp;<span class="pill s-ok">ok</span> &nbsp;ships today.</p>
  %s

</div>
""" % (SYSTEM_CSS.read_text(encoding="utf-8"), PAGE_CSS, filter_css(),
       f_inputs,
       loc("crumbHome"), COPY["navCompetitions"][0], loc("navCompetitions"),
       n_comps, len(gs), f_bar, body,
       _types_table(),
       _csv_table(CONFED_PROPOSED),
       changed, n_comps, _region_table(),
       _prov_table())


def check():
    listed = [c["league_code"] for _g, ms in grouped(REGISTRY_ALL) for c in ms]
    assert len(set(listed)) == len(listed), "a competition is listed twice"
    assert set(listed) == {c["league_code"] for c in REGISTRY_ALL}, \
        "the page and the registry disagree on the set"

    regions = set(CONFED_EN.values())
    for c in REGISTRY_ALL:
        code, ct = c["league_code"], c["competition_type"]
        assert ct in _TYPES, "%s: competition_type %r is not in the taxonomy seed" % (code, ct)
        assert TYPE_EN[ct] and TYPE_KEY[ct], "%s: %r has a blank label" % (code, ct)
        assert _TYPES[ct]["single_country"] in ("true", "false"), \
            "%s: %r has no usable single_country" % (code, ct)
        assert c.get("confederation") in CONFED_EN, \
            "%s: confederation %r does not resolve through confederations.csv" % (
                code, c.get("confederation"))
        if SINGLE_COUNTRY[ct]:
            assert c.get("country"), "%s is single_country but has no country" % code
            # a single-country row whose country is a region is mistyped
            assert c["country"] not in regions, \
                "%s is single_country=true but its country %r is a REGION — the row is mistyped" \
                % (code, c["country"])
        assert region(c), "%s resolves to an empty sub-line" % code

    # every SEED row, including the six with no registry competition yet
    for ct, row in _TYPES.items():
        assert row["label_en"] and row["label_i18n_key"], "seed: %r has a blank label" % ct
        assert row["single_country"] in ("true", "false"), "seed: %r has no single_country" % ct
        assert row["entity_type"] in ("club", "national"), "seed: %r has no entity_type" % ct
    labels = [r["label_en"] for r in _TYPES.values()]
    assert len(set(labels)) == len(labels), "two competition_types share a label_en"
    keys = [r["label_i18n_key"] for r in _TYPES.values()]
    assert len(set(keys)) == len(keys), "two competition_types share a label_i18n_key"

    gs = grouped(REGISTRY_ALL)
    changed = [c["league_code"] for _g, ms in gs for c in ms
               if region(c) != (c.get("country") or "")]
    print("  %d competitions under %d category heading(s) from the seed: %s"
          % (len(listed), len(gs), ", ".join(TYPE_EN[g] for g, _ in gs)))
    print("  %d seed types have no registry competition: %s"
          % (len(_TYPES) - len(gs),
             ", ".join(sorted(set(_TYPES) - {g for g, _ in gs}))))
    print("  region: %d of %d sub-lines change, 0 empty: %s"
          % (len(changed), len(listed), ", ".join(changed)))
    n_gap = sum(1 for r in PROVENANCE if r[3] == "gap")
    n_prop = sum(1 for r in PROVENANCE if r[3] == "proposed")
    print("  provenance: %d elements — %d ok, %d proposed, %d NAMED GAPS"
          % (len(PROVENANCE), len(PROVENANCE) - n_gap - n_prop, n_prop, n_gap))


if __name__ == "__main__":
    if sys.argv[1:2] == ["--out"]:
        OUT = Path(sys.argv[2]) / OUT.name
    check_seed_matches_shipped()
    check_registry_still_unedited()
    check_confederation_enum()
    check()
    OUT.write_text(build(), encoding="utf-8")
    print("  wrote %s (%.0f KB)" % (OUT.name, OUT.stat().st_size / 1024))
