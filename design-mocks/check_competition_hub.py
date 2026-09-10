"""Checks for competition_hub_mock.html.

Each asserts a rule the DESIGN depends on, not merely that a file was produced.

Run `python gen_competition_hub.py` first.

Check 1 exists because the defect it catches was actually written: the first draft gave the
crest its own grid track, leaving 9 tracks against 8 cells at the wide breakpoint AND hiding
the crest at desktop. `prove_check_fails()` at the bottom reconstructs that CSS and asserts
the check goes RED on it -- a check only ever seen green proves nothing.
"""
import re
import sys
from pathlib import Path

HTML = Path(__file__).with_name("competition_hub_mock.html")
import gen_competition_hub as G   # noqa: E402  (the mock's own data is the expectation)

DOC = HTML.read_text(encoding="utf-8")
FAILS = []


def ok(name):
    print("  PASS  %s" % name)


def bad(name, detail):
    FAILS.append(name)
    print("  FAIL  %s\n        %s" % (name, detail))


# ------------------------------------------------------------------ helpers

def stage_html():
    """The rendered PAGE only -- `.stage` -- with the sticky toggle bar and the legend cut off.
    Those two are the mock's review harness and say things ABOUT the page that must not be
    read as part of it."""
    start = DOC.index('<div class="stage">')
    end = DOC.index('<div class="legend">')
    return DOC[start:end]


def track_lists(css):
    """The two `--cols` declarations on `.ctab`, narrow first.

    ⚠ SCOPED TO `.ctab` BLOCKS. A bare `--cols:` search also picks up `.bgrid`'s, which the
    scorers board declares -- the first version found three and failed for the wrong reason,
    which would have made the negative control below meaningless."""
    blocks = re.findall(r"\.ctab\s*\{([^}]*)\}", css)
    out = []
    for b in blocks:
        m = re.search(r"--cols:\s*([^;]+);", b)
        if m:
            out.append(m.group(1).strip())
    return out


def n_tracks(decl):
    """Count grid tracks in a template string, treating `minmax(a, b)` as ONE track --
    a naive split on whitespace counts its comma-separated arguments as extra tracks."""
    flat = re.sub(r"\w+\([^)]*\)", "T", decl)
    return len(flat.split())


def count_cells(row_html, hidden_class=None):
    """Visible direct-child cells of one grid row."""
    cells = re.findall(r'<(?:span|a|div)\s+class="([^"]*)"', row_html)
    top = []
    depth = 0
    # the team cell is an <a> that CONTAINS two spans; count only depth-0 children
    for tok in re.finditer(r"<(/?)(span|a|b)\b[^>]*?(/?)>", row_html):
        closing = tok.group(1)
        if not closing:
            if depth == 0:
                cls = re.search(r'class="([^"]*)"', tok.group(0))
                top.append(cls.group(1) if cls else "")
            depth += 1
        else:
            depth -= 1
    del cells
    if hidden_class:
        top = [c for c in top if hidden_class not in c.split()]
    return len(top)


# ------------------------------------------------------------------- checks

def check_track_parity(css=None):
    """1. Grid track count == visible cell count, at BOTH breakpoints, for the head AND a row."""
    css = G.MOCK_CSS if css is None else css
    decls = track_lists(css)
    if len(decls) != 2:
        return bad("table track parity", "expected 2 `--cols` declarations, found %d" % len(decls))
    narrow, wide = (n_tracks(d) for d in decls)

    row = re.search(r'<div class="ctab-row">.*?</div>\s*(?=<div class="ctab-row"|\n)', DOC, re.S)
    head = re.search(r'<div class="ctab-head">.*?(?=<div class="ctab-row")', DOC, re.S)
    if not row or not head:
        return bad("table track parity", "could not locate a .ctab-row / .ctab-head in the HTML")

    for what, frag in (("row", row.group(0)), ("head", head.group(0))):
        vis_wide = count_cells(frag)
        vis_narrow = count_cells(frag, hidden_class="wdl")
        if vis_wide != wide:
            return bad("table track parity",
                       "wide: %d tracks (%s) but %d visible %s cells" % (wide, decls[1], vis_wide, what))
        if vis_narrow != narrow:
            return bad("table track parity",
                       "narrow: %d tracks (%s) but %d visible %s cells" % (narrow, decls[0], vis_narrow, what))
    ok("table track parity (narrow %d/%d, wide %d/%d)" % (narrow, narrow, wide, wide))


