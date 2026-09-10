"""Render the SITE MAP -- every page type, its URL, and what sits behind one URL without
having its own -- as a standalone HTML overview.

WHY THIS EXISTS: the information is already in the repo, but in four places that do not
agree and none of which is a map.

  docs/site_architecture.md section 3   the planned URL scheme        (no build status)
  docs/content_architecture.md section 4  the tab set per entity      (no URLs)
  docs/wireframes/00_overview.md       screen inventory + spec status (no URLs, stale)
  site_v2/src/pages + src/specs        what actually ships            (the only ground truth)

⚠ DERIVED, NOT TYPED. Almost everything below is read out of the repo at render time, so the
map cannot quietly go stale the way the screen inventory did (it still lists the home page and
the competition hub as "pending"):

  * BUILT routes            <- globbing site_v2/src/pages/**/*.astro
  * each route's contract   <- its src/specs/**/*.spec.json (entity, blocks, seo.links, ...)
  * URL-LESS SWITCHES       <- walking each page's import graph and looking for the `.tab`
                               label + `.seg-btn` radio-toggle markers. This is the answer to
                               "which tabs have no URL", and it is measured, not remembered.
  * PLANNED routes          <- parsing the URL table in site_architecture.md section 3

The ONLY hand-authored part is NOTES below: rulings and design state that no file records in a
machine-readable way. It is kept in one dict, on purpose, so what is asserted rather than
observed is obvious.
"""
import html
import json
import re
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
PAGES = REPO / "site_v2/src/pages"
SPECS = REPO / "site_v2/src/specs"
COMPONENTS = REPO / "site_v2/src/components"
SITE_ARCH = REPO / "docs/site_architecture.md"
SYSTEM_CSS = REPO / "site_v2/src/styles/system.css"
OUT = Path(__file__).with_name("sitemap_overview.html")

E = html.escape

# ------------------------------------------------------- the hand-typed part
#
# Keyed by the section-3 route pattern. `state` is one of:
#   built | designed | planned | ruled-out | deferred
# Everything with no entry here and no built page defaults to "planned".

NOTES = {
    "/{locale}/{competition-slug}/": (
        "designed",
        "Designed 2026-08-10 (this session): next matches, then the table. Both shipped entity "
        "specs already declare <code>inbound_hub: \"competition\"</code>, so this page is an "
        "outstanding promise, not new scope.",
    ),
    "/{locale}/{competition-slug}/{season-slug}/": (
        "planned",
        "Recommended OUT of v1: ~12 competitions x ~10 seasons x 3 locales is ~360 pages of bare "
        "table, and the minimum-data gate (#845) is not built.",
    ),
    "/{locale}/football/{country-slug}/": (
        "ruled-out",
        "RULED OUT 2026-08-10 (#45). CPO: twelve competitions do not need a second browse axis. "
        "The <code>countries</code> export payload is to be deleted, not parked (#44).",
    ),
    "/{locale}/{competition-slug}/table/": (
        "planned",
        "⚠ Its content is the competition hub's second block. Whether this is a SEPARATE URL or a "
        "section of the hub is the open question below.",
    ),
    "/{locale}/{competition-slug}/fixtures/": (
        "planned",
        "⚠ Same question: the hub's first block already carries the next round.",
    ),
    "/{locale}/{competition-slug}/top-scorers/": (
        "planned",
        "The home for league leaderboards. <code>mart_leaderboards</code> already ranks per "
        "league natively and the export already writes nine boards per competition-season.",
    ),
    "/{locale}/players/{player-slug}/": (
        "planned",
        "Overview tab designed and CPO-reviewed (#753 design-state comment is the authority); "
        "Performance and Career not started. ⚠ Its tab set's URL status is UNDECIDED.",
    ),
    "/{locale}/h2h/{teamA}-vs-{teamB}/": (
        "planned",
        "<code>mart_head_to_head</code> exists and is embedded on the fixture page; the standalone "
        "page is deferred (GAP-06). ⚠ site_architecture.md section 5 still calls this mart "
        "\"the one missing mart\" &mdash; stale.",
    ),
    "/{locale}/competitions/": (
        "planned",
        "Screen 08. ⚠ With country hubs ruled out this is a flat list of twelve, which is what "
        "the home page's browse block already is &mdash; so whether it earns a page is open.",
    ),
    "/{locale}/stats/{metric-slug}/": ("planned", "Screen 07, the metric glossary."),
    "/{locale}/": ("built", "Ships two of four specified blocks; Top players and Top teams are "
                            "designed (#40/#41) and unbuilt."),
}

