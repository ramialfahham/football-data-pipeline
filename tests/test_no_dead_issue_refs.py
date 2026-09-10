"""The two files that INSTRUCT must not cite an issue number that resolves to nothing.

GitHub's tracker did not migrate: 7 milestones and 114 issues are unreachable, and GitLab's own
numbering restarted, so it currently tops out around #114. Every `#115` or above in this repo is a
GitHub-era number pointing at nothing.

That is harmless in an archive and harmful in an instruction. `CLAUDE.md` is read at the start of
every session and `.claude/active_work.md` is the handover a cold session continues from; a dead
number in either sends the reader somewhere empty. It happened: `CLAUDE.md` told every session its
next work was "player insights chain (#153 -> #156)", and a memory file named issue #753 as the
authority for the player page design, which is why that page could not be built from the record.

⚠ A WARNING WAS ALREADY IN PLACE AND DID NOT WORK. The memory index says in bold that any GitHub
number is a pointer to nothing. This is a test instead.

Scope is deliberately these two files. The ~292 references under `docs/` are left alone: most are
provenance rather than instruction, and 180 of the 257 distinct numbers survive as merged PRs in
git history, so the work is recoverable even where the number is not.
"""
from __future__ import annotations

import pathlib
import re

REPO = pathlib.Path(__file__).resolve().parent.parent

# GitLab's highest issue at the time of writing. The boundary is checked, not assumed: `#33` reads
# like a GitHub-era audit reference and resolves to a real GitLab issue ("Pipeline
# cost/scalability"), so low numbers are genuinely live and only >= this are dead.
FIRST_DEAD = 115

INSTRUCTING_FILES = ("CLAUDE.md", ".claude/active_work.md")

_REF = re.compile(r"#(\d+)")


def _dead_refs(text: str) -> list[int]:
    return sorted({int(n) for n in _REF.findall(text) if int(n) >= FIRST_DEAD})


def test_the_instructing_files_cite_no_unreachable_issue():
    offenders = {}
    for rel in INSTRUCTING_FILES:
        path = REPO / rel
        assert path.exists(), f"{rel} is missing — this guard is pointed at the wrong path"
        dead = _dead_refs(path.read_text(encoding="utf-8"))
        if dead:
            offenders[rel] = dead

    assert not offenders, (
        "These files instruct, and they cite issue numbers that resolve to nothing: "
        + "; ".join(f"{f} -> {', '.join('#%d' % n for n in ns)}" for f, ns in offenders.items())
        + f". GitHub's tracker did not migrate, so any #{FIRST_DEAD}+ is unreachable. "
        "Say the FACT instead of the number — the sentence almost always already carries it. "
        "If the referenced work matters, it is probably a merged PR: `git log --all --grep='#N'` "
        "finds it. Do NOT satisfy this test by deleting the sentence."
    )


def test_the_boundary_is_not_vacuous():
    """A guard that can never fire is not a guard.

    If `FIRST_DEAD` were set above every number the repo uses, the test above would pass on any
    content at all. This pins that the pattern really does match a reference in the shape these
    files use, so the first test is known to be capable of failing.
    """
    assert _dead_refs("see #153 and #156") == [153, 156]
    assert _dead_refs("GitLab #33 and #114 are live") == []
    assert _dead_refs("no refs here") == []
