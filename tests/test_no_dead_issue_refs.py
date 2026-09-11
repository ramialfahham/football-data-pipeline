"""The two files that INSTRUCT must not cite an issue that resolves to nothing.

GitHub's tracker did not migrate — its issues are unreachable — and GitLab's numbering restarted
from 1. So every GitHub-era number left in this repo points at an empty page.

That is harmless in an archive and harmful in an instruction. `CLAUDE.md` is read at the start of
every session and `.claude/active_work.md` is the handover a cold session continues from. It has
happened twice: `CLAUDE.md` told every session its next work was "player insights chain
(#153 -> #156)", and a memory file names issue #753 as the authority for the player page design —
which is why that page could not be built from the record.

⚠ A WARNING WAS ALREADY IN PLACE AND DID NOT WORK. The memory index says in bold that any GitHub
number is a pointer to nothing. This is a test instead.

⛔ THE FIRST VERSION OF THIS GUARD USED A NUMERIC BOUNDARY (`>= 115`) AND WAS WRONG WITHIN THE HOUR.
GitLab issue #115 was filed the same day — the context-cleanup issue — so a live reference would
have been flagged as dead, and the constant would need chasing GitLab's counter forever. A guard
that must be re-tuned on a schedule fails the standard it was written to meet.

THE SET BELOW IS CLOSED, WHICH IS WHY IT DOES NOT NEED PERIODIC RE-TUNING. GitHub is gone, so no NEW
dead number can come into existence.

⚠ IT IS NOT "CORRECT FOREVER", AND THE SHAPE OF THE DECAY MATTERS. As GitLab's counter climbs from
#115 into this range, more members become live numbers, so the collision SURFACE grows — and it
grows unevenly, because the set has dense runs (`range(276, 297)` is 21 consecutive, `range(407,
429)` is 22).
⚠ BUT A COLLISION ONLY BITES ON CITATION. The guard fires when one of the two files CITES a set
member, not when GitLab files an issue — so entering a dense run costs nothing by itself. The cost
is one deletion at the moment someone writes that particular live issue into one of these two files,
and those files cite roughly 15 issues between them across the project's whole life.

⚠ CLOSED OVER WHAT THE REPO CITES, NOT OVER EVERY GITHUB ISSUE THAT EXISTED. A dead number nobody
has ever referenced — pasted in later from an old branch or the dead GitHub remote — is NOT in the
set and is NOT caught. Silent. Accepted as the price of an offline guard; the boundary version did
cover it.

These are every `#115`-`#9999` referenced anywhere in `CLAUDE.md`, `docs/`,
`.claude/active_work.md` and the memory store as of 2026-09-10; since GitLab had only reached #115
that day, anything at or above it in a document written earlier is necessarily GitHub-era.

⚠ ONE FUTURE COLLISION IS POSSIBLE AND IS HANDLED BY DESIGN: if GitLab ever issues a number that is
in this set, a legitimate reference to it would be flagged. The fix is to delete that one number
from the set — a one-line, visible, deliberate edit with a reason, not a silent breakage. Contrast
the boundary version, where the same event silenced or broke the guard invisibly.

Scope is deliberately these two files. The ~292 references under `docs/` are left alone: most are
provenance rather than instruction, and 180 of the 257 distinct numbers survive as merged PRs in
git history, so the work is recoverable even where the number is not.
"""
from __future__ import annotations

import hashlib
import pathlib
import re

REPO = pathlib.Path(__file__).resolve().parent.parent

INSTRUCTING_FILES = ("CLAUDE.md", ".claude/active_work.md")

# Every GitHub-era issue number this repo still refers to. Closed set — see the module docstring.
DEAD_GITHUB_ISSUES = frozenset({
    151, *range(153, 157), 163, 178, 182, *range(184, 187), *range(198, 200), 204, 206,
    *range(217, 229), *range(232, 241), 247, *range(250, 263), 264, 266, 268, 272,
    *range(276, 297), 299, *range(307, 315), *range(316, 330), 331, *range(361, 371), 372,
    *range(374, 378), 391, *range(401, 404), 405, *range(407, 429), 430, *range(433, 435),
    441, 444, 446, 448, 452, 477, *range(479, 481), *range(483, 485), *range(488, 490), 491,
    493, 497, 500, 503, *range(505, 509), *range(510, 513), 514, 518, 520, 524,
    *range(526, 528), 530, 536, 539, 547, 559, 561, 563, *range(571, 573), 582, 585, 587,
    589, 598, 600, 604, *range(606, 608), 609, 611, 613, 617, 619, 621, 625, 627, 630, 632,
    634, 636, 638, *range(640, 644), 645, *range(648, 650), *range(653, 655), 657, 664,
    *range(667, 669), 671, 674, *range(676, 679), 687, 690, 753, 799, 810, 822,
    *range(825, 827), *range(838, 847), *range(850, 855), 857, *range(861, 863), 866, 868,
    872, 876, 892, *range(896, 898), 908,
})