# Routes not in section 3's table but that nest inside the locale tree.
EXTRA_IN_TREE = [
    ("/{locale}/imprint/", "planned", "Legal/imprint page",
     "A v2 BUILD requirement and a publication blocker (#799). No route exists; the exact "
     "path is unchosen."),
]

# Emitted paths that sit OUTSIDE the locale tree entirely.
EXTRA_OUTSIDE = [
    ("/", "redirect", "Astro's i18n root stub. A client-side language redirect, NOT a content "
                      "page: sitemap-excluded, and never the hreflang <code>x-default</code> "
                      "target (that is the <code>en</code> URL)."),
    ("/robots.txt", "built", "Emits <code>Disallow: /</code> while <code>INDEXABLE === false</code>."),
    ("404", "deferred", "Deferred in 09_chrome.md along with the locale-switch mechanism."),
]

# --------------------------------------------------------------- derivation


def route_of(page_path):
    """site_v2/src/pages/[lang]/teams/[team].astro -> /{lang}/teams/{team}/"""
    rel = page_path.relative_to(PAGES).as_posix()
    rel = re.sub(r"\.astro$", "", rel)
    rel = re.sub(r"(^|/)index$", r"\1", rel)
    rel = rel.replace("[", "{").replace("]", "}")
    return "/" + rel if rel.startswith("") else rel


def built_pages():
    out = []
    for p in sorted(PAGES.rglob("*.astro")):
        r = route_of(p)
        if not r.endswith("/"):
            r += "/"
        out.append((r, p))
    return out


def specs_by_page():
    out = {}
    for s in sorted(SPECS.rglob("*.spec.json")):
        d = json.loads(s.read_text(encoding="utf-8"))
        out[d["page"]] = d
    return out


def imports_of(astro_path, depth=0, seen=None):
    """Every .astro this file pulls in, transitively (bounded)."""
    seen = seen if seen is not None else set()
    if depth > 3 or astro_path in seen or not astro_path.exists():
        return seen
    seen.add(astro_path)
    for m in re.finditer(r'import\s+\w+\s+from\s+"([^"]+\.astro)"', astro_path.read_text(encoding="utf-8")):
        imports_of((astro_path.parent / m.group(1)).resolve(), depth + 1, seen)
    return seen


def switches_of(page_path):
    """The URL-LESS controls behind one page: `.tab` labels and `.seg-btn` radio toggles.

    This is the measurement the whole map exists for. Both patterns are pure CSS
    (`:checked` + sibling combinator), so every panel is in the HTML and crawlable, but the
    page has ONE URL: a panel cannot be linked to, cannot rank on its own query, and cannot
    be another page's hub."""
    found = []
    for f in sorted(imports_of(page_path)):
        src = f.read_text(encoding="utf-8")
        if re.search(r'for=\{?[`"]tab-', src) or 'class="tab"' in src:
            names = re.findall(r'\{\s*go:\s*"(\w+)"', src)
            found.append(("tabs", f.name, names))
        if 'class="seg-btn"' in src or "seg-in" in src:
            found.append(("segment", f.name, []))
    return found


def planned_routes():
    """Parse the URL table out of site_architecture.md section 3's first fenced block."""
    txt = SITE_ARCH.read_text(encoding="utf-8")
    sec = txt.split("## 3. URL scheme", 1)[1]
    block = sec.split("```", 2)[1]
    rows = []
    for line in block.splitlines():
        line = line.rstrip()
        if not line.startswith("/"):
            continue
        parts = re.split(r"\s{2,}", line.strip(), maxsplit=1)
        rows.append((parts[0], parts[1] if len(parts) > 1 else ""))
    return rows


# ------------------------------------------------------------------- render

BADGE = {
    "built": ("BUILT", "b-built"),
    "designed": ("DESIGNED", "b-designed"),
    "planned": ("PLANNED", "b-planned"),
    "ruled-out": ("RULED OUT", "b-out"),
    "deferred": ("DEFERRED", "b-out"),
    "redirect": ("REDIRECT", "b-planned"),
}


def badge(state):
    text, cls = BADGE[state]
    return '<span class="badge %s">%s</span>' % (cls, text)


