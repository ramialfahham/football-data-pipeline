"""Mock of the Team page design: the team page in three tabs, built from the BUILT
Dortmund page (site_v2/dist/en/teams/borussia-dortmund/) and its served payload. Blocks the built
page has are moved, not redrawn; new blocks use the site's shared elements in the markup the built
site emits for them (the match row, the fold, the result row, the player row, the fact row, the
table). Every value is a served payload or sample field; a block nothing serves is a named gap."""
import csv
import html
import json
import math
import re
import shutil
from datetime import datetime
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
DIST = REPO / "site_v2/dist"
DATA = REPO / "site_v2/src/data"
OUT = Path(__file__).parent
E = html.escape
TEAM_ID, SLUG = 165, "borussia-dortmund"

CHEV = ('<svg class="chev" viewBox="0 0 24 24" aria-hidden="true" focusable="false">'
        '<path d="M9 6l6 6-6 6" fill="none" stroke="currentColor" stroke-width="2.2" '
        'stroke-linecap="round" stroke-linejoin="round"></path></svg>')
DAYS = ("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun")
MONTHS = ("Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sept", "Oct", "Nov", "Dec")


def balanced(h, start):
    tag = re.match(r"<(\w+)", h[start:]).group(1)
    depth = 0
    pat = re.compile(r"<(/?)%s\b[^>]*>" % tag)
    for m in pat.finditer(h, start):
        depth += -1 if m.group(1) else 1
        if depth == 0:
            return h[start:m.end()]
    raise ValueError(tag)


def grab(h, marker):
    i = h.index(marker)
    i = h.rindex("<", 0, i + 1) if not marker.startswith("<") else i
    return balanced(h, i)


def ts(s):
    return datetime.fromisoformat(s.replace(" ", "T"))


def day_head(s):
    d = ts(s)
    return f"{DAYS[d.weekday()]} {d.day} {MONTHS[d.month - 1]}"


def short_date(s):
    d = ts(s)
    return f"{d.day} {MONTHS[d.month - 1]}"


def crest(name, url):
    if url:
        return (f'<div class="crest xs"> <img src="{E(url)}" alt="" loading="lazy" width="24" height="24"> </div>')
    return '<div class="crest xs"></div>'


def sechead(label, note=""):
    n = f'<span class="win-note">{note}</span>' if note else ""
    return f'<div class="sechead"><span class="eyebrow">{label}</span>{n}</div>'


def gap(text):
    return f'<p class="mockgap"><b>Gap:</b> {text}</p>'


BUILT_FIXTURE_SLUGS = {p.name for p in (DIST / "en/bundesliga/matches").iterdir() if p.is_dir()}
PLAYER_PAGES = {p.name.rsplit("-", 1)[-1]: p.name for p in (DIST / "en/players").iterdir() if p.is_dir()}


def match_row(home, away, kickoff, fslug=None, comp_slug="bundesliga"):
    linked = fslug in BUILT_FIXTURE_SLUGS
    tag = "a" if linked else "div"
    href = f' href="/en/{comp_slug}/matches/{fslug}/"' if linked else ""
    sides = "".join(f'<span class="side">{crest(t["name"], t.get("crest"))}<span class="nm">{E(t["name"])}</span></span>'
                    for t in (home, away))
    return (f'<{tag} class="fxrow"{href}><span class="sides">{sides}</span>'
            f'<span class="when"><b class="t">{ts(kickoff):%H:%M}</b><span class="rowtz">UTC</span></span></{tag}>')


_fold = 0


def fold(rest, n):
    global _fold
    _fold += 1
    fid = f"fold-{_fold}"
    return (f'<input type="checkbox" class="fold-in" id="{fid}"><div class="fold-rest">{rest}</div>'
            f'<label class="fold-ctl" for="{fid}"><span class="lbl"><span class="closed">Show all {n}</span>'
            f'<span class="opened">Show less</span></span>{CHEV}</label>')


def comp_group(name, slug, logo, rows_with_day, folded=True, attrs=""):
    head = (f'<div class="gh"><a class="cnm" href="/en/{slug}/"><span class="clogo">{crest(name, logo)}</span>'
            f'<span class="nm">{E(name)}</span>{CHEV}</a></div>')
    parts, last = [], None
    for day, row in rows_with_day:
        parts.append((f'<div class="dh">{day}</div>' if day != last else "") + row)
        last = day
    if folded:
        shown, rest = parts[:3], parts[3:]
        body = "".join(shown) + (fold("".join(rest), len(parts)) if rest else "")
    else:
        body = "".join(parts)
    return f'<div class="fxgroup"{attrs}>{head}{body}</div>'


PLAYED_PAGES = {}
for _p in DIST.glob("en/*/matches/*/index.html"):
    PLAYED_PAGES.setdefault(_p.parent.name[:10], []).append(_p.parent.relative_to(DIST).as_posix())


def _slugify(name):
    import unicodedata
    s = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", "-", s).strip("-")


def played_href(r, comp_slug="bundesliga"):
    for path in PLAYED_PAGES.get(r["kickoff_datetime"][:10], []):
        if SLUG in path:
            return "/" + path + "/"
    opp = _slugify(r["opponent_name"])
    home, away = (SLUG, opp) if r["is_home"] else (opp, SLUG)
    return f'/en/{comp_slug}/matches/{r["kickoff_datetime"][:10]}-{home}-vs-{away}/'


def result_row(r, comp_name, comp_slug="bundesliga"):
    pill = f'<span class="pill {r["result"]}">{r["result"]}</span>'
    ha = "H" if r["is_home"] else "A"
    href = played_href(r, comp_slug)
    open_tag = f'<a class="lrow" href="{href}">' if href else '<div class="lrow">'
    close_tag = "</a>" if href else "</div>"
    return (open_tag + '<div class="resrow">' + pill +
            f'<span class="rscore">{r["goals_for"]}–{r["goals_against"]}</span>'
            f'<span class="ropp"><span class="club">{crest(r["opponent_name"], r["opponent_logo_url"])}'
            + (lambda w: f'<span class="cn">{" ".join(w[:-1])} <span class="keep">{w[-1]}&nbsp;<span class="ha">{ha}</span></span></span></span></span>')(E(r["opponent_name"]).split(" ")) +
            f'<span class="rmeta"><span class="nb">{E(comp_name)}</span> · <span class="nb">{short_date(r["kickoff_datetime"])}</span></span>'
            '</div>' + close_tag)


def frow(label, value, sub):
    return (f'<div class="frow"><span class="fl">{label}</span><span class="fv"><span class="fvv"><b>{value}</b></span>'
            f'<span class="sub">{sub}</span></span></div>')


def age(birth, on="2026-10-19"):
    b, d = datetime.fromisoformat(birth), datetime.fromisoformat(on)
    return d.year - b.year - ((d.month, d.day) < (b.month, b.day))


def player_row(p, stats=True):
    pid = str(p["player_id"])
    slug = PLAYER_PAGES.get(pid)
    tag = "a" if slug else "div"
    href = f' href="/en/players/{slug}/"' if slug else ""
    photo = f'<img src="{E(p["photo"])}" alt="" loading="lazy" width="34" height="34">' if p.get("photo") else ""
    meta = [p.get("nationality"), str(age(p["birth_date"])) if p.get("birth_date") else None]
    g, a = p["goals"], p["assists"]
    return (f'<{tag} class="lrow"{href}><div class="plrow"><span class="pphoto">{photo}</span>'
            f'<span class="pname"><span class="nm">{E(p["name"])}</span><span class="ps">'
            + E(" · ".join(x for x in meta + [
                f'{p["appearances"]} appearance{"" if p["appearances"] == 1 else "s"}' if p["appearances"] is not None else None,
                f'{round(p["minutes_per_appearance"])} minutes per appearance' if p["appearances"] else None] if x))
            + '</span></span>'
            + (f'<span class="pstat"><span class="nb"><b>{g}</b> goal{"" if g == 1 else "s"}</span> · '
               f'<span class="nb"><b>{a}</b> assist{"" if a == 1 else "s"}</span></span>' if stats else "")
            + f'</div></{tag}>')


SEASON_TYPE = {r["league_code"]: r["season_type"] for r in
               csv.DictReader(open(REPO / "dbt_project/seeds/competition_registry.csv", encoding="utf-8"))}


def season_label(y, code="BL1"):
    return str(y) if SEASON_TYPE.get(code) == "calendar_year" else f"{y}/{str(y + 1)[2:]}"


