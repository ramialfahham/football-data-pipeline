"""Verify sitemap_overview.html was DERIVED correctly, not merely rendered.

The map's whole value is that its statuses come from the repo. So the checks below compare
the emitted HTML against the repo a second time, by a different route than the generator used.
"""
import json
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

HERE = Path(__file__).parent
DOC = (HERE / "sitemap_overview.html").read_text(encoding="utf-8")
REPO = Path(__file__).resolve().parent.parent
PAGES = REPO / "site_v2/src/pages"
SPECS = REPO / "site_v2/src/specs"

FAILS = []


def ok(m):
    print("  PASS  %s" % m)


def bad(m, d):
    FAILS.append(m)
    print("  FAIL  %s\n        %s" % (m, d))


TREE = DOC.split("<h2>The tree</h2>", 1)[1].split("<h2>Behind one URL</h2>", 1)[0]
# <code class="u"> holds the relative label; checks key on the full route in <span class="full">.
NODE = re.compile(
    r'<li class="n ([a-z-]+)"><code class="u">([^<]+)</code> '
    r'<span class="badge [^"]+">([A-Z][A-Z ]*)</span>'
    r'<span class="full">([^<]*)</span>'
)
NODES = [(st, full, lab.strip(), label) for st, label, lab, full in NODE.findall(TREE)]


def show():
    for st, full, lab, label in NODES:
        # the label is the tail added to the parent, so the separator difference is the depth
        depth = max(0, full.count("/") - label.count("/"))
        print("    %-10s %s%s" % (lab, "   " * depth, label))


def check_every_built_page_shows_built():
    """Every page with a spec must be marked BUILT in the tree, matched by first-block signature."""
    for s in sorted(SPECS.rglob("*.spec.json")):
        d = json.loads(s.read_text(encoding="utf-8"))
        blocks = d.get("blocks") or []
        if not blocks:
            continue
        signature = blocks[0]["block"]
        node = None
        for st, full, _lab, _label in NODES:
            chunk = TREE.split('<span class="full">%s</span>' % full, 1)
            if len(chunk) > 1 and signature in chunk[1].split("</li>", 1)[0]:
                node = (st, full)
                break
        if node is None:
            return bad("built pages all marked BUILT",
                       "%s (entity %s) has no node carrying its first block %r"
                       % (s.name, d["entity"], signature))
        if node[0] != "built":
            return bad("built pages all marked BUILT",
                       "%s (entity %s) renders at %s but the map says %s"
                       % (s.name, d["entity"], node[1], node[0].upper()))
    ok("built pages all marked BUILT (%d specs matched by block signature)"
       % len(list(SPECS.rglob("*.spec.json"))))


def check_specs_are_quoted_faithfully():
    for s in SPECS.rglob("*.spec.json"):
        d = json.loads(s.read_text(encoding="utf-8"))
        hub = d["seo"]["links"]["inbound_hub"]
        needle = "hub <code>%s</code>" % hub
        if needle not in DOC:
            return bad("specs quoted faithfully",
                       "%s declares inbound_hub %r; the map does not say so" % (s.name, hub))
    ok("specs quoted faithfully (inbound_hub matches every spec on disk)")


def check_url_less_switches_found():
    """Cross-checks by grepping the component tree, not by the generator's import-graph walk."""
    comp = REPO / "site_v2/src/components"
    expect = set()
    for f in comp.rglob("*.astro"):
        src = f.read_text(encoding="utf-8")
        if 'class="tab"' in src or 'class="seg-btn"' in src:
            expect.add(f.name)
    table = DOC.split("<h2>Behind one URL</h2>", 1)[1].split("</table>", 1)[0]
    got = set(re.findall(r"<td><code>([\w.]+\.astro)</code></td>", table))
    if got != expect:
        return bad("URL-less switches found",
                   "grep says %s, the map says %s" % (sorted(expect), sorted(got)))
    ok("URL-less switches found (%s)" % ", ".join(sorted(got)))


def check_ruled_out_is_marked():
    node = [n for n in NODES if "country-slug" in n[1]]
    if not node:
        return bad("country hub marked ruled out", "no country-hub node in the tree at all")
    if node[0][0] != "ruled-out":
        return bad("country hub marked ruled out", "marked %r" % node[0][0])
    ok("country hub marked RULED OUT")


def check_tree_is_actually_nested():
    body = TREE.split('<ul class="tree">', 1)[1]
    depth, maxdepth = 0, 0
    for tok in re.finditer(r"<(/?)ul\b", body):
        depth += -1 if tok.group(1) else 1
        maxdepth = max(maxdepth, depth)
    # the outer `<ul class="tree">` is already split off; a flat list of siblings scores 0-1
    if maxdepth < 3:
        return bad("tree is nested",
                   "max <ul> nesting below the root is %d; a real tree needs "
                   "locale > competition > matches > panel" % maxdepth)
    comp = TREE.split('<span class="full">/{locale}/{competition-slug}/</span>', 1)
    if len(comp) < 2 or "/table/" not in comp[1].split('<span class="full">/{locale}/teams/', 1)[0]:
        return bad("tree is nested", "/table/ is not rendered inside the competition node")
    ok("tree is nested (max depth %d, competition children are inside it)" % maxdepth)


def check_no_stale_pending_claim():
    home = [n for n in NODES if n[1].rstrip("/") in ("/{locale}", "/{lang}")]
    if not home or home[0][0] != "built":
        return bad("home not called pending", "home node is %s" % (home or "missing"))
    hub = [n for n in NODES if n[1] == "/{locale}/{competition-slug}/"]
    if not hub or hub[0][0] != "designed":
        return bad("hub marked designed", "hub node is %s" % (hub or "missing"))
    ok("home is BUILT and the hub is DESIGNED (not inherited as 'pending')")


def prove_check_1_fires():
    """Marks the fixture page PLANNED and asserts check 1 rejects it."""
    global TREE, NODES
    orig_tree, orig_nodes, before = TREE, NODES, len(FAILS)
    TREE = TREE.replace('<li class="n built"><code class="u">/matches/',
                        '<li class="n planned"><code class="u">/matches/')
    if TREE == orig_tree:
        raise SystemExit("FATAL: could not find the BUILT fixture node to break.")
    NODES = [(st, full, lab.strip(), label) for st, label, lab, full in NODE.findall(TREE)]
    try:
        check_every_built_page_shows_built()
    finally:
        TREE, NODES = orig_tree, orig_nodes
    if len(FAILS) == before:
        raise SystemExit("FATAL: check 1 stayed GREEN with the fixture page marked PLANNED.")
    FAILS.pop()
    print("  (check 1 correctly went RED on the fixture page reading PLANNED)")


if __name__ == "__main__":
    print("sitemap_overview.html")
    show()
    print()
    check_every_built_page_shows_built()
    check_specs_are_quoted_faithfully()
    check_url_less_switches_found()
    check_tree_is_actually_nested()
    check_ruled_out_is_marked()
    check_no_stale_pending_claim()
    print("negative control")
    prove_check_1_fires()
    if FAILS:
        sys.exit("\n%d CHECK(S) FAILED: %s" % (len(FAILS), ", ".join(FAILS)))
    print("\nall checks pass")