# `#` + 1-4 digits, not preceded by `&` or `;`, not followed by another hex digit. All three found
# by review rather than by writing the pattern, in escalating order:
#   · TRAILING — `docs/roles/ui_expert.md` carries the CSS colour `#475569`, which a naive
#     `#(\d+)` reads as issue 475569.
#   · `&` — `&#153;` is an HTML numeric character entity and reads as issue 153, which IS in the set.
#   · `;` — and this is the one worth understanding. `&amp;#753;` (a literally-displayed entity)
#     defeats a `(?<!&)` lookbehind, because the character before `#` is `;`, not `&`. Adding
#     `(?<!&amp;)` would then be defeated by `&amp;amp;#753;`, and so on forever: chasing escape
#     DEPTH is an infinite regress. Excluding `;` ends it at every depth at once, because every
#     escaped entity — however many times nested — closes with `;` immediately before the `#`.
# ⚠ A `;` directly before an issue reference is not a real citation form, so this costs no coverage.
# Four digits is generous — GitHub's counter never passed four.
_REF = re.compile(r"(?<![&;])#(\d{1,4})(?![0-9a-fA-F])")


def _dead_refs(text: str) -> list[int]:
    return sorted({n for n in (int(m) for m in _REF.findall(text)) if n in DEAD_GITHUB_ISSUES})


def test_the_instructing_files_cite_no_unreachable_issue():
    offenders = {}
    for rel in INSTRUCTING_FILES:
        path = REPO / rel
        assert path.exists(), f"{rel} is missing — this guard is pointed at the wrong path"
        dead = _dead_refs(path.read_text(encoding="utf-8"))
        if dead:
            offenders[rel] = dead

    assert not offenders, (
        "These files instruct, and they cite issues that resolve to nothing: "
        + "; ".join(f"{f} -> {', '.join('#%d' % n for n in ns)}" for f, ns in offenders.items())
        + ". GitHub's tracker did not migrate. Say the FACT instead of the number — the sentence "
        "almost always already carries it. If the referenced work matters it is probably a merged "
        "PR: `git log --all --grep='#N'` finds it (180 of the 257 are there). Do NOT satisfy this "
        "test by deleting the sentence, and do NOT satisfy it by removing the number from "
        "DEAD_GITHUB_ISSUES unless GitLab has genuinely issued that number."
    )


def test_the_guard_can_actually_fire():
    """A guard that never fires is not a guard.

    Pins that the pattern matches a real reference, that a LIVE number is not flagged, and that the
    CSS colour in `docs/roles/ui_expert.md` cannot be mistaken for an issue.
    """
    assert _dead_refs("the authority is #753") == [753]
    assert _dead_refs("see #153 and #156") == [153, 156]
    # GitLab issues, live: #33 is the cost/scalability plan, #115 the context cleanup.
    assert _dead_refs("#33 and #114 and #115 are live") == []
    # The trailing-hex guard: a six-digit CSS colour is not issue 475569.
    assert _dead_refs("| Weaker side | `#475569` (slate-600) |") == []
    # HTML entities are not issue references, at ANY escape depth — the `;` exclusion, not a
    # per-depth blacklist. `platform-reviewer` found depth 2 after depth 1 was fixed; depth 3 is
    # pinned here so the regress is closed rather than one step behind.
    assert _dead_refs("the trademark sign is &#153; in legacy markup") == []
    assert _dead_refs("shown literally as &amp;#753; in the source") == []
    assert _dead_refs("and doubly as &amp;amp;#753; if quoted again") == []
    # A real reference in punctuation still matches — the exclusion costs no coverage.
    assert _dead_refs("see (#753) and [#156]") == [156, 753]