def history_table(rows, with_rank):
    head = ('<div class="ctab-head"><span class="h rk">#</span><span class="h nmh"></span><span class="h">P</span>'
            '<span class="h wdl">W</span><span class="h wdl">D</span><span class="h wdl">L</span>'
            '<span class="h wdl">Goals</span><span class="h">GD</span><span class="h">Pts</span></div>')
    out = []
    for s in rows:
        rk = s.get("latest_rank") if with_rank else None
        gd = s["goal_diff"]
        out.append(f'<div class="ctab-row"><span class="rk num">{rk if rk is not None else ""}</span>'
                   f'<span class="tm"><span class="nm">{season_label(s["season_api_year"], s["league_code"])}</span></span>'
                   f'<span class="n num">{s["played"]}</span><span class="n num wdl">{s["wins"]}</span>'
                   f'<span class="n num wdl">{s["draws"]}</span><span class="n num wdl">{s["losses"]}</span>'
                   f'<span class="n num wdl">{s["goals_for"]}:{s["goals_against"]}</span>'
                   f'<span class="n num gd">{gd:+d}</span><span class="n num pts">{s["points"]}</span></div>'.replace(">+0<", ">0<"))
    return f'<div class="ctab-section"><div class="ctab">{head}{"".join(out)}</div></div>'


TABS = [("overview", "Overview"), ("matches", "Matches"), ("stats", "Performance")]

TAB_CSS = ("\n".join(f'#tab-{k}:checked ~ .tabs .tab[for="tab-{k}"]' + ("," if i < len(TABS) - 1 else "")
                     for i, (k, _) in enumerate(TABS))
           + " { color: var(--ink); font-weight: 700; border-bottom-color: var(--ink); }\n"
           + "\n".join(f'#tab-{k}:checked ~ .page[data-page="{k}"]' + ("," if i < len(TABS) - 1 else "")
                       for i, (k, _) in enumerate(TABS))
           + " { display: block; }\n")

HARNESS_CSS = """
/* MOCK HARNESS ONLY */
.mockbar { font: 600 12px/1.45 system-ui, sans-serif; background: #fff3c4; color: #3a2f00;
  padding: 8px 16px; border-bottom: 1px solid #e0c96a; }
.mockbar .note { font-weight: 400; display: block; margin-top: 2px; }
/* PROPOSED: the Competitions block (one list row per competition) */
a.lrow.tc { padding-block: 12px; }
.tc .tcin { display: grid; grid-template-columns: 24px minmax(0, 1fr) auto;
  grid-template-areas: "crest name right" ". extra extra";
  column-gap: 12px; row-gap: 8px; align-items: center; }
.tc .tc-keep { white-space: nowrap; }
.tc .tc-rank2 { display: none; font-size: 15px; font-weight: 700; color: var(--ink); }
.tc .tc-extra:not(:has(.cchips)) { display: none; }
@container (max-width: 340px) {
  .tc .tcin { grid-template-areas: "crest name name" ". extra extra"; }
  .tcomps .tc .tc-extra { display: grid; grid-template-columns: auto 1fr; grid-template-areas: "rank nums" "pills pills";
    justify-items: start; align-items: baseline; gap: 8px 0; }
  .tcomps .tc .tc-extra .cchips { grid-area: pills; margin-right: 0; }
  .tcomps .tc .tc-rank2 { grid-area: rank; }
  .tcomps .tc .tc-nums { grid-area: nums; margin-left: 0; }
  .tcomps .tc .tc-extra:has(.tc-nums) .tc-rank2::after { content: " ·"; font-size: 12px; font-weight: 400; color: var(--muted); margin-right: 4px; }
  .tc .tc-right { display: none; }
  .tc .tc-rank2 { display: inline; }
  .tc .tc-extra:not(:has(.cchips)) { display: flex; }
  .tc .tc-extra .cchips { margin-right: auto; }
}
.tc .tc-crest { grid-area: crest; }
.tc .tc-name { grid-area: name; font-size: 15px; font-weight: 600; color: var(--ink); min-width: 0; }
.tc .tc-ctx { font-size: 12px; font-weight: 400; color: var(--muted); white-space: nowrap; }
.tc .tc-right { grid-area: right; font-size: 15px; font-weight: 700; color: var(--ink); white-space: nowrap; font-variant-numeric: tabular-nums; }
.tc .tc-extra { grid-area: extra; display: flex; align-items: center; justify-content: space-between; gap: 8px 14px; flex-wrap: wrap; }
.tc .tc-nums { margin-left: auto; font-size: 12px; color: var(--muted); font-variant-numeric: tabular-nums; }
.tc .tc-nums b { font-size: 15px; font-weight: 700; color: var(--ink); }
.tcomps .tc-keep { white-space: nowrap; }
/* PROPOSED system.css: the Filter row as a native dropdown in the row's own box */
.seg.sel { position: relative; padding: 0; }
.seg.sel .sel-in { appearance: none; -webkit-appearance: none; width: 100%; border: 0; background: transparent;
  font: inherit; font-size: 13px; font-weight: 700; color: var(--ink); padding: 12px 40px 12px 14px;
  border-radius: 8px; cursor: pointer; }
.seg.sel .sel-in:focus-visible { outline: 2px solid var(--accent); outline-offset: -2px; }
.seg.sel .sel-in option { color: var(--ink); background: var(--surface); }
.seg.sel .chev { position: absolute; right: 14px; top: 50%; transform: translateY(-50%) rotate(90deg); pointer-events: none; }
/* the open list in the site's design where the browser allows it; elsewhere the system's own list */
@supports (appearance: base-select) {
  .seg.sel .sel-in, .seg.sel .sel-in::picker(select) { appearance: base-select; }
  .seg.sel .sel-in::picker-icon { display: none; }
  .seg.sel .sel-in::picker(select) { background: var(--sunk); border: 1px solid var(--line); border-radius: 9px;
    padding: 3px; margin-top: 6px; box-shadow: 0 10px 28px rgba(0, 0, 0, .45); }
  .seg.sel .sel-in option { background: transparent; color: var(--muted); font-size: 13px; font-weight: 600;
    padding: 10px 12px; border-radius: 6px; cursor: pointer; }
  .seg.sel .sel-in option::checkmark { display: none; }
  .seg.sel .sel-in option:hover { color: var(--ink-2); background: color-mix(in srgb, var(--ink) 11%, transparent); }
  .seg.sel .sel-in option:checked { background: var(--surface); color: var(--ink); font-weight: 700; box-shadow: 0 1px 3px rgba(0, 0, 0, .25); }
  .seg.sel .sel-in option:focus-visible { outline: 2px solid var(--accent); outline-offset: -2px; }
}
/* PROPOSED: the squad's player rows in two columns where there is room */
.sqgrid { display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); column-gap: 24px; }
.sqgrid > .lrow { border-bottom: 1px solid var(--line); margin-inline: 0; padding-inline: 0; }
/* PROPOSED system.css: the result row keeps H/A with the last word of the club's name */
.resrow .ropp .keep { white-space: nowrap; }
.tcomps .tc-ctx { font-size: 12px; font-weight: 400; color: var(--muted); white-space: nowrap; }
/* PROPOSED, variant A: a stat strip */
a.lrow.ta, a.lrow.tb { padding-block: 12px; }
.ta .ta-in { display: grid; grid-template-columns: 24px minmax(0, 1fr); grid-template-areas: "crest name" ". strip";
  column-gap: 12px; row-gap: 8px; align-items: center; }
.ta .tc-crest, .tb .tc-crest { grid-area: crest; }
.ta .tc-name, .tb .tc-name { grid-area: name; font-size: 15px; font-weight: 600; color: var(--ink); min-width: 0; }
.ta .ts { grid-area: strip; display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)) minmax(0, 1.4fr) minmax(0, 1fr); column-gap: 8px; max-width: 420px; }
.ta .ts-c { display: flex; flex-direction: column; gap: 2px; min-width: 0; }
.ta .ts-l { font-size: 11px; font-weight: 700; color: var(--muted); }
.ta .ts-v { font-size: 15px; font-weight: 700; color: var(--ink); font-variant-numeric: tabular-nums; white-space: nowrap; }
/* PROPOSED, variant B: a text line */
.tb .tb-in { display: grid; grid-template-columns: 24px minmax(0, 1fr) auto; grid-template-areas: "crest name right" ". line line";
  column-gap: 12px; row-gap: 6px; align-items: center; }
.tb .tb-right { grid-area: right; font-size: 15px; font-weight: 700; color: var(--ink); white-space: nowrap; }
.tb .tb-line { grid-area: line; font-size: 12px; color: var(--muted); font-variant-numeric: tabular-nums; }
.tb .tb-line b { font-size: 13px; font-weight: 700; color: var(--ink); }
.mockvariant { font: 600 12px/1.4 system-ui, sans-serif; color: #6b5300; background: #fff3c4; border-radius: 6px;
  padding: 4px 10px; margin: 14px 0 4px; }
.mockvariant span { font-weight: 400; margin-left: 6px; }
.mocksentence { font-size: 15px; color: var(--ink-2); margin: 16px 0 0; }
.mockgap { font: 13px/1.45 system-ui, sans-serif; color: #6b5300; background: #fff8dc;
  border: 1px dashed #d9b84a; border-radius: 8px; padding: 8px 12px; margin: 14px 0 0; }
"""


def _ord(n):
    return f'{n}{"th" if 10 <= n % 100 <= 20 else {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")}'