def build():
    built = built_pages()
    specs = specs_by_page()
    planned = planned_routes()

    # route pattern (section 3) -> the built page that serves it, matched by shape
    def norm(r):
        """Compare routes by SHAPE: any path segment containing a parameter collapses to one
        slot. ⚠ Collapsing each `{...}` individually is not enough -- section 3 writes the
        fixture segment as `{date}-{home}-vs-{away}` against the template's single `{fixture}`,
        so a per-brace substitution leaves `{}-{}-vs-{}` and the built fixture page silently
        reads as PLANNED. It did, and the first version of check 1 passed anyway on a matching
        count."""
        segs = [("{}" if "{" in s else s) for s in r.strip("/").split("/")]
        return "/" + "/".join(segs) + "/"

    built_by_norm = {norm(r): (r, p) for r, p in built}

    rows = []
    for pattern, desc in planned:
        key = norm(pattern)
        hit = built_by_norm.get(key)
        state, note = NOTES.get(pattern, (None, ""))
        if state is None:
            state = "built" if hit else "planned"
        rows.append((pattern, desc, state, note, hit))

    # section-3 patterns already covered; anything BUILT and not in section 3 is a surprise
    covered = {norm(p) for p, _d in planned}
    orphan_built = [(r, p) for r, p in built if norm(r) not in covered and r != "/"]

    for pattern, state, desc, note in EXTRA_IN_TREE:
        rows.append((pattern, desc, state, note, None))

    # ---------------------------------------------------------------- tree
    #
    # A REAL TREE, nested by URL SEGMENT -- which is the hierarchy a crawler actually walks,
    # and is derived rather than arranged by hand. Tabs and segment toggles hang off their
    # page as leaves so "what has no URL of its own" is visible in place rather than in a
    # separate table.
    node_html = {}
    for pattern, desc, state, note, hit in rows:
        spec, switches = None, []
        if hit:
            _r, page_path = hit
            spec = specs.get(page_path.relative_to(PAGES).as_posix())
            switches = switches_of(page_path)

        detail = []
        if spec:
            links = spec["seo"]["links"]
            detail.append("<b>Blocks</b> (%d): %s"
                          % (len(spec["blocks"]), E(", ".join(b["block"] for b in spec["blocks"]))))
            detail.append("hub <code>%s</code> &rarr; %s"
                          % (E(links["inbound_hub"]),
                             ", ".join("<code>%s</code>" % E(o) for o in links["outbound"]) or "&mdash;"))
        if note:
            detail.append('<span class="note">%s</span>' % note)

        # tabs / segments become CHILD LEAVES of the page they live on
        leaves = []
        for kind, fname, names in switches:
            if kind == "tabs":
                for n in names:
                    leaves.append(("tab", n, fname))
            else:
                leaves.append(("segment", "two panels", fname))

        node_html[tuple(pattern.strip("/").split("/"))] = (pattern, state, desc, detail, leaves)

    # ------------------------------------------------- nest by URL segment
    keys = set(node_html)

    def parent_of(k):
        """The longest proper prefix that is itself a node; () otherwise. Intermediate
        segments that are not pages of their own (e.g. `football/`) collapse into the child's
        label rather than inventing a node that does not exist."""
        for i in range(len(k) - 1, 0, -1):
            if k[:i] in keys:
                return k[:i]
        return ()

    kids = {}
    for k in sorted(keys):
        kids.setdefault(parent_of(k), []).append(k)

    # Reading order is NAVIGATIONAL, not status-ordered: a tree is read as a walk of the site,
    # and sorting by state put /teams/ above the competition hub, which is not how anyone
    # traverses it. Decided-against branches sink to the bottom of their level.
    HINT = {"{competition-slug}": 0, "competitions": 1, "teams": 2, "players": 3,
            "h2h": 4, "stats": 5, "imprint": 6, "football": 9,
            "table": 0, "fixtures": 1, "top-scorers": 2, "matches": 3, "{season-slug}": 4}
    DEAD = {"ruled-out", "deferred"}

    def render(parent):
        def sort_key(x):
            seg = x[len(parent)]
            return (node_html[x][1] in DEAD, HINT.get(seg, 50), x)

        out = []
        for k in sorted(kids.get(parent, []), key=sort_key):
            pattern, state, desc, detail, leaves = node_html[k]
            label = "/" + "/".join(k[len(parent):]) + "/"
            body = (
                '<li class="n %s"><code class="u">%s</code> %s'
                '<span class="full">%s</span>'
                '<span class="desc">%s</span>%s'
                % (state, E(label), badge(state), E(pattern), E(desc),
                   ('<ul class="d">%s</ul>' % "".join("<li>%s</li>" % d for d in detail))
                   if detail else "")
            )
            sub = []
            for kind, name, fname in leaves:
                sub.append('<li class="leaf %s"><span class="mark">%s</span>'
                           '<span class="lname">%s</span>'
                           '<span class="nourl">no own URL</span>'
                           '<span class="src">%s</span></li>'
                           % (kind, "tab" if kind == "tab" else "switch", E(name), E(fname)))
            sub.append(render(k))
            sub = "".join(s for s in sub if s)
            out.append(body + ('<ul>%s</ul>' % sub if sub else "") + "</li>")
        return "".join(out)

    tree = [render(())]

    # -------------------------------------------------- behind-one-URL table
    behind = []
    for r, p in built:
        for kind, fname, names in switches_of(p):
            behind.append((r, kind, fname, names))
    behind_rows = "".join(
        "<tr><td><code>%s</code></td><td>%s</td><td>%s</td><td><code>%s</code></td></tr>"
        % (E(r), E(kind), ", ".join(E(n) for n in names) or "&mdash;", E(fname))
        for r, kind, fname, names in behind
    )

    outside = "".join(
        '<li class="n %s"><code class="u">%s</code> %s'
        '<ul class="d"><li><span class="note">%s</span></li></ul></li>' % (state, E(route), badge(state), note)
        for route, state, note in EXTRA_OUTSIDE
    )

    orphan = ("".join("<li><code>%s</code> &mdash; built but absent from section 3</li>" % E(r)
                      for r, _p in orphan_built)
              or "<li>none &mdash; every built route appears in the URL scheme</li>")

    return """<!doctype html>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Matchday Pilot -- site map</title>
<style>
%s
%s
</style>
<div class="fx">
<div class="wrap">

  <h1>Site map</h1>
  <p class="sub">Every page type, its URL, and what sits behind one URL without having its
     own. Statuses, blocks, link graph and the URL-less switches are <b>read out of the repo
     at render time</b>; only the italic notes are hand-written.</p>

  <div class="key">
    %s one or more pages ship today
    %s agreed design, nothing built
    %s in the URL scheme, no design
    %s decided against
  </div>

  <h2>The tree</h2>
  <p class="sub">Nested by URL segment &mdash; the hierarchy a crawler walks. Tabs and switch
     panels hang off the page they live on, so what has no URL of its own is visible in place.</p>
  <ul class="tree">
%s
  </ul>

  <h3>Outside the locale tree</h3>
  <ul class="tree flat">
%s
  </ul>

  <h2>Behind one URL</h2>
  <p class="sub">Both mechanisms are pure CSS (<code>:checked</code> + sibling combinator), so
     every panel <b>is</b> in the HTML and crawlable. But the page has one URL, so a panel
     cannot be linked to, cannot rank on its own query, and cannot be another page's hub.</p>
  <table>
    <tr><th>Route</th><th>Control</th><th>Panels</th><th>Component</th></tr>
%s
  </table>

  <h2>Built routes missing from the URL scheme</h2>
  <ul class="plain">%s</ul>

  <h2 class="q">The question this map exposes</h2>
  <p class="sub"><b>The two entity types model tabs incompatibly, and nobody has ruled which
     is right.</b> The team page puts Overview / Performance / Squad behind one URL. The
     competition, per section 3, gets a separate URL per tab
     (<code>/table/</code>, <code>/fixtures/</code>, <code>/top-scorers/</code>). The player
     page's tab set is undecided. Three entity types, three answers.</p>
  <p class="sub">It is not a cosmetic choice: a URL-less panel cannot be a hub, and
     <code>inbound_hub</code> is the field every page spec must declare. Deciding it is
     upstream of the internal-linking rule (#45), not downstream.</p>

</div>
</div>
""" % (SYSTEM_CSS.read_text(encoding="utf-8"), PAGE_CSS,
       badge("built"), badge("designed"), badge("planned"), badge("ruled-out"),
       "\n".join(tree), outside, behind_rows, orphan)