def test_a_short_all_digit_hex_colour_is_a_KNOWN_false_positive():
    """⚠ PINNED AS A LIMITATION, NOT FIXED — and deliberately.

    `#217` is both a member of the dead set and a valid three-digit CSS shorthand colour. The two
    are TEXTUALLY IDENTICAL, so no regex can separate them; the six-digit form is only caught
    because a trailing hex digit gives the lookahead something to trip on.

    Not fixed because every available fix is worse. A context rule — "ignore it after the word
    colour", "ignore it inside backticks" — buys this at the price of FALSE NEGATIVES, and a guard
    that lets through the thing it exists to catch has failed at its job, where one that occasionally
    complains has not. The failure here is loud: a red test with a message naming the number.

    ⛔ ASSERTING THE CURRENT (WRONG) BEHAVIOUR ON PURPOSE. If someone later makes `#217` in prose
    stop being read as an issue, this test fails and they must decide deliberately whether they have
    also just introduced a false negative. That is the point — an undocumented gap becomes a
    documented one.

    Found by `platform-reviewer` at round 3, after it had already found the six-digit colour and two
    depths of HTML entity in the same pattern.
    """
    assert _dead_refs("accent colour #217 was chosen") == [217]
    assert _dead_refs("use #753 as the tint") == [753]
    # The forms that ARE separable stay separable: letters, or six digits.
    assert _dead_refs("shorthand #fff") == []
    assert _dead_refs("the six-digit #475569") == []


def test_a_reference_abutting_a_hex_letter_is_a_KNOWN_false_negative():
    """⚠ THE OTHER SIDE OF THE SAME TRADE, PINNED — and this is the dangerous direction.

    The trailing `(?![0-9a-fA-F])` exists to stop `#475569` reading as issue 475569. It excludes any
    digit run followed by a hex letter, which is broader than that: `#217e` matches nothing, so a
    real dead reference written that way is MISSED. A false negative, not a false positive — the
    guard letting through what it exists to catch.

    ACCEPTED, because the ambiguity is genuine in both directions and the lengths overlap: CSS hex
    colours are 3, 4, 6 or 8 characters, so `#217e` is itself a valid 4-digit `#RGBA` colour. There
    is no reading of `#217e` that is unambiguously a citation.
    WHAT DECIDES IT is which side has occurred: `#475569` was real, in `docs/roles/ui_expert.md`.
    A citation written as `#217e`, with no space or punctuation after the number, is not a form
    anyone uses — verified: `grep -P "#\\d{1,4}[a-fA-F]"` over both guarded files matches nothing.

    ⛔ PINNED BECAUSE IT WAS SILENT. `platform-reviewer` FAILed round 4 on exactly that: I had
    pinned the false-POSITIVE side (`#217` as a colour) and left this side undisclosed and
    untested, which is the more dangerous half by this file's own standard. Its words: a test that
    would still pass with the change reverted is not coverage. This is that assertion.
    """
    assert _dead_refs("see #217e for details") == []
    assert _dead_refs("the tag #908d covers it") == []
    # Every ordinary citation form still matches — the exclusion only bites on direct abutment.
    assert _dead_refs("see #217 for details") == [217]
    assert _dead_refs("see #217, then #908.") == [217, 908]


def test_no_member_of_the_dead_set_can_be_removed_quietly():
    """⛔ THE OBVIOUS WAY TO SILENCE THIS GUARD IS TO EDIT THE SET, so every member is pinned.

    An earlier version pinned only `min(...) == 151` and two literal strings, which protected
    exactly 4 of 256 members — deleting any of the other 252 left all tests green.
    `platform-reviewer` caught it, and caught that the mutation offered as proof had deleted 151
    itself: the one member that happened to be pinned. A cherry-picked mutation demonstrates
    nothing about the general property it is offered for.

    A digest covers every member against deletion, addition AND substitution, which a length check
    alone would not. `hashlib` rather than `hash()` because the built-in is salted per process for
    some types and this must be stable across runs and machines.
    """
    digest = hashlib.sha256(
        ",".join(str(n) for n in sorted(DEAD_GITHUB_ISSUES)).encode()
    ).hexdigest()
    assert len(DEAD_GITHUB_ISSUES) == 256 and digest == (
        "eabfb8b6a38282660b314f9ce9d72a6b713c3f8decea897b77edcb8c3bba1e84"
    ), (
        "DEAD_GITHUB_ISSUES changed. There is exactly one legitimate reason: GitLab has issued a "
        "number that is in the set, so a live reference was being flagged — remove that ONE entry "
        "and update the count and digest here, in the same commit, with the issue named in the "
        "message. Any other change means the set was regenerated or edited to silence a failure."
    )


def test_the_headroom_before_a_collision_is_stated():
    """The set is closed, so the only way it goes wrong is GitLab reaching one of these numbers.

    GitLab was at #115 on 2026-09-10 and the lowest dead number is #151, so there are 35 issues of
    headroom. Pinning both ends makes the collision arrive as a named test failure rather than as a
    confusing false positive on a live reference.
    """
    assert min(DEAD_GITHUB_ISSUES) == 151
    assert 115 not in DEAD_GITHUB_ISSUES, "GitLab #115 is the context-cleanup issue and is live"