# the switch: tier-3 rows (the catalogue's importance_tier) are hidden in their places until the
# site's fold control opens them; their order never changes
# dropped from the pages: their metric_order becomes blank in the build
DROPPED = {"shots_off_target_per_match", "shots_blocked_per_match"}
# cards as season totals: the totals take the per-match rows' places
CARDS_AS_TOTALS = {"cards_yellow_per_match": "cards_yellow", "cards_red_per_match": "cards_red"}
# the key team metrics are tier 1; every other served team metric is tier 3
KEY = {"goals_per_match", "goals_against_per_match", "shots_per_match", "shots_on_goal_per_match",
       "shots_on_goal_against_per_match", "passes_per_match", "passes_accuracy_pct", "passes_share_pct",
       "duels_per_match", "duels_won_pct", "defensive_actions_per_match", "fouls_per_match", "cards_yellow", "cards_red"}
CAT = {r["metric_id"]: r for r in csv.DictReader(open(REPO / "dbt_project/seeds/metric_catalogue.csv", encoding="utf-8"))}
TIER = {m: ("1" if m in KEY else "3") for m in CAT}


def served_rows():
    out = []
    for r in json.loads((DATA / "metric_rows.json").read_text(encoding="utf-8"))["rows"]:
        if r["metric_id"] in DROPPED:
            continue
        if r["metric_id"] in CARDS_AS_TOTALS:
            c = CAT[CARDS_AS_TOTALS[r["metric_id"]]]
            r = {**r, "metric_id": c["metric_id"], "label_i18n_key": c["label_i18n_key"], "format": "integer", "per_match": False}
        out.append(r)
    return out
FOLD_CHEV = ('<svg class="chev" viewBox="0 0 24 24" aria-hidden="true" focusable="false"><path d="M9 6l6 6-6 6" '
             'fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"></path></svg>')
# the switch is the site's Filter row (segmented buttons) at the top of each table: Key metrics shows
# tier 1 and 2, All metrics shows every row in its place
ON = "background: var(--surface); color: var(--ink); font-weight: 700; box-shadow: 0 1px 3px rgba(0, 0, 0, .25);"
# a new element, proposed: an on/off switch "Show all metrics", off by default; on shows every row in
# its place. Track in the sunk ground, the knob in the surface; on, the track takes the accent
FOLD_CSS = ('<style>.tsw:not(:checked) ~ * .t3, .tsw:not(:checked) ~ * .t3g { display: none; } '
            '.tsw { position: absolute; opacity: 0; width: 1px; height: 1px; pointer-events: none; } '
            '.tsw-lbl { display: flex; align-items: center; justify-content: flex-end; gap: 10px; margin: 4px 0 10px; '
            'font-size: 13px; font-weight: 600; color: var(--ink-2); cursor: pointer; } '
            '.tsw-track { position: relative; width: 36px; height: 20px; border-radius: 10px; background: var(--sunk); '
            'border: 1px solid var(--line); transition: background .15s; flex: 0 0 auto; } '
            '.tsw-knob { position: absolute; top: 2px; left: 2px; width: 14px; height: 14px; border-radius: 50%; '
            'background: var(--ink-2); transition: transform .15s; } '
            '.tsw:checked ~ .tsw-lbl .tsw-track { background: var(--ink-2); border-color: var(--ink-2); } '
            '.tsw:checked ~ .tsw-lbl .tsw-knob { transform: translateX(16px); background: var(--page); } '
            '.tsw:focus-visible ~ .tsw-lbl .tsw-track { outline: 2px solid var(--accent); outline-offset: 2px; } '
            '.yoyt-wrap .ctab.yoyt .ctab-row { background: transparent; } '
            '.tsw:not(:checked) ~ .yoyt-wrap .ctab.yoyt .ctab-row:nth-child(odd of :not(.t3)), '
            '.tsw:checked ~ .yoyt-wrap .ctab.yoyt .ctab-row:nth-child(odd) '
            '{ background: color-mix(in srgb, var(--ink) 5%, transparent); }</style>')


def fold_open(fid):
    return (f'<input class="tsw" type="checkbox" role="switch" id="{fid}">'
            f'<label class="tsw-lbl" for="{fid}">Show all metrics<span class="tsw-track" aria-hidden="true">'
            '<span class="tsw-knob"></span></span></label>')


def fold_ctl(fid, n):
    return ""


def league_values(league_code):
    """Every club's served value per metric in the featured season of one league, from the sample."""
    vals = {}
    for p in sorted((DATA / "teams").glob("*.json")):
        t = json.loads(p.read_text(encoding="utf-8"))
        for s in t["seasons"]:
            if s.get("is_featured_season") and s.get("league_code") == league_code:
                for b in s.get("benchmarks") or []:
                    if b.get("metric_value") is not None:
                        vals.setdefault(b["metric_key"], []).append((t["name"], b["metric_value"]))
    return vals


def build_league_rows(feat, team_name="Borussia Dortmund"):
    import re
    strings = (REPO / "site_v2/src/i18n/strings.ts").read_text(encoding="utf-8")

    def label(key):
        m = re.search(r'"%s": "([^"]*)"' % re.escape(key), strings)
        return m.group(1) if m else key

    served = served_rows()
    groups = sorted(json.loads((DATA / "metric_groups.json").read_text(encoding="utf-8"))["groups"], key=lambda x: x["order"])
    bench = {b["metric_key"]: b for b in feat["benchmarks"]}
    clubs = league_values(feat["league_code"])
    bind = {"clean_sheets": "clean_sheets_pct"}

    def fmt(v, f):
        if v is None:
            return "–"
        from decimal import Decimal, ROUND_HALF_UP

        def r(x, q):
            return str(Decimal(str(x)).quantize(Decimal(q), rounding=ROUND_HALF_UP))
        return {"percent": r(v * 100, "1") + "%", "decimal_0": r(v, "1"), "integer": r(v, "1")}.get(f, r(v, "0.1"))

    css = ('<style>.rs-head,.rs-row{display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1.5fr) 4.6rem;'
           'column-gap:14px;align-items:center} '
           '@container (max-width:479.98px){.rs-head,.rs-row{grid-template-columns:minmax(0,1fr) 4.2rem;row-gap:6px}'
           '.rs-row .rs-strip,.rs-head .rs-scale{grid-column:1 / -1;grid-row:2}} '
           '.rs-row{padding:10px 0;border-bottom:1px solid var(--line)} '
           '.rs-name{font-size:14px;color:var(--ink);line-height:1.3} .rs-name small{display:block;font-size:12px;color:var(--muted)} '
           '.rs-strip{position:relative;height:14px;margin:26px 0 14px} .rs-medv{position:absolute;top:-25px;transform:translateX(-50%);'
           'font-size:11px;color:var(--ink-2);font-variant-numeric:tabular-nums;white-space:nowrap} '
           '.rs-legend{display:flex;flex-wrap:wrap;gap:4px 16px;font-size:12px;color:var(--ink-2);margin:2px 0 6px} '
           '.rs-legend span{display:inline-flex;align-items:center;gap:6px} '
           '.rs-k-club{width:6px;height:6px;border-radius:50%;background:color-mix(in srgb,var(--ink) 24%,transparent)} '
           '.rs-k-med{width:2px;height:14px;background:var(--ink-2)} .rs-k-dot{width:10px;height:10px;border-radius:50%;background:var(--ink)} '
           '.rs-dir{position:absolute;top:16px;left:0;font-size:11px;color:var(--muted);white-space:nowrap} .rs-dir.r{left:auto;right:0} '
           '.rs-line{position:absolute;left:0;right:0;top:50%;height:1px;background:var(--div)} '
           '.rs-med{position:absolute;top:-3px;bottom:-3px;width:2px;margin-left:-1px;background:var(--ink-2)} '
           '.rs-club{position:absolute;top:50%;width:6px;height:6px;margin:-3px 0 0 -3px;border-radius:50%;'
           'background:color-mix(in srgb,var(--ink) 24%,transparent)} '
           '.rs-dot{position:absolute;width:10px;height:10px;margin:-5px 0 0 -5px;border-radius:50%;background:var(--ink);'
           'box-shadow:0 0 0 2px var(--page)} .rs-val{text-align:right;font-size:15px;font-weight:700;color:var(--ink);'
           'font-variant-numeric:tabular-nums;line-height:1.25} .rs-val small{display:block;font-size:12px;font-weight:400;'
           'color:var(--muted)} .rkgroup > .gh{margin-bottom:26px}</style>')
    out, missing = [FOLD_CSS, css, '<p class="bsub">Each value is ranked against the other Bundesliga clubs this season. The median '
                    'splits the league in two: half the clubs are above it, half below. <a class="mk-chevlink" href="/en/glossary/">Metric Glossary' + CHEV + '</a></p>', fold_open("tf-league"),
                    f'<div class="rs-legend" aria-hidden="true"><span><i class="rs-k-club"></i>Other Bundesliga teams</span>'
                    f'<span><i class="rs-k-med"></i>League median</span><span><i class="rs-k-dot"></i>{E(team_name)}</span></div>'
                    '<div class="lgt-wrap">'], []
    share_by_count = {"clean_sheets_pct", "shots_inside_box_pct", "duels_won_pct", "dribbles_success_pct", "saves_pct"}
    for grp in groups:
        rows = sorted((r for r in served if r["metric_group"] == grp["key"]), key=lambda r: r["metric_order"])
        if not rows:
            continue
        all_t3 = all(TIER.get(r["metric_id"]) == "3" for r in rows)
        out.append(f'<div class="rs-sec fxgroup rkgroup{" t3g" if all_t3 else ""}"><div class="gh"><span class="nm">'
                   f'{label("metricGroups.%s.label" % grp["key"])}</span></div>')
        for r in rows:
            key = bind.get(r["metric_id"], r["metric_id"])
            b = bench.get(key)
            f = "percent" if key.endswith("_pct") else r["format"]
            sub = "per match" if r["per_match"] else ("percentage" if key in share_by_count else "")
            name = label(r["label_i18n_key"]) + (f"<small>{sub}</small>" if sub else "")
            strip, val = "", '–<small>&nbsp;</small>'
            if b and clubs.get(key):
                v, med = b["metric_value"], b["league_median"]
                pts = clubs[key]
                lo, hi = min(x for _, x in pts), max(x for _, x in pts)
                span = (hi - lo) or 1
                # values always grow to the right; the ends sit inside the row so no dot is cut
                def pos(x):
                    return round(3 + (x - lo) / span * 94, 2)
                # one line: close values overlap and the overlap reads darker
                dots = [f'<span class="rs-club" style="left:{pos(x)}%" title="{E(club)}: {fmt(x, f)}"></span>'
                        for club, x in sorted(pts, key=lambda p: p[1]) if club != team_name]
                strip = ('<span class="rs-line"></span>'
                         f'<span class="rs-med" style="left:{pos(med)}%"></span><span class="rs-medv" style="left:{pos(med)}%">{fmt(med, f)}</span>'
                         + "".join(dots)
                         + f'<span class="rs-dot" style="left:{pos(v)}%;top:50%" title="{E(team_name)}: {fmt(v, f)}"></span>'
                         + ({'higher_better': '<span class="rs-dir r">better →</span>',
                             'lower_better': '<span class="rs-dir">← better</span>'}.get(r['direction'], '')))
                val = f'{fmt(v, f)}<small>{_ord(b["rank"])}</small>'
            else:
                missing.append(label(r["label_i18n_key"]) + (f" ({sub})" if sub else ""))
            t3 = " t3" if TIER.get(r["metric_id"]) == "3" else ""
            out.append(f'<div class="rs-row{t3}"><span class="rs-name">{name}</span><span class="rs-strip">'
                       f'{strip}</span><span class="rs-val">{val}</span></div>')
        out.append("</div>")
    out.append("</div>")
    return "".join(out) + gap(f"{len(missing)} of {len(served)} rows have no league values yet: "
                                + ", ".join(missing) + ". The warehouse serves them in this page's build.")


