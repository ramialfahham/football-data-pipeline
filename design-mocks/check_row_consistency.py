"""Prove the match-row block renders identically on every mock page, by reading the emitted HTML.

Run the generators first; restyling of the row is checked by scripts/check_page_css.py.
"""
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

HERE = Path(__file__).parent
DOCS = {name: (HERE / f).read_text(encoding="utf-8") for name, f in (
    ("home", "home_mock.html"),
    ("matches-next", "matches_next_mock.html"),
    ("matches-past", "matches_past_mock.html"),
    ("hub", "competition_hub_mock_league.html"),
)}

_stale = HERE / "matches_mock.html"
if _stale.exists():
    sys.exit("FATAL: %s still exists. It is the stacked two-in-one file; re-run gen_matches.py."
             % _stale.name)

FAILS = []


def ok(m):
    print("  PASS  %s" % m)


def bad(m, d):
    FAILS.append(m)
    print("  FAIL  %s\n        %s" % (m, d))


ROW = re.compile(r'<(a|div) class="(fxrow[^"]*)"[^>]*>(.*?)</\1>', re.S)
GH = re.compile(r'<div class="gh">(.*?)</div>\s*(?=<div class="dh"|<a|<div class="fxrow|\n)', re.S)

KNOWN_ROW_CLASSES = {"sides", "side", "crest", "xs", "nm", "when", "t", "rowtz",
                     "g", "winner", "num"}


def skeletons(doc):
    """Every `.fxrow` reduced to structure; the SVG badge and the `winner` marker are normalised
    because they legitimately vary by sample data."""
    out = {"upcoming": set(), "played": set()}
    for tag, cls, inner in ROW.findall(doc):
        inner = re.sub(r"<svg.*?</svg>", "", inner, flags=re.S)
        inner = inner.replace('class="g winner num"', 'class="g num"')
        inner = re.sub(r">[^<>]*<", "><", inner)
        inner = re.sub(r"\s+", " ", inner).strip()
        out["played" if "played" in cls.split() else "upcoming"].add(
            "<%s class=%r>%s" % (tag, cls, inner))
    return out


def gh_skeletons(doc):
    """The group head reduced to structure, with the competition link normalised."""
    out = set()
    for inner in GH.findall(doc):
        inner = re.sub(r"<svg.*?</svg>", "", inner, flags=re.S)
        inner = re.sub(r'<a class="cnm[^"]*"[^>]*>(.*?)</a>', r"<CNM>\1</CNM>", inner, flags=re.S)
        inner = re.sub(r">[^<>]*<", "><", inner)
        out.add(re.sub(r"\s+", " ", inner).strip())
    return out


def check_row_markup_matches():
    """1. Every surface emits the same row skeleton, per kind."""
    per = {n: skeletons(d) for n, d in DOCS.items()}
    compared = 0
    for kind in ("upcoming", "played"):
        have = {n: s[kind] for n, s in per.items() if s[kind]}
        if len(have) < 2:
            print("        (skipped %s — on %d surface(s), nothing to compare)"
                  % (kind, len(have)))
            continue
        compared += 1
        shared = set.intersection(*have.values())
        union = set.union(*have.values())
        if not shared or union - shared:
            return bad("row markup matches",
                       "%s rows differ across %s\n        %s"
                       % (kind, sorted(have), sorted(union - shared)[:1] or sorted(union)[:1]))
    if not compared:
        return bad("row markup matches", "no row kind appears on two surfaces — nothing compared")
    ok("row markup matches (%d kind(s) across %d surfaces, identical skeletons)"
       % (compared, len(DOCS)))


def check_group_head_matches():
    """2. Grouping is competition, then date, everywhere: no day headings, no matchday."""
    per = {n: gh_skeletons(d) for n, d in DOCS.items()}

    # The competition page's own <h1> is the competition level, so it must emit no group head.
    if per["hub"]:
        return bad("group head matches",
                   "the competition page emits a competition heading under its own <h1>")
    have = {n: s for n, s in per.items() if s}
    if len(have) < 2:
        return bad("group head matches", "fewer than two surfaces carry the level — %s" % sorted(have))
    first = per["home"]
    for n, s in have.items():
        if s != first:
            return bad("group head matches",
                       "%s differs from home.\n        home: %s\n        %s: %s"
                       % (n, sorted(first)[:1], n, sorted(s)[:1]))
    for n, d in DOCS.items():
        if 'class="daydate"' in d:
            return bad("group head matches", "%s still emits a day heading" % n)
        if 'class="md"' in d:
            return bad("group head matches", "%s still emits a matchday on the heading" % n)
        if 'class="dh"' not in d:
            return bad("group head matches", "%s has no date level inside the group" % n)
    ok("group head matches (identical on %s; %s correctly has none; date level on all %d)"
       % (", ".join(sorted(have)), "hub", len(DOCS)))


SYSTEM_CSS = Path(__file__).resolve().parent.parent / "site_v2/src/styles/system.css"

