"""Checks for the competition page mocks (competition_hub_mock_<kind>.html, four kinds).

Each asserts a rule the DESIGN depends on, not merely that a file was produced.

Run `python gen_competition_hub.py` first.

The track-parity check exists because the defect it catches was actually written: a first draft
gave the crest its own grid track, leaving more tracks than cells at the wide breakpoint. A
later one let the heading and the rows size their own tracks, so the headings sat off the
numbers. `prove_check_fails()` at the bottom reconstructs the first and asserts the check goes
RED on it -- a check only ever seen green proves nothing.
"""
import re
import sys

import gen_competition_hub as G   # noqa: E402  (the mock's own data is the expectation)

FAILS = []


def ok(name):
    print("  PASS  %s" % name)


QUIET = [False]


def bad(name, detail):
    FAILS.append(name)
    if not QUIET[0]:
        print("  FAIL  %s\n        %s" % (name, detail))


# ------------------------------------------------------------------ helpers

def doc(kind):
    return G.out_path(kind).read_text(encoding="utf-8")


def stage_html(text):
    """The rendered PAGE only -- `.stage` -- with the toggle bar and the legend cut off."""
    return text[text.index('<div class="stage">'):text.index('<div class="legend">')]


def track_lists(css):
    """Every `--cols` declared on a bare `.ctab` block, narrow first, wide second."""
    out = []
    for b in re.findall(r"(?<![.\w])\.ctab\s*\{([^}]*)\}", css):
        m = re.search(r"--cols:\s*([^;]+);", b)
        if m:
            out.append(m.group(1).strip())
    return out


def n_tracks(decl):
    """Grid tracks in a template string; `minmax(a, b)` is ONE track."""
    flat = re.sub(r"\w+\([^)]*\)", "T", decl)
    return len(flat.split())


def top_level_cells(row_html):
    """Class lists of the direct-child cells of one grid row (the row's own tag stripped)."""
    inner = row_html[row_html.index(">") + 1:row_html.rindex("</")]
    top = []
    depth = 0
    for tok in re.finditer(r"<(/?)(span|a|b|div|svg|path)\b[^>]*?(/?)>", inner):
        if tok.group(3):
            continue
        if not tok.group(1):
            if depth == 0:
                cls = re.search(r'class="([^"]*)"', tok.group(0))
                top.append(cls.group(1) if cls else "")
            depth += 1
        else:
            depth -= 1
    return top


def first(pattern, text):
    m = re.search(pattern, text, flags=re.S)
    return m.group(0) if m else ""


# ------------------------------------------------------------------- checks

def check_track_parity(css=None):
    """The narrow and wide `--cols` lists must count exactly the cells a row shows at that
    width: every cell at wide, every cell minus the `.wdl` ones at narrow (their tracks are
    zero-width, the cells display:none). The heading emits the same cells as a row."""
    text = doc("league")
    css = css or text[:text.index("</style>")]
    lists = track_lists(css)
    if len(lists) != 2:
        bad("table track parity", "expected a narrow and a wide --cols on .ctab, found %d" % len(lists))
        return
    page = stage_html(text)
    head = first(r'<div class="ctab-head">.*?</div>', page)
    row = first(r'<a class="ctab-row".*?</a>', page)
    head_cells, row_cells = top_level_cells(head), top_level_cells(row)
    if head_cells and row_cells and len(head_cells) != len(row_cells):
        bad("table track parity", "heading emits %d cells, a row %d" % (len(head_cells), len(row_cells)))
        return
    wide_cells = len(row_cells)
    narrow_cells = wide_cells - sum(1 for c in row_cells if "wdl" in c.split())
    narrow, wide = n_tracks(lists[0]), n_tracks(lists[1])
    zero_tracks = lists[0].split().count("0")
    if wide != wide_cells:
        bad("table track parity", "wide: %d tracks vs %d cells" % (wide, wide_cells))
        return
    if narrow - zero_tracks != narrow_cells:
        bad("table track parity", "narrow: %d non-zero tracks vs %d visible cells" % (narrow - zero_tracks, narrow_cells))
        return
    ok("table track parity (wide %d/%d, narrow %d/%d, one fixed list per width)"
       % (wide, wide_cells, narrow - zero_tracks, narrow_cells))


def check_every_row_is_one_link():
    """A row that leads somewhere is one link, the whole row: every table row and every
    deserved row is an <a class="ctab-row" href>, and no name inside a row is its own link."""
    page = stage_html(doc("league"))
    rows = re.findall(r'<a class="ctab-row" href="/en/teams/[^"]+/"', page)
    n_table = sum(len(t) for t in G.KINDS["league"]["tables"].values())
    inner = re.findall(r'<a class="tm"', page)
    if len(rows) != n_table + 6 or inner:
        bad("every row is one link", "%d row links for %d table rows + 6 deserved rows; %d name links"
            % (len(rows), n_table, len(inner)))
        return
    ok("every row is one link (%d table + 6 deserved rows, no name link)" % n_table)


def check_only_the_next_round():
    """Next matches carries the next round only: every fixture row is upcoming and linked,
    no played row, no results group."""
    page = stage_html(doc("league"))
    upcoming = re.findall(r'<a class="fxrow"\s+href=', page)
    played = re.findall(r'class="fxrow played"', page)
    if len(upcoming) != len(G.LEAGUE_ROUND[2]) or played or "Latest results" in page:
        bad("only the next round", "%d upcoming rows, %d played rows" % (len(upcoming), len(played)))
        return
    ok("only the next round (%d upcoming rows, 0 played)" % len(upcoming))