def build_season_bars(feat):
    """Compared with last season: the match page's comparison element (value · name with split bar · value),
    last season at the same point on the left, this season on the right; the served 36-row list."""
    strings = (REPO / "site_v2/src/i18n/strings.ts").read_text(encoding="utf-8")

    def label(key):
        m = re.search(r'"%s": "([^"]*)"' % re.escape(key), strings)
        return m.group(1) if m else key

    served = served_rows()
    groups = sorted(json.loads((DATA / "metric_groups.json").read_text(encoding="utf-8"))["groups"], key=lambda g: g["order"])
    bind = {"clean_sheets": "clean_sheets_pct"}
    share_by_count = {"clean_sheets_pct", "shots_inside_box_pct", "duels_won_pct", "dribbles_success_pct", "saves_pct"}
    from decimal import Decimal, ROUND_HALF_UP

    def fmt(v, f):
        if v is None:
            return "–"

        def r(x, q):
            return str(Decimal(str(x)).quantize(Decimal(q), rounding=ROUND_HALF_UP))
        return {"percent": r(v * 100, "1") + "%", "decimal_0": r(v, "1"), "integer": r(v, "1")}.get(f, r(v, "0.1"))

    n = feat.get("yoy_games_played_cutoff") or feat["played"]
    # a table (the site's table element): this season, last season, and a third column with the trend:
    # ▲ green when better than last season, ▼ red when worse (by the metric's direction), – when equal
    css = ('<style>.ctab.yoyt{--cols:minmax(0,1fr) 3.4rem 3.4rem 2.8rem;margin-top:0} .yoyt-head .h{white-space:normal;line-height:1.2} '
           '@container (min-width:420px){.ctab.yoyt{--cols:minmax(0,1fr) 4.6rem 4.6rem 3rem}} .ctab.yoyt .tm .nm{font-weight:400} '
           '.yoyt-sub{display:block;font-size:12px;color:var(--muted);font-weight:400} '
           '.ctab.yoyt .n.now{font-size:15px;font-weight:700;color:var(--ink)} '
           '.ctab.yoyt .n.prev{font-size:15px;color:var(--ink-2)} '
           '.ctab.yoyt .n.tr{font-size:13px;text-align:center;padding-left:0} .tr.up{color:var(--accent)} '
           '.tr.down{color:var(--loss)} .tr.flat{color:var(--muted)} '
           '.yoyt-head{margin-top:6px} .rkgroup > .gh{margin-bottom:26px}</style>')
    out = [css, f'<p class="bsub">Both seasons are compared over their first {n} matches. <a class="mk-chevlink" href="/en/glossary/">Metric Glossary' + CHEV + '</a></p>', fold_open("tf-season"),
           '<div class="ctab yoyt yoyt-head"><div class="ctab-head"><span class="h"></span><span class="h">This season</span>'
           '<span class="h">Last season</span><span class="h" style="text-align:center">Trend</span></div></div>',
           '<div class="yoyt-wrap">']
    missing = []
    for g in groups:
        rows = sorted((r for r in served if r["metric_group"] == g["key"]), key=lambda r: r["metric_order"])
        if not rows:
            continue
        all_t3 = all(TIER.get(r["metric_id"]) == "3" for r in rows)
        out.append(f'<div class="yoyt-sec fxgroup rkgroup{" t3g" if all_t3 else ""}"><div class="gh"><span class="nm">{label("metricGroups.%s.label" % g["key"])}'
                   '</span></div><div class="ctab yoyt">')
        for r in rows:
            key = bind.get(r["metric_id"], r["metric_id"])
            f = "percent" if key.endswith("_pct") else r["format"]
            prev, now = feat.get(f"{key}_prev_season"), feat.get(f"{key}_this_season")
            sub = "per match" if r["per_match"] else ("percentage" if key in share_by_count else "")
            name = label(r["label_i18n_key"]) + (f'<span class="yoyt-sub">{sub}</span>' if sub else "")
            trend = '<span class="n tr flat" aria-label="no change">–</span>'
            if prev is None or now is None:
                missing.append(label(r["label_i18n_key"]) + (f" ({sub})" if sub else ""))
                trend = '<span class="n tr flat"></span>'
            elif fmt(now, f) != fmt(prev, f) and r["direction"] != "neutral":
                if (now > prev) == (r["direction"] == "higher_better"):
                    trend = '<span class="n tr up" aria-label="better than last season">▲</span>'
                else:
                    trend = '<span class="n tr down" aria-label="worse than last season">▼</span>'
            t3 = " t3" if TIER.get(r["metric_id"]) == "3" else ""
            out.append(f'<div class="ctab-row{t3}"><span class="tm"><span class="nm">{name}</span></span>'
                       f'<span class="n now">{fmt(now, f)}</span><span class="n prev">{fmt(prev, f)}</span>{trend}</div>')
        out.append("</div></div>")
    out.append("</div>" + fold_ctl("tf-season", len(served)))
    return "".join(out) + gap(f"{len(missing)} of {len(served)} rows have no value at the same point last season yet: "
                              + ", ".join(missing) + ". The warehouse serves them in this page's build.")