# classes the block deliberately reuses from the design system; every other emitted class must be new
BORROWED = {"fxrow", "fxgroup", "gh", "sides", "side", "crest", "xs", "nm", "when", "t", "d",
            "lnk", "num", "linkchip", "linkrow", "tab", "tabs", "on", "here", "sep", "crumb",
            "eyebrow", "sechead", "dh", "rowtz", "g", "winner", "played", "clogo", "cnm", "chev"}


def check_no_class_collides_with_the_design_system():
    """A class the block invents must not already exist in system.css, or it inherits its rules."""
    css = re.sub(r"/\*.*?\*/", "", SYSTEM_CSS.read_text(encoding="utf-8"), flags=re.S)
    system_classes = set(re.findall(r"\.([a-zA-Z][\w-]*)", css))

    emitted = set()
    for name, doc in DOCS.items():
        for tag, cls, inner in ROW.findall(doc):
            emitted.update(cls.split())
            emitted.update(c for grp in re.findall(r'class="([\w -]+)"', inner)
                           for c in grp.split())

    collisions = sorted((emitted - BORROWED) & system_classes)
    if collisions:
        return bad("no class collides with the design system",
                   "the block emits %s, which system.css already defines — rename, or add to "
                   "BORROWED if the reuse is deliberate" % collisions)
    ok("no class collides with the design system (%d emitted, %d deliberately borrowed)"
       % (len(emitted), len(emitted & BORROWED)))


def check_row_vocabulary_is_closed():
    """3. A row may only emit classes from a FIXED set, or a surface could add an element and
    the comparison would simply learn to live with it."""
    for name, doc in DOCS.items():
        for _t, _c, inner in ROW.findall(doc):
            inner = re.sub(r"<svg.*?</svg>", "", inner, flags=re.S)
            classes = {c for grp in re.findall(r'class="([\w -]+)"', inner) for c in grp.split()}
            unknown = classes - KNOWN_ROW_CLASSES
            if unknown:
                return bad("row vocabulary is closed",
                           "%s emits unrecognised row class(es): %s" % (name, sorted(unknown)))
    ok("row vocabulary is closed (%d known classes, nothing else on any surface)"
       % len(KNOWN_ROW_CLASSES))


def check_time_slots_are_right():
    """4. Every upcoming row carries its own timezone, and played rows and group heads carry none."""
    counts = []
    for name, doc in DOCS.items():
        rows = ROW.findall(doc)
        if not rows:
            return bad("time slots are right", "%s emits no match rows at all" % name)
        for _t, cls, inner in rows:
            is_played = "played" in cls.split()
            has_when = 'class="when"' in inner
            has_zone = 'class="rowtz"' in inner
            if is_played and (has_when or has_zone):
                return bad("time slots are right",
                           "%s: a played row still carries a kick-off column" % name)
            if not is_played and not (has_when and has_zone):
                return bad("time slots are right",
                           "%s: an upcoming row is missing its kick-off or its zone" % name)
        if 'class="tzone"' in doc:
            return bad("time slots are right", "%s puts a timezone on a group head" % name)
        up = sum(1 for _t, c, _i in rows if "played" not in c.split())
        counts.append("%s %d/%d" % (name, up, len(rows)))
    ok("time slots are right (upcoming/total per surface: %s — none on a heading)"
       % ", ".join(counts))


def prove_checks_fire():
    """Both comparisons must be shown to fail, or they are decoration."""
    global DOCS
    original = dict(DOCS)

    before = len(FAILS)
    DOCS = dict(original)
    DOCS["hub"] = original["hub"].replace('<span class="rowtz">', '<span class="d">', 1)
    if DOCS["hub"] == original["hub"]:
        raise SystemExit("FATAL: could not find an upcoming row in the hub to break.")
    check_row_markup_matches()
    if len(FAILS) == before:
        raise SystemExit("FATAL: check 1 stayed GREEN with one surface using a bespoke row.")
    FAILS.pop()
    print("  (check 1 went RED on one surface using a bespoke time slot)")

    before = len(FAILS)
    DOCS = dict(original)
    # give the competition page back the redundant competition heading under its own <h1>
    DOCS["hub"] = original["hub"].replace(
        '<div class="dh">',
        '<div class="gh"><a class="cnm lnk" href="/en/bundesliga/">'
        '<span class="clogo"></span><span class="nm">Bundesliga</span></a></div>'
        '<div class="dh">', 1)
    check_group_head_matches()
    if len(FAILS) == before:
        raise SystemExit("FATAL: check 2 stayed GREEN with the competition heading back on its "
                         "own page.")
    FAILS.pop()
    print("  (check 2 went RED on the competition page repeating its own name)")

    DOCS = original


if __name__ == "__main__":
    print("Next-matches block — home vs matches vs competition hub")
    check_row_markup_matches()
    check_group_head_matches()
    check_no_class_collides_with_the_design_system()
    check_row_vocabulary_is_closed()
    check_time_slots_are_right()
    print("negative controls")
    prove_checks_fire()
    if FAILS:
        sys.exit("\n%d CHECK(S) FAILED: %s" % (len(FAILS), ", ".join(FAILS)))
    print("\nall checks pass")