def check_crest_survives_both_widths():
    """2. The crest is on every table row at BOTH widths -- the CPO ruled every row carries it."""
    if re.search(r"\.ctab[^{]*\.crest[^{]*\{[^}]*display:\s*none", G.MOCK_CSS):
        return bad("crest on every row", "a rule hides the table crest at some width")
    rows = re.findall(r'<div class="ctab-row">.*?</span></div>', DOC, re.S)
    missing = [i for i, r in enumerate(rows, 1) if 'class="crest xs"' not in r]
    if missing:
        return bad("crest on every row", "rows without a crest: %s" % missing)
    ok("crest on every row (%d rows, no width-conditional hide)" % len(rows))


def check_every_team_links():
    """3. THE HUB'S WHOLE JOB. Both shipped specs declare inbound_hub "competition", so every
    team in the table must be an anchor to its page -- otherwise the declaration is false."""
    hrefs = set(re.findall(r'<a class="tm" href="(/en/teams/[^"]+)"', DOC))
    if len(hrefs) != len(G.TABLE):
        return bad("every team is a link",
                   "%d distinct team links for %d table rows" % (len(hrefs), len(G.TABLE)))
    ok("every team is a link (%d/%d distinct hrefs)" % (len(hrefs), len(G.TABLE)))


def check_only_the_next_round():
    """4. The hub carries the NEXT ROUND AND NOTHING ELSE (CPO 2026-08-10). Past matches belong
    on the competition's own results page.

    This replaced a check that counted played rows and asserted they were inert. The rule
    changed underneath it: there are no played rows to be inert."""
    upcoming = re.findall(r'<a class="fxrow" href="[^"]*">', DOC)
    played = re.findall(r'<(?:a|div) class="fxrow played"', DOC)
    if len(upcoming) != len(G.NEXT_ROUND[2]):
        return bad("only the next round",
                   "%d upcoming anchors for %d fixtures" % (len(upcoming), len(G.NEXT_ROUND[2])))
    if played:
        return bad("only the next round",
                   "%d played row(s) on the hub -- they belong on the results page" % len(played))
    for trace in ("Latest results", "Viimeisimm", "Matchday 24"):
        if trace in DOC:
            return bad("only the next round",
                       "the cut results group left %r behind" % trace)
    ok("only the next round (%d upcoming, 0 played, no trace of the cut group)" % len(upcoming))


def check_cut_block_left_no_trace():
    """5. THE CUT LEAVES NOTHING BEHIND. A top-scorers board was in the first draft and was
    removed; "a deleted module leaves traces that do not carry its name" fired five times on
    !27, so sweep by CONCEPT -- the row component, the board grid, the catalogue machinery
    that existed only to name it, and the section heading key."""
    # ⚠ SCANNED WITH COMMENTS STRIPPED, and narrowed rather than dropped. The first version
    # fired on a CSS comment that names `.brow` to explain why a league table is NOT that
    # component -- a justification, not a leftover. A live `.brow { ... }` rule or an emitted
    # class still trips this; prose no longer does. Verified: system.css contains none of
    # these needles, so a hit can only come from this mock.
    def code_only(blob):
        return re.sub(r"<!--.*?-->", "", re.sub(r"/\*.*?\*/", "", blob, flags=re.S), flags=re.S)

    # ...and scoped to the PAGE, not the review harness. `.ctl` and `.legend` are the mock's
    # own scaffolding, and the legend's job is to SAY the board was cut and why -- scanning it
    # made the check fire on its own explanation.
    page = stage_html()

    # ⚠ A CLASS NEEDLE MUST BE MATCHED AS A TOKEN, NOT A SUBSTRING, on BOTH sides. In CSS the
    # leftover reads `.brow`; in HTML it reads `class="brow"`, so a `.brow` substring scan of
    # the markup can never hit -- the negative control below caught exactly that. And dropping
    # the dot to compensate collides with `eyebrow`, which is a live class on this page. So
    # class needles are checked against the page's parsed class-token SET.
    page_classes = set()
    for attr in re.findall(r'class="([^"]*)"', code_only(page)):
        page_classes.update(attr.split())

    for needle, why in ((".brow", "board row component"),
                        (".bgrid", "board grid"),
                        (".bhd", "board head"),
                        ("metric_catalogue", "catalogue lookup"),
                        ("label_en", "catalogue label field"),
                        ("scorer", "the block's own name"),
                        ("Top scorers", "the section heading")):
        if needle.startswith("."):
            if needle in code_only(G.MOCK_CSS):
                return bad("cut block left no trace",
                           "%r (%s) still has a rule in the generator" % (needle, why))
            if needle[1:] in page_classes:
                return bad("cut block left no trace",
                           "class %r (%s) is still emitted in the page" % (needle[1:], why))
            continue
        for where, blob in (("generator", code_only(G.MOCK_CSS)), ("page", code_only(page))):
            if needle.lower() in blob.lower():
                return bad("cut block left no trace",
                           "%r (%s) still present in the %s" % (needle, why, where))
    if "secScorers" in G.COPY:
        return bad("cut block left no trace", "COPY still carries the secScorers key")
    ok("cut block left no trace (row component, board grid, catalogue machinery, copy key)")