def check_blocks_per_kind():
    """A block renders only where its mart serves something: league = all four; groups =
    table (six sections, no ranking table) + next round + facts; cup = next round + facts;
    offseason = table + deserved + facts, no next matches."""
    want = {
        "league": {"Table", "Next matches", "Deserved points", "The season in numbers"},
        "groups": {"Table", "Next matches", "The season in numbers"},
        "cup": {"Next matches", "The season in numbers"},
        "offseason": {"Table", "Deserved points", "The season in numbers"},
    }
    for kind, expected in want.items():
        page = stage_html(doc(kind))
        eyebrows = set(re.findall(r'<span class="eyebrow"><span class="en">([^<]+)</span>', page))
        if eyebrows != expected:
            bad("blocks per kind", "%s: rendered %s, expected %s" % (kind, sorted(eyebrows), sorted(expected)))
            return
    groups = stage_html(doc("groups"))
    sections = re.findall(r'<div class="gh"><span class="nm">([^<]+)</span></div>', groups)
    if len(sections) != 6 or any("Ranking" in s for s in sections):
        bad("blocks per kind", "groups: sections %s" % sections)
        return
    ok("blocks per kind (league 4, groups 3 with six group tables, cup 2, offseason 3)")


def check_tabs_inert():
    """Overview is the active tab; the two others are labels without a link."""
    page = stage_html(doc("league"))
    tabs = re.findall(r'<(span|a) class="tab[^"]*"[^>]*>', page)
    links = [t for t in tabs if t == "a"]
    if len(tabs) != 3 or links or 'class="tab on"' not in page:
        bad("tabs inert", "%d tabs, %d links" % (len(tabs), len(links)))
        return
    ok("tabs inert (3 tabs, Overview active, none a link)")


def check_deserved_sign():
    """The Diff column carries the catalogue's sign, actual minus deserved: the 'better' board
    shows minus, the 'worse' board plus, and the boards are ordered by the gap."""
    page = stage_html(doc("league"))
    boards = re.findall(r'<div class="board">.*?</div></div>', page)
    if len(boards) != 2:
        bad("deserved sign", "%d boards" % len(boards))
        return
    better = re.findall(r'<span class="n num pts">([^<]+)</span>', boards[0])
    worse = re.findall(r'<span class="n num pts">([^<]+)</span>', boards[1])
    if not all(v.startswith("−") for v in better) or not all(v.startswith("+") for v in worse):
        bad("deserved sign", "better %s / worse %s" % (better, worse))
        return
    ok("deserved sign (better: %s; worse: %s)"
       % (", ".join(better).replace("−", "-"), ", ".join(worse)))


def check_names_never_truncate():
    """The team name in a table row wraps rather than ellipsising."""
    text = doc("league")
    css = text[:text.index("</style>")]
    m = re.search(r"\.ctab \.tm \.nm\s*\{([^}]*)\}", css)
    decl = m.group(1) if m else ""
    need = ("white-space: normal", "text-overflow: clip", "overflow: visible")
    missing = [n for n in need if n not in decl]
    if missing:
        bad("names never truncate", "missing %s" % missing)
        return
    ok("names never truncate (.ctab overrides the system ellipsis)")


def check_no_external_fetch_and_no_js():
    for kind in G.KINDS:
        text = doc(kind)
        for needle in ("<script", "<img", "media.api-sports.io", "http://", "https://"):
            if needle in text:
                bad("no script, no external fetch", "%s: %r present" % (kind, needle))
                return
    ok("no script, no external fetch (all kinds)")


def check_probe_marking():
    """Every Finnish string's `probe` class matches COPY's flag."""
    page = stage_html(doc("league"))
    for key, (en, fi, probe) in G.COPY.items():
        want = 'class="fi probe"' if probe else 'class="fi"'
        pat = r'<span %s lang="fi">%s</span>' % (re.escape(want), re.escape(G.E(fi)))
        if fi and not re.search(pat, page):
            bad("probe marking", "%s: expected %s for %r" % (key, want, fi[:40]))
            return
    ok("probe marking (every Finnish string marked as COPY declares)")


# ---------------------------------------------------------- negative controls

def prove_check_fails():
    """Reconstruct the crest-track defect and assert check 1 goes RED on it."""
    broken = (".ctab { --cols: 2rem minmax(0, 1fr) 2.3rem 0 0 0 0 2.8rem 2.6rem; }\n"
              "@container (min-width: 470px) { .ctab { --cols: 2rem 24px minmax(0, 1fr) 2.3rem 2.3rem 2.3rem 2.3rem 3.9rem 2.8rem 2.6rem; } }")
    before = list(FAILS)
    QUIET[0] = True
    check_track_parity(css=broken)
    QUIET[0] = False
    fired = len(FAILS) > len(before)
    del FAILS[len(before):]
    if not fired:
        bad("negative control", "the track-parity check stayed green on the crest-track defect")
        return
    ok("negative control: track parity goes red on the crest-track defect")


if __name__ == "__main__":
    print("check_competition_hub.py")
    check_track_parity()
    check_every_row_is_one_link()
    check_only_the_next_round()
    check_blocks_per_kind()
    check_tabs_inert()
    check_deserved_sign()
    check_names_never_truncate()
    check_no_external_fetch_and_no_js()
    check_probe_marking()
    prove_check_fails()
    if FAILS:
        print("\n%d check(s) failed: %s" % (len(FAILS), ", ".join(FAILS)))
        sys.exit(1)
    print("\nall checks passed")
