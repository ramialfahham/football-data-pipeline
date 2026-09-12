"""Prove the "Next matches" block is IDENTICAL on every surface that shows it.

The rule: *"this is a repetitive content block ... it has to be consistent everywhere we
show this type of content block"*. `rows.py` makes that true by construction; this file proves
it of the RENDERED output, which is the only thing a reader ever sees.

⚠ THREE surfaces, not two. The home page was left out of the first version of this check and
that is precisely where the inconsistency was spotted — `home/HeroFixtures.astro` had its own
copy of the markup. A consistency check that skips a surface is worse than none.

  home_mock.html              the home page's Next matches module
  matches_mock.html           /matches/ and /matches/results/
  competition_hub_mock.html   a competition's own page

Comparing the GENERATORS would prove nothing — they all import the same module. These checks
read the emitted HTML and compare markup skeletons.

Run the three generators first.
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
    ("hub", "competition_hub_mock.html"),
)}

# ⚠ FOUR files, because Matches is TWO pages. It was one stacked file with "Page 1"/"Page 2"
# labels, which read as a single page showing both lists and whose tab bar did nothing when
# clicked. Two tabs means two URLs (#46), so it is two files and the tabs link to each other.
_stale = HERE / "matches_mock.html"
if _stale.exists():
    sys.exit("FATAL: %s still exists. It is the stacked two-in-one file; re-run gen_matches.py."
             % _stale.name)

import rows as R   # noqa: E402

FAILS = []


def ok(m):
    print("  PASS  %s" % m)


def bad(m, d):
    FAILS.append(m)
    print("  FAIL  %s\n        %s" % (m, d))


ROW = re.compile(r'<(a|div) class="(fxrow[^"]*)"[^>]*>(.*?)</\1>', re.S)
GH = re.compile(r'<div class="gh">(.*?)</div>\s*(?=<div class="dh"|<a|<div class="fxrow|\n)', re.S)

# ⚠ `rep` / `repoff` are GONE. A "Report" / "No report yet" chip occupied the played row's right
# column — the slot that carries the kick-off on every other row — and was removed when the
# played row was ruled to be the same row. Removing them from this set is what
# makes their return a failure rather than a silent tolerance.
KNOWN_ROW_CLASSES = {"sides", "side", "crest", "xs", "nm", "when", "t", "rowtz",
                     "g", "winner", "num"}


def skeletons(doc):
    """Every `.fxrow` reduced to STRUCTURE: tag, classes and nested element classes, with all
    variable content removed.

    ⚠ Two things are normalised, and only two. The SVG badge, because a club crest and a
    national flag are deliberately different drawings — leaving them in would report the design
    working correctly as an inconsistency. And the `win` marker, because it says which side won,
    so a page whose sample has no away win would otherwise look inconsistent. Both are applied
    by the shared function to every page, so neither hides a real difference."""
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
    """The GROUP HEAD. This is the surface that was actually inconsistent: the Matches page
    headed its groups with a DAY while the competition page used a MATCHDAY.

    The competition name renders as `<a class="cnm lnk">` off its own page and
    `<span class="cnm here">` on it — a STATE, the same convention the nav and breadcrumb use —
    so the whole element is normalised, open tag and close. Everything inside must still match."""
    out = set()
    for inner in GH.findall(doc):
        inner = re.sub(r"<svg.*?</svg>", "", inner, flags=re.S)
        # ⚠ MATCH `cnm` WITH OR WITHOUT EXTRA CLASSES, and swallow the href. The class was
        # `cnm lnk` until the interaction standard dropped `lnk` (the underline it named is gone),
        # and this pattern silently stopped matching — which let each competition's own href into
        # the skeleton, so every surface "differed" purely by which leagues it happened to list.
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
    """2. THE GROUPING IS THE SAME EVERYWHERE: competition, then date. No day headings, and no
    matchday on the heading."""
    per = {n: gh_skeletons(d) for n, d in DOCS.items()}

    # ⚠ THE COMPETITION PAGE MUST HAVE NONE. Level 1 of the block is the competition, and on
    # that page the competition is the <h1>; rendering it again as a group heading put
    # "Bundesliga" directly under "Bundesliga". A block may OMIT a level the page supplies. This
    # is an assertion, not a skip: the omission is the rule, so its absence is checked.
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
    # ⚠ report what was actually compared. The first version said "identical on all 3" while the
    # competition page carried none at all — a check that overstates its own coverage is how a
    # gap survives a green run.
    ok("group head matches (identical on %s; %s correctly has none; date level on all %d)"
       % (", ".join(sorted(have)), "hub", len(DOCS)))


SYSTEM_CSS = Path(__file__).resolve().parent.parent / "site_v2/src/styles/system.css"

# classes the block deliberately REUSES from the design system — everything else it emits must be
# a name system.css has never heard of
BORROWED = {"fxrow", "fxgroup", "gh", "sides", "side", "crest", "xs", "nm", "when", "t", "d",
            "lnk", "num", "linkchip", "linkrow", "tab", "tabs", "here", "sep", "crumb",
            "eyebrow", "sechead"}


def check_no_class_collides_with_the_design_system():
    """⚠ THE BUG THAT COST FOUR ROUNDS. The played row's modifier was `res`. `system.css:155`
    already defines `.res` — the W/D/L result chip of the `.rmatch` row — carrying
    `width: 24px; height: 24px`. So every played row was TWENTY-FOUR PIXELS WIDE: the name
    collapsed to nothing, the rows overlapped, and four rounds of layout fixes could not help,
    because none of them touched the cause.

    A block's own class names must be names the design system has never defined, unless the block
    is deliberately reusing that component. This is the class-level fix; renaming `res` to
    `played` was only the instance."""
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
    """4. Every UPCOMING row carries its own timezone, and nothing else does. A conditional
    zone put two shapes of one block on a single screen."""
    # ⚠ UPCOMING rows carry a kick-off and a zone; PLAYED rows carry NEITHER (a finished
    # match's start time is not information). Both halves are asserted, so dropping a
    # zone from an upcoming row and re-adding a kick-off to a played one are each a failure.
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


def check_shared_css_everywhere():
    """5. Same markup with different CSS is not consistency."""
    probe = ".fxrow .side .g { margin-left: auto;"
    if probe not in R.ROW_CSS:
        return bad("shared CSS everywhere", "the probe line is no longer in rows.ROW_CSS")
    for name, doc in DOCS.items():
        if R.ROW_CSS.strip() not in doc:
            return bad("shared CSS everywhere", "rows.ROW_CSS is not inlined verbatim in %s" % name)
    ok("shared CSS everywhere (rows.ROW_CSS inlined byte for byte in all %d)" % len(DOCS))


def check_no_surface_redefines_the_row():
    """6. A surface must not quietly restyle the shared block — that is how four treatments
    appeared in the first place."""
    for name, doc in DOCS.items():
        css = doc.split("<style>", 1)[1].split("</style>", 1)[0].replace(R.ROW_CSS, "")
        # ⚠ SPLIT ON THE MARKER FIRST, THEN STRIP COMMENTS: the marker lives inside a comment,
        # so stripping first deletes it and the check reports system.css's own rules as overrides.
        if "MOCK HARNESS ONLY" not in css:
            return bad("no surface redefines the row", "%s: marker not found — check is blind" % name)
        mine = re.sub(r"/\*.*?\*/", "", css.split("MOCK HARNESS ONLY", 1)[1], flags=re.S)
        strays = re.findall(r"^[^{}\n]*\.(?:fxrow|fxgroup|clogo|dh)\b[^{}\n]*\{", mine, re.M)
        if strays:
            return bad("no surface redefines the row",
                       "%s restyles the shared block: %s" % (name, [s.strip() for s in strays]))
    ok("no surface redefines the row (no stray block rule in any surface's own CSS)")


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
    check_shared_css_everywhere()
    check_no_surface_redefines_the_row()
    print("negative controls")
    prove_checks_fire()
    if FAILS:
        sys.exit("\n%d CHECK(S) FAILED: %s" % (len(FAILS), ", ".join(FAILS)))
    print("\nall checks pass")