PAGE_CSS = """
body { margin: 0; background: #06070a; }
.wrap { max-width: 900px; margin: 0 auto; padding: 28px clamp(16px, 4vw, 28px) 60px; }
h1 { font-size: 26px; margin: 0 0 6px; }
h2 { font-size: 16px; margin: 38px 0 10px; padding-bottom: 7px; border-bottom: 1px solid var(--div); }
h2.q { color: var(--ink); }
.sub { font-size: 13.5px; color: var(--ink-2); line-height: 1.65; margin: 0 0 6px; }
code { font-family: ui-monospace, SFMono-Regular, Menlo, monospace; font-size: 12.5px; }
code.u { color: var(--ink); font-weight: 600; }
.key { display: flex; flex-wrap: wrap; gap: 8px 16px; margin: 16px 0 0; font-size: 12px; color: var(--muted); align-items: center; }
.badge { display: inline-block; font-size: 10px; font-weight: 700; letter-spacing: .08em;
         padding: 2px 7px; border-radius: 4px; border: 1px solid var(--div); color: var(--muted); }
.b-built { border-color: var(--win); color: var(--win); }
.b-designed { border-color: var(--ink-2); color: var(--ink); }
.b-planned { border-color: var(--div); color: var(--muted); }
.b-out { border-color: var(--loss); color: var(--loss); }

/* ---------------------------------------------------------------- *
 *  THE TREE. Nested <ul>; the connectors are drawn, not typed --     *
 *  `li::before` is the elbow (down from the parent, then across to   *
 *  the row) and `li::after` continues the trunk past this row to the *
 *  next sibling. `:last-child` drops the trunk, which is what makes  *
 *  the branch visibly END rather than running into whitespace.       *
 *  The elbow is anchored in `em`, not `%`, so a row with two lines   *
 *  of detail keeps its connector on the FIRST line.                  *
 * ---------------------------------------------------------------- */
ul.tree, ul.tree ul { list-style: none; margin: 0; padding: 0; }
ul.tree { margin-top: 14px; }
ul.tree ul { padding-left: 26px; }
ul.tree li { position: relative; padding: 7px 0 7px 20px; }
ul.tree ul > li::before {
  content: ""; position: absolute; left: -14px; top: 0;
  width: 20px; height: 1.35em;
  border-left: 1px solid var(--div); border-bottom: 1px solid var(--div);
  border-bottom-left-radius: 4px;
}
ul.tree ul > li::after {
  content: ""; position: absolute; left: -14px; top: 1.35em; bottom: 0;
  border-left: 1px solid var(--div);
}
ul.tree ul > li:last-child::after { display: none; }
/* the state stripe sits on the row itself, inside the connector gutter */
ul.tree li.n > code.u { border-left: 3px solid var(--line); padding-left: 9px; margin-left: -12px; }
li.n.built > code.u { border-left-color: var(--win); }
li.n.designed > code.u { border-left-color: var(--ink-2); }
li.n.ruled-out > code.u, li.n.deferred > code.u { border-left-color: var(--loss); }
li.n.ruled-out, li.n.deferred { opacity: .68; }
ul.tree.flat ul.d { padding-left: 0; }
ul.tree.flat > li::before, ul.tree.flat > li::after { display: none; }

li.n .full { font-size: 11px; color: var(--muted); font-family: ui-monospace, monospace;
             margin-left: 9px; opacity: .65; }
li.n .desc { display: block; font-size: 12px; color: var(--muted); margin-top: 3px; }
ul.d { list-style: none; padding: 0; margin: 6px 0 0; }
ul.d > li { font-size: 12px; color: var(--ink-2); line-height: 1.55; padding: 1px 0; }
ul.d > li::before, ul.d > li::after { display: none; }
ul.d b { color: var(--ink); font-weight: 600; }

/* a tab / switch panel: a child of the page, but NOT a URL */
li.leaf { font-size: 12.5px; color: var(--ink-2); }
li.leaf .mark { display: inline-block; min-width: 46px; font-size: 10px; font-weight: 700;
                letter-spacing: .07em; text-transform: uppercase; color: var(--muted); }
li.leaf .lname { color: var(--ink); font-weight: 600; }
.nourl { font-size: 10px; font-weight: 700; letter-spacing: .05em; color: var(--loss);
         border: 1px solid var(--loss); border-radius: 4px; padding: 1px 5px; margin-left: 8px; }
.src { color: var(--muted); font-size: 11px; margin-left: 8px; }
.note { color: var(--muted); font-style: italic; }
ul.plain { margin: 8px 0 0; padding-left: 18px; font-size: 13px; color: var(--ink-2); line-height: 1.7; }

table { width: 100%; border-collapse: collapse; margin-top: 12px; }
th { text-align: left; font-size: 11px; letter-spacing: .06em; text-transform: uppercase;
     color: var(--muted); padding: 0 10px 8px 0; border-bottom: 1px solid var(--div); }
td { font-size: 13px; color: var(--ink-2); padding: 9px 10px 9px 0; border-bottom: 1px solid var(--line); }
"""


if __name__ == "__main__":
    OUT.write_text(build(), encoding="utf-8")
    print("  wrote %s (%.0f KB)" % (OUT.name, OUT.stat().st_size / 1024))
