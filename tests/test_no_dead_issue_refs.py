"""The files that instruct must not cite a GitHub-era issue number, which now resolves to nothing.

`DEAD_GITHUB_ISSUES` is a closed set; remove an entry only when GitLab has issued that number.
"""
from __future__ import annotations

import hashlib
import pathlib
import re

REPO = pathlib.Path(__file__).resolve().parent.parent

INSTRUCTING_FILES = ("CLAUDE.md",)

DEAD_GITHUB_ISSUES = frozenset({
    163, 178, 182, *range(184, 187), *range(198, 200), 204, 206,
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

# `#` + 1-4 digits, not preceded by `&` or `;` (an escaped HTML entity at any depth has `;` before
# the `#`), and not followed by a hex digit (so the CSS colour `#475569` is not issue 475569).
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
    assert _dead_refs("the authority is #753") == [753]
    assert _dead_refs("see #163 and #178") == [163, 178]
    assert _dead_refs("#33 and #114 and #115 are live") == []
    assert _dead_refs("| Weaker side | `#475569` (slate-600) |") == []
    # HTML entities are not issue references at any escape depth.
    assert _dead_refs("the trademark sign is &#153; in legacy markup") == []
    assert _dead_refs("shown literally as &amp;#753; in the source") == []
    assert _dead_refs("and doubly as &amp;amp;#753; if quoted again") == []
    assert _dead_refs("see (#753) and [#163]") == [163, 753]


def test_a_short_all_digit_hex_colour_is_a_KNOWN_false_positive():
    """A dead-set member can also be a valid three-digit CSS colour, so no regex can split them."""
    assert _dead_refs("accent colour #217 was chosen") == [217]
    assert _dead_refs("use #753 as the tint") == [753]
    assert _dead_refs("shorthand #fff") == []
    assert _dead_refs("the six-digit #475569") == []


def test_a_reference_abutting_a_hex_letter_is_a_KNOWN_false_negative():
    """The trailing hex exclusion also drops `#217e`, which is itself a valid CSS `#RGBA` colour."""
    assert _dead_refs("see #217e for details") == []
    assert _dead_refs("the tag #908d covers it") == []
    assert _dead_refs("see #217 for details") == [217]
    assert _dead_refs("see #217, then #908.") == [217, 908]


def test_no_member_of_the_dead_set_can_be_removed_quietly():
    """A digest pins every member against deletion, addition and substitution."""
    digest = hashlib.sha256(
        ",".join(str(n) for n in sorted(DEAD_GITHUB_ISSUES)).encode()
    ).hexdigest()
    assert len(DEAD_GITHUB_ISSUES) == 251 and digest == (
        "f9570f666e58f898b5216e3a4268b03f87ca6a8a3247c1d44472bba678b7e45c"
    ), (
        "DEAD_GITHUB_ISSUES changed. There is exactly one legitimate reason: GitLab has issued a "
        "number that is in the set, so a live reference was being flagged — remove that ONE entry "
        "and update the count and digest here, in the same commit, with the issue named in the "
        "message. Any other change means the set was regenerated or edited to silence a failure."
    )


def test_the_headroom_before_a_collision_is_stated():
    """Pinning both ends makes a GitLab collision a named failure, not a false positive."""
    assert min(DEAD_GITHUB_ISSUES) == 163
    assert 115 not in DEAD_GITHUB_ISSUES, "GitLab #115 is the context-cleanup issue and is live"