def check_names_never_truncate():
    """6. system.css ellipsises `.nm`. The one surface that carries an entity name in a
    constrained cell must override it -- a clipped name defeats a page whose purpose is to
    send people to that entity."""
    sel = r"\.ctab \.tm \.nm"
    block = re.search(sel + r"\s*\{([^}]*)\}", G.MOCK_CSS)
    if not block:
        return bad("names never truncate", "no override block for %s" % sel)
    body = block.group(1)
    for prop in ("white-space: normal", "text-overflow: clip", "overflow: visible"):
        if prop not in body:
            return bad("names never truncate", "%s is missing `%s`" % (sel, prop))
    ok("names never truncate (.ctab overrides the system ellipsis)")


def check_no_external_fetch_and_no_js():
    """7. The review surface is a static snapshot with no network: script never runs, and a
    hotlinked crest (#36) would render as a broken image."""
    for needle, why in (("<script", "script never runs on the review surface"),
                        ("<img", "no image may be fetched"),
                        ("media.api-sports.io", "crests must not be hotlinked (#36)"),
                        ("http://", "no external reference"),
                        ("https://", "no external reference")):
        if needle in DOC:
            return bad("no script, no external fetch", "%r present -- %s" % (needle, why))
    ok("no script, no external fetch")


def check_probe_marking():
    """8. Every Finnish string that does NOT exist in strings.ts must be marked as a probe, or
    the mock reads as if the copy were approved."""
    for key, (_en, fi, probe) in G.COPY.items():
        pat = r'<span class="fi( probe)?" lang="fi">%s</span>' % re.escape(fi)
        m = re.search(pat, DOC)
        if not m:
            continue          # key not used on the page
        marked = bool(m.group(1))
        if marked != probe:
            return bad("probe marking",
                       "%s: marked=%s but COPY says probe=%s" % (key, marked, probe))
    ok("probe marking (unshipped Finnish strings are dotted, shipped ones are not)")


# --------------------------------------------------- prove check 1 goes red

def prove_check_fails():
    """Reconstruct the defect that was really written -- the crest given its own wide track --
    and assert check 1 rejects it."""
    broken = G.MOCK_CSS.replace(
        "--cols: 1.4rem minmax(0, 1fr) 1.9rem 1.7rem 1.7rem 1.7rem 2.4rem 2.2rem;",
        "--cols: 1.4rem 24px minmax(0, 1fr) 1.9rem 1.7rem 1.7rem 1.7rem 2.4rem 2.2rem;")
    if broken == G.MOCK_CSS:
        sys.exit("FATAL: could not reconstruct the defect -- the wide --cols string moved.")
    before = len(FAILS)
    check_track_parity(css=broken)
    if len(FAILS) == before:
        sys.exit("FATAL: check 1 stayed GREEN on the real defect. It is decoration.")
    FAILS.pop()
    print("  (check 1 correctly went RED on the 9-track/8-cell defect)")


def prove_trace_check_still_fires():
    """Check 5 was NARROWED to ignore comments. Prove the narrowing did not hollow it out:
    a live leftover rule must still trip it."""
    global DOC
    original, before = DOC, len(FAILS)
    # inject INSIDE .stage, since the scan is now page-scoped -- a leftover in the harness is
    # not the failure this guards against
    DOC = original.replace('<div class="fx">', '<div class="fx"><div class="brow"></div>', 1)
    try:
        check_cut_block_left_no_trace()
    finally:
        DOC = original
    if len(FAILS) == before:
        raise SystemExit("FATAL: check 5 stayed GREEN on a live leftover `.brow` rule.")
    FAILS.pop()
    print("  (check 5 correctly went RED on a live leftover `.brow` rule)")


if __name__ == "__main__":
    print("competition_hub_mock.html")
    check_track_parity()
    check_crest_survives_both_widths()
    check_every_team_links()
    check_only_the_next_round()
    check_cut_block_left_no_trace()
    check_names_never_truncate()
    check_no_external_fetch_and_no_js()
    check_probe_marking()
    print("negative controls")
    prove_check_fails()
    prove_trace_check_still_fires()
    if FAILS:
        sys.exit("\n%d CHECK(S) FAILED: %s" % (len(FAILS), ", ".join(FAILS)))
    print("\nall checks pass")