def build_deserved_block(feat, team_name, expl, cap):
    """Deserved points: the six catalogue metrics as league rows, then a scaled scatter of the league."""
    import statistics
    comp = (DIST / "en/bundesliga/index.html").read_text(encoding="utf-8")
    i = comp.index("Deserved points table")
    names = {}
    for r in re.findall(r'<a class="ctab-row".*?</a>', comp[i:comp.index("</section>", i)], re.S):
        nm = re.search(r'<span class="nm">([^<]*)</span>', r).group(1)
        bal, dpts, pts, _ = [float(v.replace("−", "-")) for v in
                             re.findall(r'<span class="n num[^"]*">([^<]*)</span>', r)]
        names.setdefault((round(bal, 1), round(dpts, 1), int(pts)), []).append(html.unescape(nm))
    teams = []
    for d in feat["deserved_scatter"]:
        key = (round(d["sotd"], 1), round(d["deserved"], 1), int(d["points"]))
        pool = names.get(key, [])
        nm = team_name if d["is_self"] else next((x for x in pool if x != team_name), "a Bundesliga team")
        if nm in pool:
            pool.remove(nm)
        teams.append({**d, "name": nm})
    n = len(teams)

    # league rows, the "Vs the league" element: value · rank of n · median; ranks direction-aware
    bench = {b["metric_key"]: b for b in feat["benchmarks"]}

    def row(label, sub, value, rank, median, direction):
        fill = round((n - rank + 1) / n * 100) if direction != "neutral" else 0
        better = (value >= median) if direction == "higher_better" else (value <= median)
        up = " up" if direction != "neutral" and better else ""
        bar = f'<div class="vs-fill{up}" style="width:{fill}%"></div>' if fill else ""
        s = f'<span class="sub">{sub}</span>' if sub else ""
        return (f'<div class="vs-row"> <span class="vs-name">{label}{s}</span> <div class="vs-bar"> {bar} '
                f'<div class="vs-notch"></div> </div> <span class="vs-vr"> <span class="vs-val num">{value_fmt[label](value)}</span> '
                f'<span class="vs-rank">{_ord(rank)} of {n}</span> </span> <span class="vs-medv num">{value_fmt[label](median)}</span> </div>')

    value_fmt = {"Shots on target": lambda v: f"{v:.1f}", "Shots on target against": lambda v: f"{v:.1f}",
                 "Shots on target difference": lambda v: f"{v:+.1f}", "Points": lambda v: f"{v:g}",
                 "Deserved points": lambda v: f"{v:.1f}", "Difference from deserved points": lambda v: f"{v:+.1f}"}
    sotd = bench["shots_on_goal_difference_per_match"]
    pts = [t["points"] for t in teams]
    dps = [t["deserved"] for t in teams]
    gaps = [t["points"] - t["deserved"] for t in teams]
    me = next(t for t in teams if t["is_self"])
    gap_me = me["points"] - me["deserved"]
    # the overview: the site's table element (Table head + striped Table rows), one row per metric
    def trow(label, sub, value, rank, median):
        s = f'<span class="dpm-sub">{sub}</span>' if sub else ""
        return (f'<div class="ctab-row"><span class="tm"><span class="nm">{label}{s}</span></span>'
                f'<span class="n dpm-v">{value_fmt[label](value)}</span></div>')

    rows = ('<style>.ctab.dpm{--cols:minmax(0,1fr) 4.2rem;margin-top:10px} '
            '.ctab.dpm .tm .nm{font-weight:400} .ctab.dpm .n.dpm-v{font-size:15px;font-weight:700;color:var(--ink)} .dpm-sub{display:block;font-size:12px;color:var(--muted);font-weight:400}</style>'
            f'<div class="ctab dpm"><div class="ctab-head"><span class="h" style="text-align:left">Bundesliga, after '
            f'{feat["played"]} matches</span><span class="h"></span></div>'
            + trow("Shots on target difference", "per match", sotd["metric_value"], sotd["rank"], sotd["league_median"])
            + trow("Points", "", me["points"], feat["latest_rank"], statistics.median(pts))
            + trow("Deserved points", "", me["deserved"], feat["deserved_rank"], statistics.median(dps))
            + trow("Difference from deserved points", "", gap_me, feat["deserved_points_gap_rank"], statistics.median(gaps))
            + "</div>")

    # the deserved line: deserved points against shots on target difference across the league
    xs = [t["sotd"] for t in teams]
    mx, my = statistics.mean(xs), statistics.mean(dps)
    slope = sum((x - mx) * (y - my) for x, y in zip(xs, dps)) / sum((x - mx) ** 2 for x in xs)
    icpt = my - slope * mx

    def chart(W, H, fs, cls):
        L, R, T, B = (46 if W > 400 else 34), 14, 12, 58
        x0, x1 = math.floor(min(xs)) - 1, math.ceil(max(xs)) + 1
        y1 = math.ceil((max(pts + dps) + 2) / 3) * 3
        def sx(x):
            return L + (x - x0) / (x1 - x0) * (W - L - R)

        def sy(y):
            return T + (1 - y / y1) * (H - T - B)
        g = []
        # journal style: two axis lines with outward ticks, no grid; a faint reference line at zero difference
        g.append(f'<line x1="{L}" x2="{W - R}" y1="{H - B}" y2="{H - B}" stroke="var(--muted)" stroke-width="1"/>'
                 f'<line x1="{L}" x2="{L}" y1="{T}" y2="{H - B}" stroke="var(--muted)" stroke-width="1"/>')
        for xv in range(x0, x1 + 1):
            if (xv - x0) % 2:
                continue
            g.append(f'<line x1="{sx(xv):.1f}" x2="{sx(xv):.1f}" y1="{H - B}" y2="{H - B + 4}" stroke="var(--muted)" stroke-width="1"/>'
                     f'<text x="{sx(xv):.1f}" y="{H - B + fs + 6}" font-size="{fs}" fill="var(--muted)" text-anchor="middle">{xv:+d}</text>'.replace("+0", "0"))
        for yv in range(0, y1 + 1, 3):
            g.append(f'<line x1="{L - 4}" x2="{L}" y1="{sy(yv):.1f}" y2="{sy(yv):.1f}" stroke="var(--muted)" stroke-width="1"/>'
                     f'<text x="{L - 7}" y="{sy(yv) + fs * 0.35:.1f}" font-size="{fs}" fill="var(--muted)" text-anchor="end">{yv}</text>')
        # the axis title as the site writes a metric: its name, then "per match" on the line under it
        g.append(f'<text x="{(L + W - R) / 2:.1f}" y="{H - 20}" font-size="{fs}" fill="var(--ink-2)" text-anchor="middle">'
                 f'Shots on target difference</text><text x="{(L + W - R) / 2:.1f}" y="{H - 5}" font-size="{fs - 1}" '
                 f'fill="var(--muted)" text-anchor="middle">per match</text>')
        g.append(f'<text transform="translate(13 {(T + H - B) / 2:.1f}) rotate(-90)" font-size="{fs}" fill="var(--ink-2)" text-anchor="middle">Points</text>')
        g.append(f'<line x1="{sx(x0):.1f}" y1="{sy(icpt + slope * x0):.1f}" x2="{sx(x1):.1f}" y2="{sy(icpt + slope * x1):.1f}" '
                 f'stroke="var(--ink-2)" stroke-width="1.5"/>')
        for t in sorted(teams, key=lambda t: t["is_self"]):
            tip = (f'{E(t["name"])} · Shots on target difference {t["sotd"]:+.1f} per match · Points {t["points"]} · '
                   f'Deserved points {t["deserved"]:.1f}')
            if t["is_self"]:
                cx, cy, cl = sx(t["sotd"]), sy(t["points"]), sy(icpt + slope * t["sotd"])
                # journal style: the residual as a thin neutral line from the point to the fitted line, the
                # team as the one solid point, small regular labels beside it
                g.append(f'<line x1="{cx:.1f}" x2="{cx:.1f}" y1="{cy:.1f}" y2="{cl:.1f}" stroke="var(--ink-2)" '
                         f'stroke-width="1" stroke-dasharray="2 2"/>')
                g.append(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="5" data-px="5" data-halo="2" fill="var(--ink)" stroke="var(--page)" paint-order="stroke"><title>{tip}</title></circle>')
                ly = (cy + cl) / 2
                right = cx < (L + W - R) / 2
                lx, anc = (cx + 7, "start") if right else (cx - 7, "end")
                g.append(f'<text x="{lx:.1f}" y="{ly + fs * 0.35:.1f}" font-size="{fs}" fill="var(--ink-2)" text-anchor="{anc}">{gap_me:+.1f}</text>'
                         f'<text x="{lx:.1f}" y="{cy + fs * 0.35:.1f}" font-size="{fs}" fill="var(--ink)" text-anchor="{anc}">{E(t["name"])}</text>')
            else:
                g.append(f'<circle cx="{sx(t["sotd"]):.1f}" cy="{sy(t["points"]):.1f}" r="3" data-px="3" style="fill:color-mix(in srgb,var(--ink) 24%,transparent)"><title>{tip}</title></circle>')
        return (f'<svg class="dp-chart {cls}" viewBox="0 0 {W} {H}" role="img" aria-label="{E(cap)}" '
                f'style="width:100%;height:auto;font-family:inherit">{"".join(g)}</svg>')

    legend = ('<div class="dp-legend"><span><svg width="22" height="8" aria-hidden="true"><line x1="0" y1="4" x2="22" y2="4" '
              'stroke="var(--ink-2)" stroke-width="1.5"/></svg>Deserved points</span>'
              '<span><svg width="10" height="14" aria-hidden="true"><line x1="5" y1="1" x2="5" y2="13" stroke="var(--ink-2)" '
              'stroke-width="1" stroke-dasharray="2 2"/></svg>Difference from deserved points</span>'
              '<span><svg width="10" height="10" aria-hidden="true"><circle cx="5" cy="5" r="5" fill="var(--ink)"/></svg>'
              f'{E(team_name)}</span><span><svg width="10" height="10" aria-hidden="true"><circle cx="5" cy="5" r="3" '
              'style="fill:color-mix(in srgb,var(--ink) 24%,transparent)"/></svg>Other Bundesliga teams</span></div>')
    css = ('<style>.dp-wrap{container-type:inline-size;margin-top:18px} .dp-wrap .dp-wide{display:block} .dp-wrap .dp-narrow{display:none} '
           '@container (max-width:479.98px){.dp-wrap .dp-wide{display:none}.dp-wrap .dp-narrow{display:block}} '
           '.dp-legend{display:flex;flex-wrap:wrap;gap:6px 16px;font-size:12px;color:var(--ink-2);margin:0 0 8px} '
           '.dp-legend span{display:inline-flex;align-items:center;gap:6px} .dp-chart text{font-family:inherit}</style>')
    return (f'<section aria-label="Deserved points">{sechead("Deserved points")}<p class="bsub">{E(expl)} <a class="mk-chevlink" href="/en/glossary/">Metric Glossary{CHEV}</a></p>{rows}'
            f'{css}<div class="dp-wrap">{legend}{chart(560, 330, 12, "dp-wide")}{chart(280, 230, 11, "dp-narrow")}'
            f'</div></section>')


# the scatter's marks stay at their pixel size at every width (the chart standard's shared marks)
DOT_SCRIPT = """<script>(()=>{const fit=()=>document.querySelectorAll('svg.dp-chart').forEach(s=>{
const w=s.getBoundingClientRect().width;if(!w)return;const k=s.viewBox.baseVal.width/w;
s.querySelectorAll('circle[data-px]').forEach(c=>{c.setAttribute('r',c.dataset.px*k);
if(c.dataset.halo)c.setAttribute('stroke-width',c.dataset.halo*2*k);});});
addEventListener('resize',fit);new ResizeObserver(fit).observe(document.body);fit();})();</script>"""


def build():
    h = (DIST / f"en/teams/{SLUG}/index.html").read_text(encoding="utf-8")
    # the header: no control that looks like a filter; the season is plain text at the end of the meta
    # line (one rule for every page showing one season's data; the label comes from the warehouse)
    yr = re.search(r'<span class="yr">([^<]*)</span>', h).group(1)
    h = re.sub(r'\s*<div class="selector">.*?</div>', "", h, count=1, flags=re.S)
    h = re.sub(r'(<div class="meta">.*?)(\s*</div>)', lambda m: m.group(1).rstrip() + f" · Season {yr}" + m.group(2),
               h, count=1, flags=re.S)
    payload = json.loads((DATA / f"teams/{TEAM_ID}.json").read_text(encoding="utf-8"))
    comps = json.loads((DATA / "competitions.json").read_text(encoding="utf-8"))
    idx = {c["league_code"]: c for c in json.loads((DATA / "competition_index.json").read_text(encoding="utf-8"))["competitions"]}
    seasons = payload["seasons"]
    feat = next(s for s in seasons if s["is_featured_season"])
    now = [s for s in seasons if s["season_api_year"] == feat["season_api_year"]]
    me = {"name": payload["name"], "crest": payload["crest"]}

    yoy = grab(h, '<section aria-label="Vs last season">')
    pts, pts_d = re.search(r'<span class="yl">Points</span>\s*<span class="yn num">(-?\d+)</span>\s*'
                           r'<span class="yd num">([+-]?\d+)</span>', yoy).groups()
    pts_d = int(pts_d)
    rk_now = feat["latest_rank"]
    rk_txt = f'{rk_now}{"th" if 10 <= rk_now % 100 <= 20 else {1: "st", 2: "nd", 3: "rd"}.get(rk_now % 10, "th")}'
    # the season so far: standing and points, each against the same point last season (Fact rows)
    yoy_sentence = (f'<section aria-label="Standing">{sechead("Standing")}'
                    + frow("Position", rk_txt, "Season before: –")
                    + frow("Points", pts, f"Season before: {int(pts) - pts_d}")
                    + "</section>"
                    + gap("Position in the season before at the same point: no mart serves it (the payload has this season's latest_rank "
                          "and last season's final rank only). Points in the season before at the same point are served (points_prev_season)."))
    # Deserved points: heading and explainer in the catalogue's metric names (shots on target difference)
    expl = ("Deserved points are the points a team usually earns with its shots on target difference – its shots "
            "on target minus its opponents'. Teams with fewer points than deserved are better than the table shows; "
            "teams with more are worse.")
    # the chart's name for screen readers only: its axes and line, in the metrics' own names
    cap = "Scatter plot: Shots on target difference per match against Points for each Bundesliga team, with the Deserved points line."
    deserved = build_deserved_block(feat, payload["name"], expl, cap)

    def cname(code):
        return (idx.get(code) or {}).get("competition_name") or comps.get(code, {}).get("name") or code

    def cslug(code):
        return (idx.get(code) or {}).get("slug") or ""

    def clogo(code):
        return (idx.get(code) or {}).get("logo_url")

    # upcoming: the Bundesliga's remaining fixtures from the competition payload; other competitions' next match from the team payload
    bl1 = json.loads((DATA / "competitions/BL1/2026.json").read_text(encoding="utf-8"))
    upcoming = {}
    for rnd in bl1["fixtures"]:
        for fx in rnd["fixtures"]:
            if not fx["is_played"] and TEAM_ID in (fx["home"]["team_id"], fx["away"]["team_id"]):
                upcoming.setdefault("BL1", []).append((fx["kickoff"], match_row(fx["home"], fx["away"], fx["kickoff"], fx["slug"])))
    for s in now:
        nf = s.get("next_fixture")
        if s["league_code"] != "BL1" and nf:
            opp = {"name": nf["opponent_name"], "crest": nf["opponent_logo_url"]}
            home, away = (me, opp) if nf["is_home"] else (opp, me)
            upcoming.setdefault(s["league_code"], []).append((nf["kickoff_datetime"], match_row(home, away, nf["kickoff_datetime"])))
    results = sorted(((r["kickoff_datetime"], r, s["league_code"]) for s in now for r in (s.get("recent_results") or [])),
                     key=lambda x: x[0], reverse=True)

    order = {"G": 0, "D": 1, "M": 2, "F": 3, "A": 3}
    names = {0: "Goalkeepers", 1: "Defenders", 2: "Midfielders", 3: "Forwards"}
    squad = [p for p in feat["squad"] if p["appearances"]]
    squad.sort(key=lambda p: (order.get((p["position"] or "?")[0], 4), -p["appearances"], p["name"]))
    sq, last = [], None
    for p in squad:
        g = order.get((p["position"] or "?")[0], 4)
        if g != last:
            sq.append(f'<div class="colhead">{names.get(g, "Other")}</div>')
            last = g
        sq.append(player_row(p))

    sq_groups = {}
    covered = (feat.get("player_stat_coverage_season_games") or 0) >= feat["played"]
    roster = [dict(p, appearances=0) if p["appearances"] is None and covered else p for p in feat["squad"]]
    roster = sorted(roster, key=lambda p: (order.get((p["position"] or "?")[0], 4), -(p["appearances"] or 0), p["name"]))
    for p in roster:
        sq_groups.setdefault(order.get((p["position"] or "?")[0], 4), []).append(player_row(p, stats=False))
    squad_block = ('<section>' + sechead("Squad")
                   + "".join(f'<div class="colhead">{names.get(g, "Other")}</div><div class="sqgrid">{"".join(rows)}</div>'
                             for g, rows in sorted(sq_groups.items()))
                   + "</section>")

    hist = []
    for code in ["BL1"] + sorted({s["league_code"] for s in seasons} - {"BL1"}):
        rows = sorted((s for s in seasons if s["league_code"] == code), key=lambda s: -s["season_api_year"])
        if not rows:
            continue
        league = (idx.get(code) or {}).get("competition_type") == "domestic_league" or code == "BL1"
        hist.append(f'<div class="colhead">{E(cname(code))}</div>' + history_table(rows, league))

    tabs_in = "".join(f'<input type="radio" name="team-tab" id="tab-{k}" class="tab-in"{" checked" if k == "overview" else ""}> '
                      for k, _ in TABS)
    tabs_nav = ('<nav class="tabs comp-tabs" aria-label="Team sections">'
                + "".join(f'<label class="tab" for="tab-{k}">{lbl}</label>' for k, lbl in TABS) + "</nav>")
    comp_page = (DIST / "en/bundesliga/index.html").read_text(encoding="utf-8")

    def excerpt(section_marker):
        sec = balanced(comp_page, comp_page.rindex("<section", 0, comp_page.index(section_marker)))
        rows = re.findall(r'<a class="ctab-row".*?</a>', sec, flags=re.S)
        mine = next(i for i, r in enumerate(rows) if f'/teams/{SLUG}/' in r)
        lo = max(0, min(mine - 2, len(rows) - 5))
        keep = "".join(rows[lo:lo + 5])
        first, last = sec.index('<a class="ctab-row"'), sec.rindex("</a>") + len("</a>")
        return sec[:first] + keep + sec[last:]

    table_x = excerpt('<span class="eyebrow">Table</span>')
    table_x = table_x.replace('<span class="eyebrow">Table</span>', '<span class="eyebrow">Bundesliga table</span>', 1)
    def ordinal_of(n):
        return f'{n}{"th" if 10 <= n % 100 <= 20 else {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")}'

    def link_frow(href, label, value, sub):
        return (f'<a class="frow" href="{href}"><span class="fl">{label}</span><span class="fv"><span class="fvv"><b>{value}</b></span>'
                f'<span class="sub">{sub}</span></span></a>')

    season_rows = []
    sort_order = {r["league_code"]: int(r["sort_order"] or 999) for r in
                  csv.DictReader(open(REPO / "dbt_project/seeds/competition_registry.csv", encoding="utf-8"))}
    def national_first(s):
        return (0 if (s.get("competition_type") or "").startswith("domestic") else 1,
                sort_order.get(s["league_code"], 999), s["league_code"])

    comp_rows = []
    for s in sorted(now, key=national_first):
        code = s["league_code"]
        rk = s.get("latest_rank")
        if rk is None:
            line = f'{s["played"]} played, {s["wins"]} won'
        elif (s.get("competition_type") or "").startswith("domestic"):
            line = f'{ordinal_of(rk)} · {s["points"]} pts after {s["played"]} matches'
        else:
            line = f'{ordinal_of(rk)} in the league phase · {s["points"]} pts'
        comp_rows.append(f'<a class="comp-row" href="/en/{cslug(code)}/">{crest(cname(code), clogo(code))}'
                         f'<span class="comp-meta"><span class="comp-name">{E(cname(code))}</span>'
                         f'<span class="comp-region">{line}</span></span></a>')
        season_rows.append(
            f'<a class="ctab-row" href="/en/{cslug(code)}/"><span class="rk num">{rk if rk is not None else "–"}</span>'
            f'<span class="tm">{crest(cname(code), clogo(code))}<span class="nm">{E(cname(code))}</span></span>'
            f'<span class="n num">{s["played"]}</span><span class="n num wdl">{s["wins"]}</span>'
            f'<span class="n num wdl">{s["draws"]}</span><span class="n num wdl">{s["losses"]}</span>'
            f'<span class="n num wdl">{s["goals_for"]}:{s["goals_against"]}</span>'
            f'<span class="n num gd">{s["goal_diff"]:+d}</span><span class="n num pts">{s["points"]}</span></a>'.replace(">+0<", ">0<"))
    def round_no(name):
        m = re.search(r"(\d+)$", name or "")
        return int(m.group(1)) if m else None

    def chips(s):
        return ('<span class="cchips">' + "".join(f'<span class="cchip {k}">{s[f]} <small>{k}</small></span>'
                                                 for k, f in (("W", "wins"), ("D", "draws"), ("L", "losses"))) + "</span>")

    tc_rows = []
    for s in sorted(now, key=national_first):
        code, ctype = s["league_code"], s.get("competition_type") or ""
        last = (s.get("recent_results") or [{}])[0].get("round_name")
        nf = s.get("next_fixture")
        nums = f'<span class="tc-nums">Goals <b>{s["goals_for"]}:{s["goals_against"]}</b> · Pts <b>{s["points"]}</b></span>'
        if ctype == "domestic_cup" or s.get("latest_rank") is None:
            last_res = (s.get("recent_results") or [{}])[0].get("result")
            ctx = E(nf["round_name"]) if nf else E(last or "")
            if nf:
                right = "Through"
            elif last_res == "W" and (last or "").lower().startswith("final"):
                right = "Winners"
            else:
                right = "Knocked out"
            extra = ""
        elif ctype == "domestic_league":
            right, ctx, extra = ordinal_of(s["latest_rank"]), f"Matchday {round_no(last)}", chips(s) + nums
        else:
            right, ctx, extra = ordinal_of(s["latest_rank"]), "League phase", chips(s) + nums
        words = E(cname(code)).split(" ")
        name_html = " ".join(words[:-1] + [f'<span class="tc-keep">{words[-1]} <span class="tc-ctx">· {ctx}</span></span>'])
        tc_rows.append(
            f'<a class="lrow tc" href="/en/{cslug(code)}/"><div class="tcin"><span class="tc-crest">{crest(cname(code), clogo(code))}</span>'
            f'<span class="tc-name">{name_html}</span><span class="tc-right">{right}</span>'
            f'<span class="tc-extra"><span class="tc-rank2" aria-hidden="true">{right}</span>{extra}</span>'
            + "</div></a>")
    def cell(label, value, span=1):
        st = f' style="grid-column: span {span}"' if span > 1 else ""
        return f'<span class="ts-c"{st}><span class="ts-l">{label}</span><span class="ts-v">{value}</span></span>'

    rows_a, rows_b = [], []
    for s in sorted(now, key=national_first):
        code, ctype = s["league_code"], s.get("competition_type") or ""
        last = (s.get("recent_results") or [{}])[0].get("round_name")
        nf = s.get("next_fixture")
        cup = ctype == "domestic_cup" or s.get("latest_rank") is None
        if cup:
            ctx, rnd = ("Still in" if nf else "Out"), E(nf["round_name"] if nf else (last or ""))
        else:
            ctx = f"Matchday {round_no(last)}" if ctype == "domestic_league" else "League phase"
        words = E(cname(code)).split(" ")
        name_html = " ".join(words[:-1] + [f'<span class="tc-keep">{words[-1]} <span class="tc-ctx">· {ctx}</span></span>'])
        head_a = (f'<span class="tc-crest">{crest(cname(code), clogo(code))}</span><span class="tc-name">{name_html}</span>')
        if cup:
            strip = cell("Round", rnd, 6)
        else:
            strip = (cell("#", s["latest_rank"]) + cell("W", s["wins"]) + cell("D", s["draws"]) + cell("L", s["losses"])
                     + cell("Goals", f'{s["goals_for"]}:{s["goals_against"]}') + cell("Pts", s["points"]))
        rows_a.append(f'<a class="lrow ta" href="/en/{cslug(code)}/"><div class="ta-in">{head_a}<span class="ts">{strip}</span></div></a>')
        right = rnd if cup else ordinal_of(s["latest_rank"])
        line2 = "" if cup else (f'<span class="tb-line"><b>{s["wins"]}</b> W · <b>{s["draws"]}</b> D · <b>{s["losses"]}</b> L'
                                f' · Goals <b>{s["goals_for"]}:{s["goals_against"]}</b> · Pts <b>{s["points"]}</b></span>')
        rows_b.append(f'<a class="lrow tb" href="/en/{cslug(code)}/"><div class="tb-in">{head_a}<span class="tb-right">{right}</span>{line2}</div></a>')

    q1 =(f'<section>{sechead("Competitions")}<div class="tcomps">{"".join(tc_rows)}</div></section>'
          + f'<section>{sechead("Recent matches")}<div class="rlist">{"".join(result_row(r, cname(c), cslug(c)) for _, r, c in results[:5])}</div></section>')

    next_groups = []
    shown = [sorted(upcoming.get(s["league_code"], []))[:3] for s in now]
    soonest = min(k for rows in shown for k, _ in rows)
    for code in list(upcoming):
        upcoming[code] = [(k, r.replace('<span class="when">', '<span class="topmatch">Next</span><span class="when">', 1)
                           if k == soonest else r) for k, r in upcoming[code]]
    for s in sorted(now, key=lambda s: (min([k for k, _ in upcoming.get(s["league_code"], [])] or ["9999"]),
                                        national_first(s))):
        code = s["league_code"]
        rows = sorted(upcoming.get(code, []))
        if rows:
            next_groups.append(comp_group(cname(code), cslug(code), clogo(code),
                                          [(day_head(k), r) for k, r in rows[:1]]))
    q4 = f'<section aria-label="Next matches">{sechead("Next matches")}{"".join(next_groups)}</section>'

    played = []
    for rnd in bl1["fixtures"]:
        for fx in rnd["fixtures"]:
            if fx["is_played"] and TEAM_ID in (fx["home"]["team_id"], fx["away"]["team_id"]):
                home = fx["home"]["team_id"] == TEAM_ID
                gf, ga = (fx["goals_home"], fx["goals_away"]) if home else (fx["goals_away"], fx["goals_home"])
                opp = fx["away"]["name"] if home else fx["home"]["name"]
                played.append((gf, ga, opp, home, "BL1", fx["kickoff"]))
    for s in now:
        if s["league_code"] != "BL1":
            for r in s.get("recent_results") or []:
                played.append((r["goals_for"], r["goals_against"], r["opponent_name"], r["is_home"], s["league_code"], r["kickoff_datetime"]))

    def match_fact(m):
        gf, ga, opp, home, code, k = m
        return f'{gf}–{ga}', f'{"vs" if home else "at"} {E(opp)}, {E(cname(code))}, {short_date(k)}'

    league_matches = sorted((m for m in played if m[4] == "BL1"), key=lambda m: m[5])

    def longest(keep):
        best = run = 0
        for m in league_matches:
            run = run + 1 if keep(m) else 0
            best = max(best, run)
        return best

    wins = [m for m in played if m[0] > m[1]]
    losses = [m for m in played if m[0] < m[1]]
    big_win = sorted(wins, key=lambda m: (-(m[0] - m[1]), -(m[0] + m[1]), m[5]))[0]
    heavy = sorted(losses, key=lambda m: (-(m[1] - m[0]), -(m[0] + m[1]), m[5]))[0]
    q5 = (f'<section>{sechead("Highs and lows")}'
          + frow("Biggest win", *match_fact(big_win))
          + frow("Heaviest defeat", *match_fact(heavy))
          + frow("Longest unbeaten run", f'{longest(lambda m: m[0] >= m[1])} matches', "Bundesliga")
          + frow("Longest winless run", f'{longest(lambda m: m[0] <= m[1])} matches', "Bundesliga")
          + "</section>")

    # Matches tab: competition filter, every upcoming fixture by competition, every result newest first
    comp_order = sorted(now, key=lambda s: (min([k for k, _ in upcoming.get(s["league_code"], [])] or ["9999"]),
                                            national_first(s)))
    codes = [s["league_code"] for s in sorted(now, key=national_first)]
    radios = ('<input class="seg-in" type="radio" name="mf" id="mf-all" checked>'
              + "".join(f'<input class="seg-in" type="radio" name="mf" id="mf-{c}">' for c in codes))
    labels = ["All"] + [cname(c) for c in codes]
    seg = ('<div class="seg mfrow" role="group" aria-label="Filter by competition">'
           '<label class="seg-btn" for="mf-all">All</label>'
           + "".join(f'<label class="seg-btn" for="mf-{c}">{E(cname(c))}</label>' for c in codes) + "</div>"
           + '<div class="seg sel"><select class="sel-in" aria-label="Competition">'
           '<option value="all" selected>All competitions</option>'
           + "".join(f'<option value="{c}">{E(cname(c))}</option>' for c in codes)
           + f'</select>{CHEV}</div>')
    # the switch width, worked out from the labels: ~7.6px per character at 13px bold, 24px
    # padding per button, 8px for the box, plus a 32px safety margin
    switch_px = round(sum(len(lbl) * 7.6 + 24 for lbl in labels) + 8 + 32)
    up_html = "".join(
        comp_group(cname(s["league_code"]), cslug(s["league_code"]), clogo(s["league_code"]),
                   [(day_head(k), r) for k, r in sorted(upcoming.get(s["league_code"], []))],
                   folded=False, attrs=f' data-lc="{s["league_code"]}"')
        for s in comp_order if upcoming.get(s["league_code"]))
    all_results = []
    for rnd in bl1["fixtures"]:
        for fx in rnd["fixtures"]:
            if fx["is_played"] and TEAM_ID in (fx["home"]["team_id"], fx["away"]["team_id"]):
                home = fx["home"]["team_id"] == TEAM_ID
                gf, ga = (fx["goals_home"], fx["goals_away"]) if home else (fx["goals_away"], fx["goals_home"])
                opp = fx["away"] if home else fx["home"]
                all_results.append((fx["kickoff"], {"result": "W" if gf > ga else "L" if gf < ga else "D",
                                                    "goals_for": gf, "goals_against": ga, "opponent_name": opp["name"],
                                                    "opponent_logo_url": opp.get("crest"), "is_home": home,
                                                    "kickoff_datetime": fx["kickoff"]}, "BL1"))
    for s in now:
        if s["league_code"] != "BL1":
            for r in s.get("recent_results") or []:
                all_results.append((r["kickoff_datetime"], r, s["league_code"]))
    all_results.sort(key=lambda x: x[0], reverse=True)
    res_html = "".join(result_row(r, cname(c), cslug(c)).replace('class="lrow"', f'class="lrow" data-lc="{c}"', 1)
                       for _, r, c in all_results)
    on = "background: var(--surface); color: var(--ink); font-weight: 700; box-shadow: 0 1px 3px rgba(0,0,0,.25);"
    wide = "".join(
        f'#mf-{c}:checked ~ .mfb [data-lc]:not([data-lc="{c}"]) {{ display: none; }}'
        f'#mf-{c}:checked ~ .mfrow .seg-btn[for="mf-{c}"] {{ {on} }}' for c in codes) \
        + f'#mf-all:checked ~ .mfrow .seg-btn[for="mf-all"] {{ {on} }} .mfwrap .seg.sel {{ display: none; }}'
    narrow = "".join(
        f'.mfwrap:has(.sel-in option[value="{c}"]:checked) .mfb [data-lc]:not([data-lc="{c}"]) {{ display: none; }}'
        for c in codes) + ' .mfwrap .mfrow { display: none; }'
    filter_css = (f'.mfc {{ container: mfw / inline-size; }} .mfrow .seg-btn {{ flex: 1 1 auto; }}'
                  f'@container mfw (min-width: {switch_px}px) {{ {wide} }}'
                  f'@container mfw (max-width: {switch_px - 0.02}px) {{ {narrow} }}')
    matches_tab = (f'<style>{filter_css}</style><div class="mfc"><div class="mfwrap">{radios}{seg}<div class="mfb">'
                   f'<section>{sechead("Upcoming")}{up_html}</section>'
                   f'<section>{sechead("Results")}<div class="rlist">{res_html}</div></section></div></div></div>'
                   + gap("Upcoming: the sample holds only the next Champions League and DFB-Pokal tie; a full build lists every scheduled one."))

    pages = {
        "overview": q1 + q4 + q5 + squad_block
                    + gap("Biggest win, Heaviest defeat and the two longest runs: no mart serves them per team yet (the runs are computed per team inside mart_competition_season_summary, which serves only the league's longest) (the competition's come from mart_competition_season_summary); the mock picks them from the sample. Cup row: the round reached and Through / Knocked out / Winners must be served by the warehouse (the round phase key, #148); this mock infers them from the next fixture."),
        "matches": matches_tab,
        # Stats: Deserved vs actual first, then the league comparison, then last season, each its
        # own block (no switch between the two comparisons)
        "stats": ('<style>p.bsub a.mk-chevlink { text-decoration: none; font-weight: 600; color: var(--ink); white-space: nowrap; padding-block: 14px; } .mk-chevlink .chev { width: 14px; height: 14px; vertical-align: -2px; margin-left: 3px; } @media (hover: hover) { .mk-chevlink:hover .chev { color: var(--ink-2); transform: translateX(2px); } }</style>' + '<style>.page[data-page="stats"] .pf-league, .page[data-page="stats"] .pf-season { display: block; }</style>'
                  + f'<p class="bsub" style="margin-top:14px">Bundesliga {yr}: {E(payload["name"])} compared with the other teams and with the season before. Other competitions are not included.</p>'
                  + yoy_sentence + deserved
                  + f'<section aria-label="Compared with the league">{sechead("Compared with the league")}'
                  + build_league_rows(feat) + "</section>"
                  + f'<section aria-label="Compared with last season">{sechead("Compared with last season")}'
                  + build_season_bars(feat) + "</section>"),
        "squad": f'<p class="pagecap">Bundesliga · season to date · {len(squad)} players with a match</p>' + "".join(sq),
        "history": f'<section>{sechead("Seasons")}{"".join(hist)}</section>'
                   + gap("All-time and Coach: all-time can count only the seasons held (Bundesliga since 2016/17); no mart serves the coach (it stops at staging)."),
    }
    body = tabs_in + tabs_nav + "".join(f'<div class="page" data-page="{k}">{pages[k]}</div>' for k, _ in TABS)

    start = h.index('<input type="radio" name="team-tab"')
    end = h.index('<div class="footnote">')
    end = h.index("</div>", end) + len("</div>")
    h = h[:start] + body + h[end:]
    h = h.replace('<span class="sep">›</span> <span>Teams</span>',
                  '<span class="sep">›</span> <a class="lnk" href="/en/teams/">Teams</a>', 1)
    h = h.replace("</head>", f"<style>{TAB_CSS}{HARNESS_CSS}</style></head>", 1)
    bar = ('<div class="mockbar">MOCK #134, the team page in three tabs: Overview, Matches, Performance'
           '<span class="note">The built Dortmund page, its blocks moved into three tabs; '
           'new blocks use the site\'s shared rows. Dashed boxes are gaps nothing serves. Data: the committed sample.</span></div>')
    h = re.sub(r"(<body[^>]*>)", lambda m: m.group(1) + bar, h, count=1)
    h = h.replace("</body>", DOT_SCRIPT + "</body>")
    (OUT / "team.html").write_text(h, encoding="utf-8")


if __name__ == "__main__":
    dst = OUT / "_astro"
    if dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(DIST / "_astro", dst)
    build()
    print("ok")
