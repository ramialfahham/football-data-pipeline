"""Prose must agree with the guards it describes.

`.claude/review_routing.json` is the source of truth for which paths confer which
reviewers, and `task_contract_gate.py` for which paths are protected. Neither the
COUNT nor the LIST is derived anywhere: both are restated as English prose, by
hand, across eleven sites. MR !4 added exactly ONE routing row, and that one-line
change cost eleven prose edits and three review rounds (GitLab #1).

The failure mode is not carelessness. It is that nothing can tell you a
hand-copied list is incomplete — a stale "eight" is valid prose, and round 1 of
that review missed the protected-path axis entirely because both lists happened
to be identical eight-item sets, so one grep looked exhaustive.

So these tests derive every number and every list from the two sources and check
the prose against them.

THREE TRAPS THESE TESTS ARE BUILT AROUND, each of which has already cost this repo
a round:

1. A LINE-BASED GREP MISSES A PHRASE STRADDLING A LINE BREAK. Four of the eleven
   sites wrap mid-claim (`cto-reviewer.md` breaks between "all nine" and "guard
   paths"; `working_agreement.md` and `agent_guardrails.md` break inside "on all
   nine, plus platform-reviewer on exactly three"). A first sweep while writing
   this found seven of eleven for exactly that reason. Everything here reads whole
   files and normalises: blockquote markers stripped, then all whitespace collapsed.

2. HISTORICAL NARRATIVE LIVES INSIDE LIVE FILES. `review_routing.json` and
   `working_agreement.md` both quote the superseded "eight"/"two" claim on
   purpose, as the record of a churn worth remembering, and `.claude/task/
   escalations.log` is an append-only log full of them. A blanket word search
   calls all of those drift. They are classified explicitly in `HISTORICAL`, by
   exact snippet, so a real regression cannot hide behind the same excuse.

3. CLASSIFY BY CONTENT, NOT BY PHRASING. The enumeration test does not carry a
   list of sites. It finds every RUN of adjacent protected-path tokens anywhere in
   the covered files and asserts each run is one of the derived sets. A partial
   list — the exact round-1 defect — fails on contents, no matter how it is worded
   or where it is added.

KNOWN HOLE, stated rather than left implicit. The COUNT test anchors on the
phrasings that exist today, and `test_no_unclassified_count_claim` sweeps for the
established claim SHAPES. A count written in a genuinely new sentence form ("the
CTO covers a dozen paths") is not caught. The enumeration axis has no such hole,
because it matches on paths rather than words. Closing the count hole means either
dropping the counts from prose entirely (GitLab #1's option 2) or generating them,
both of which are CPO calls that were considered and not taken.
"""

from __future__ import annotations

import json
import os
import re
import sys

import pytest

from test_governance_hooks import real_routing

REPO = os.path.normpath(os.path.join(os.path.dirname(__file__), ".."))


# --------------------------------------------------------------------------- #
# The two sources of truth. Read from the real files; never retyped here.
# --------------------------------------------------------------------------- #
def _contract_gate():
    """The hook module. Its `main()` is `__main__`-guarded, so importing is
    side-effect free — the same pattern `test_governance_hooks._gd()` uses for
    `git_discipline`."""
    sys.path.insert(0, os.path.join(REPO, ".claude", "hooks"))
    import task_contract_gate

    return task_contract_gate


def protected_paths() -> set[str]:
    """The protected set, normalised to the glob spelling routing uses.

    The gate stores directories as PREFIXES (`.claude/hooks/`) and single files
    verbatim; routing spells the same directories as globs (`.claude/hooks/**`).
    Same nine paths, two notations, which is precisely why a human restating
    either one gets it wrong."""
    gate = _contract_gate()
    return {p.rstrip("/") + "/**" for p in gate.PROTECTED_PREFIXES} | set(gate.PROTECTED_FILES)


def _routing_paths() -> dict:
    return real_routing()["paths"]


def shared_guard_paths() -> set[str]:
    """Guard paths where `platform-reviewer` is routed alongside the CTO."""
    rows = _routing_paths()
    return {p for p in protected_paths() if "platform-reviewer" in rows.get(p, [])}


def cto_alone_guard_paths() -> set[str]:
    return protected_paths() - shared_guard_paths()


def cto_routing_rows() -> set[str]:
    """Every routing row requiring the CTO. Wider than the guard set: it also
    carries the DEPENDENCY class (`*requirements*.txt`, the two site_v2 package
    files), which `north_star.md` counts alongside the guard paths."""
    return {p for p, revs in _routing_paths().items() if "cto-reviewer" in revs}


# --------------------------------------------------------------------------- #
# Text normalisation. See trap 1 in the module docstring.
# --------------------------------------------------------------------------- #
_BLOCKQUOTE = re.compile(r"^[>\s]*>\s?")

# Prose files whose text restates these facts. `test_every_file_stating_the_facts
# _is_covered` stops this list decaying as documents are added.
COVERED_FILES = (
    ".claude/agents/cto-reviewer.md",
    ".claude/agents/platform-reviewer.md",
    ".claude/review_routing.json",
    ".claude/task/TEMPLATE.md",
    "docs/working_agreement.md",
    "docs/agent_guardrails.md",
    "docs/roles/platform_reliability.md",
    "docs/north_star.md",
)

# Files that RECORD rather than GOVERN. A superseded number in one of these is the
# point of the file, not drift in it, and none of them is a rule anybody follows.
#   .claude/task/       per-task paperwork, replaced every task, including the
#                       append-only escalations.log of past CPO rulings
#   .claude/active_work.md  the handover, rewritten every session (routing files it
#                       under `artifact_only` for the same reason)
#   docs/audits/        dated snapshots of what was true on the day
#   tests/              this file, which quotes every claim shape it checks
SWEEP_EXEMPT = (".claude/task/", ".claude/active_work.md", "docs/audits/", "tests/")


def normalise(rel: str) -> str:
    """Whole-file text with blockquote markers stripped and whitespace collapsed.

    For JSON, only the `_doc*` narrative keys are read. The `paths` object is
    data, not prose — flattening it would hand the enumeration test a 30-entry
    "run" that is the routing table itself."""
    with open(os.path.join(REPO, rel), encoding="utf-8") as fh:
        raw = fh.read()
    if rel.endswith(".json"):
        doc = json.loads(raw)
        parts: list[str] = []
        for key, value in doc.items():
            if key.startswith("_doc"):
                parts.extend(value if isinstance(value, list) else [value])
        raw = " ".join(parts)
    lines = [_BLOCKQUOTE.sub("", ln).strip() for ln in raw.splitlines()]
    return re.sub(r"\s+", " ", " ".join(lines))


NUMBER_WORD = {
    "one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6,
    "seven": 7, "eight": 8, "nine": 9, "ten": 10, "eleven": 11, "twelve": 12,
}


def _as_int(token: str) -> int | None:
    token = token.strip().lower()
    if token.isdigit():
        return int(token)
    return NUMBER_WORD.get(token)


# --------------------------------------------------------------------------- #
# Test 1 — the identity every "nine" depends on.
# --------------------------------------------------------------------------- #
def test_every_protected_path_is_routed_to_the_cto():
    """A guard path is a PROTECTED path that routes to `cto-reviewer`, and the
    docs use the two terms interchangeably. That only holds while the sets agree.

    Add a protected path and forget its routing row and the prose "nine" silently
    means two different things in two places: nine files the gate blocks, eight
    the CTO reviews. This is the invariant the count tests below rest on, so it
    is asserted before them."""
    rows = _routing_paths()
    missing = sorted(p for p in protected_paths() if "cto-reviewer" not in rows.get(p, []))
    assert not missing, (
        "PROTECTED paths with no `cto-reviewer` routing row: "
        f"{missing}. Every protected path must confer the CTO, or 'the nine guard "
        "paths' stops meaning one thing. Add the row to .claude/review_routing.json "
        "or remove the path from task_contract_gate.py."
    )


def test_the_guard_path_counts_are_what_the_docs_claim():
    """Pins the three derived numbers, so a change to either source shows up as a
    failure here naming the new value, not as eleven quietly stale documents."""
    assert len(protected_paths()) == 9, (
        f"The guard set is now {sorted(protected_paths())}. Every prose site saying "
        "'nine' is stale; the count tests below name each one.")
    assert len(shared_guard_paths()) == 3, (
        f"platform-reviewer now shares {sorted(shared_guard_paths())} with the CTO.")
    assert len(cto_alone_guard_paths()) == 6, (
        f"The CTO now reviews {sorted(cto_alone_guard_paths())} alone.")
    assert len(cto_routing_rows()) == 12, (
        f"The CTO now has {len(cto_routing_rows())} routing rows, which is what "
        "north_star.md's role table counts.")
    assert shared_guard_paths() == {
        ".claude/hooks/**", ".github/workflows/**", ".gitlab-ci.yml"}, (
        "The set platform-reviewer shares with the CTO changed. Widening it is a "
        "RECURRING COST (a second opus specialist on every commit touching those "
        "paths) and therefore CPO-class — .claude/review_routing.json's own _doc "
        "records a review round that failed for widening it without a cost approval."
    )


# --------------------------------------------------------------------------- #
# Test 2 — every prose COUNT, anchored.
# --------------------------------------------------------------------------- #
def _guard_total() -> int:
    return len(protected_paths())


def _shared() -> int:
    return len(shared_guard_paths())


def _cto_alone() -> int:
    return len(cto_alone_guard_paths())


def _cto_rows() -> int:
    return len(cto_routing_rows())


# (file, anchor, [expected-count callables, one per capture group]).
# Each anchor must match EXACTLY ONCE. That is the load-bearing half: reword the
# sentence and the test fails loudly with "matched 0 times" instead of silently
# checking nothing.
COUNT_SITES = (
    (".claude/agents/cto-reviewer.md",
     r"on any of the (\w+) guard paths", [_guard_total]),
    (".claude/agents/cto-reviewer.md",
     r"routed alongside you, also at opus, on exactly (\w+) of them", [_shared]),
    (".claude/agents/cto-reviewer.md",
     r"On the other (\w+) you are the only", [_cto_alone]),
    (".claude/agents/cto-reviewer.md",
     r"spawned at opus on all (\w+) guard paths", [_guard_total]),

    (".claude/agents/platform-reviewer.md",
     r"on the (\w+) guard paths you are routed to", [_shared]),
    (".claude/agents/platform-reviewer.md",
     r"NOT routed to the other (\w+) guard paths", [_cto_alone]),

    (".claude/review_routing.json",
     r"joins cto-reviewer on exactly (\w+) of the (\w+)", [_shared, _guard_total]),
    (".claude/review_routing.json", r"docs must say (\w+)", [_shared]),
    (".claude/review_routing.json", r"floor on those (\w+)", [_shared]),
    (".claude/review_routing.json",
     r"The other (\w+) go to cto-reviewer ALONE", [_cto_alone]),

    ("docs/working_agreement.md",
     r"means `cto-reviewer` on all (\w+),", [_guard_total]),
    ("docs/working_agreement.md",
     r"`platform-reviewer` on exactly (\w+) of them", [_shared]),
    ("docs/working_agreement.md",
     r"deliberately absent from the other (\w+),", [_cto_alone]),

    ("docs/agent_guardrails.md",
     r"That means `cto-reviewer` on all (\w+),", [_guard_total]),
    ("docs/agent_guardrails.md",
     r"plus `platform-reviewer` on exactly (\w+)\*\*", [_shared]),
    ("docs/agent_guardrails.md",
     r"Platform is absent from the other (\w+) by design", [_cto_alone]),

    ("docs/roles/platform_reliability.md",
     r"On exactly (\w+) of the (\w+) guard paths", [_shared, _guard_total]),
    ("docs/roles/platform_reliability.md",
     r"the other (\w+) it is not routed at all", [_cto_alone]),

    ("docs/north_star.md",
     r"\*\*(\d+) rows\*\*: the (\d+) guard paths", [_cto_rows, _guard_total]),
)


@pytest.mark.parametrize(
    "rel,anchor,expected", COUNT_SITES,
    ids=[f"{r}::{a[:34]}" for r, a, _ in COUNT_SITES])
def test_every_prose_count_matches_the_derived_value(rel, anchor, expected):
    text = normalise(rel)
    found = re.findall(anchor, text)
    assert len(found) == 1, (
        f"{rel}: the anchor {anchor!r} matched {len(found)} times, expected exactly 1. "
        "Either the sentence was reworded (update the anchor in COUNT_SITES, and check "
        "the number while you are there) or a second site now says the same thing "
        "(give it its own COUNT_SITES row)."
    )
    groups = found[0] if isinstance(found[0], tuple) else (found[0],)
    for token, want in zip(groups, expected):
        got, target = _as_int(token), want()
        assert got == target, (
            f"{rel} says {token!r} where the source gives {target}. "
            "The source is .claude/review_routing.json + task_contract_gate.py. "
            "Fix the prose, not the test — .claude/review_routing.json's _doc records "
            "a round that failed for widening the rows to match the prose instead."
        )


# --------------------------------------------------------------------------- #
# Test 3 — every prose LIST, matched on contents rather than phrasing.
# --------------------------------------------------------------------------- #
def _path_tokens() -> list[str]:
    """Both spellings of every protected path, longest first so `.claude/hooks/**`
    is consumed before the `.claude/hooks/` prefix inside it."""
    tokens = set()
    for glob in protected_paths():
        tokens.add(glob)
        if glob.endswith("/**"):
            tokens.add(glob[:-2])
    return sorted(tokens, key=len, reverse=True)


# A gap wider than this ends a list. Sized against the real files: the widest
# real separator is "`, `.claude/review_routing.json`, `" plus a stray "and".
_RUN_GAP = 42


def _runs(text: str) -> list[tuple[int, frozenset]]:
    """Every maximal run of adjacent protected-path mentions, as path SETS."""
    hits = []
    for token in _path_tokens():
        for m in re.finditer(re.escape(token), text):
            hits.append((m.start(), m.end(), token))
    hits.sort()
    kept: list[tuple[int, int, str]] = []
    for start, end, token in hits:
        if kept and start < kept[-1][1]:
            continue  # inside a longer token already taken
        kept.append((start, end, token))

    runs, current, start_at, last_end = [], set(), None, None
    for start, end, token in kept:
        canonical = token if token in protected_paths() else token + "**"
        if last_end is not None and start - last_end > _RUN_GAP:
            if len(current) > 1:
                runs.append((start_at, frozenset(current)))
            current, start_at = set(), None
        if start_at is None:
            start_at = start
        current.add(canonical)
        last_end = end
    if len(current) > 1:
        runs.append((start_at, frozenset(current)))
    return runs


# Runs that are prose ARGUMENTS rather than enumerations of the guard set. Scoped
# to the file that makes the argument, so the same subset staying legitimate in one
# document does not quietly excuse it appearing in another.
PROSE_SUBSETS = {
    ".claude/agents/cto-reviewer.md": {
        frozenset({".claude/settings.json", ".mcp.json", ".cursor/mcp.json"}):
            "the config trio that carries env blocks and tokens",
    },
    ".claude/review_routing.json": {
        frozenset({".mcp.json", ".cursor/mcp.json"}):
            "the two MCP entry points, ruled command-class together (CPO 2026-06-18)",
        frozenset({".claude/commands/**", ".mcp.json", ".cursor/mcp.json"}):
            "the same ruling, cited by the paths it covers",
        frozenset({".github/workflows/**", ".gitlab-ci.yml"}):
            "the CI pair either side of the 2026-08 migration",
        frozenset({".claude/settings.json", ".mcp.json", ".cursor/mcp.json"}):
            "the config trio, on why settings.json was already protected",
    },
    "docs/working_agreement.md": {
        frozenset({".claude/settings.json", ".mcp.json", ".cursor/mcp.json"}):
            "the config trio, on why an mcpServers block is command-class",
    },
    "docs/agent_guardrails.md": {
        frozenset({".claude/commands/**", ".mcp.json"}):
            "two CPO rulings cited by the paths they were about",
        frozenset({".claude/hooks/**", ".claude/settings.json"}):
            "where a project hook lives and where it is wired",
    },
    "docs/roles/platform_reliability.md": {
        frozenset({".claude/hooks/**", ".github/workflows/**"}):
            "the CTO's PRE-split routing, described in the past tense",
    },
}

# Real incomplete lists that cannot be fixed from the task that finds them —
# typically because they sit on a PROTECTED path and correcting one needs a
# CPO-approved governance task carrying `protected_override`. Recorded rather than
# exempted, and `test_known_incomplete_lists_have_not_been_fixed` fails the moment
# one IS corrected, so an entry cannot outlive its defect.
#
# EMPTY IS THE CORRECT STEADY STATE, and it got here the intended way. The single
# entry recorded the `platform-reviewer.md` territory sentence omitting
# `.gitlab-ci.yml` (GitLab #22, found by this file on its first run in #1). When
# that sentence was fixed under an override, the paired test went RED and named
# the entry to delete — the exemption could not outlive the defect, which is the
# whole point of the pair. Add an entry only when a real incomplete list genuinely
# cannot be fixed in the same task, and expect the pair to retire it for you.
KNOWN_INCOMPLETE: dict = {}


def _allowed_runs(rel: str) -> dict:
    """Every path set a run in this file may legitimately be. A run that is none of
    them is a partial or drifted list."""
    allowed = {
        frozenset(protected_paths()): "all nine guard paths",
        frozenset(cto_alone_guard_paths()): "the six the CTO reviews alone",
        frozenset(shared_guard_paths()): "the three platform shares",
    }
    allowed.update(PROSE_SUBSETS.get(rel, {}))
    return allowed


@pytest.mark.parametrize("rel", COVERED_FILES)
def test_every_protected_path_list_is_complete(rel):
    """Catches the round-1 defect directly: a list that dropped a path.

    Deliberately NOT a table of known sites. It reads whatever lists are actually
    in the file, so a new list added anywhere in a covered document is checked the
    moment it appears, and no site table can go stale."""
    text = normalise(rel)
    allowed = _allowed_runs(rel)
    for position, run in _runs(text):
        if (rel, run) in KNOWN_INCOMPLETE:
            continue
        assert run in allowed, (
            f"{rel}: a list of protected paths near {text[max(0, position - 70):position + 190]!r}\n"
            f"  holds {sorted(run)}\n"
            f"  which is no derived set. Missing from the full nine: "
            f"{sorted(protected_paths() - run) or 'nothing'}. "
            "Complete the list, or add it to PROSE_SUBSETS with the reason it is "
            "legitimately a subset."
        )


@pytest.mark.parametrize("key", sorted(KNOWN_INCOMPLETE, key=str),
                         ids=[k[0] for k in sorted(KNOWN_INCOMPLETE, key=str)])
def test_known_incomplete_lists_have_not_been_fixed(key):
    """The other direction, so a recorded defect cannot outlive itself.

    An exemption that survives the thing it excuses is how a list of known issues
    becomes a list of silently-allowed ones. When the prose is corrected this test
    goes red and says to delete the entry."""
    rel, run = key
    assert any(r == run for _, r in _runs(normalise(rel))), (
        f"{rel} no longer contains the incomplete list {sorted(run)}. If it was "
        f"fixed, delete this entry from KNOWN_INCOMPLETE.\n  Recorded reason: "
        f"{KNOWN_INCOMPLETE[key]}"
    )


def test_the_platform_role_row_names_only_the_shared_guard_paths():
    """`north_star.md`'s "Wakes on" column is read as the authority on what routes
    a role, and its own preamble attaches a duty to keeping it honest. A guard path
    listed there that platform is not routed to would over-state its surface."""
    text = normalise("docs/north_star.md")
    row = re.search(r"\| \[Platform and Reliability\][^|]*\|[^|]*\|([^|]*)\|", text)
    assert row, "The Platform and Reliability row is no longer parseable in north_star.md."
    named = {p for p in protected_paths() if p in row.group(1)}
    assert named == shared_guard_paths(), (
        f"north_star.md's Platform row names guard paths {sorted(named)}, "
        f"but routing gives it {sorted(shared_guard_paths())}."
    )


# --------------------------------------------------------------------------- #
# Test 4 — nothing states these facts outside the checks above.
# --------------------------------------------------------------------------- #
# The claim SHAPES in use. Every match must be covered by COUNT_SITES or listed
# in HISTORICAL. See the known hole in the module docstring.
CLAIM_SHAPES = (
    r"\b(\w+) guard paths?\b",
    r"`cto-reviewer` on all (\w+)",
    r"`platform-reviewer` on exactly (\w+)",
    r"on exactly (\w+) of them",
    r"other (\w+) go to cto-reviewer",
)

# Superseded numbers quoted ON PURPOSE, as the record of a churn worth keeping.
# Exact snippets: a real regression cannot hide behind a loose pattern.
HISTORICAL = (
    "three documents claiming BOTH reviewers on all EIGHT guard paths",
    'three documents claiming "both on all eight"',
    "this returns to eight paths and TWO",
    "platform is routed to only two of the eight guard paths",
    "spawned at **opus** on all eight",
)


@pytest.mark.parametrize("rel", COVERED_FILES)
def test_no_unclassified_count_claim(rel):
    text = normalise(rel)
    anchored = {a for r, a, _ in COUNT_SITES if r == rel}
    covered = []
    for anchor in anchored:
        covered.extend((m.start(), m.end()) for m in re.finditer(anchor, text))
    for snippet in HISTORICAL:
        covered.extend((m.start(), m.end()) for m in re.finditer(re.escape(snippet), text))

    for shape in CLAIM_SHAPES:
        for m in re.finditer(shape, text):
            if _as_int(m.group(1)) is None:
                continue  # "the guard paths", "those guard paths" — no number claimed
            if any(lo <= m.start() and m.end() <= hi for lo, hi in covered):
                continue
            pytest.fail(
                f"{rel}: unclassified count claim {m.group(0)!r} at {m.start()}\n"
                f"  context: ...{text[max(0, m.start() - 90):m.end() + 90]}...\n"
                "  Add a COUNT_SITES row if it is a live claim, or a HISTORICAL entry "
                "if it deliberately quotes a superseded number."
            )


def test_every_file_stating_the_facts_is_covered():
    """Stops COVERED_FILES decaying. A document added tomorrow that restates the
    guard-path facts joins the checks above automatically, instead of becoming a
    twelfth unchecked site."""
    import subprocess

    out = subprocess.run(
        ["git", "grep", "-l", "-i", "-e", "guard path", "-e", "protected path", "--", "."],
        capture_output=True, text=True, cwd=REPO)
    assert out.returncode in (0, 1), f"git grep failed: {out.stderr}"
    found = {p.replace("\\", "/") for p in out.stdout.split() if p}
    uncovered = sorted(
        p for p in found
        if p not in COVERED_FILES
        and not any(p.startswith(x) for x in SWEEP_EXEMPT)
        and not p.startswith(".claude/hooks/")  # the gates themselves; code, not prose
        and p != "CLAUDE.md"                    # orientation; states no count
    )
    assert not uncovered, (
        f"These files mention guard/protected paths but are not in COVERED_FILES: "
        f"{uncovered}. Add them so their claims are checked, or add them to "
        "SWEEP_EXEMPT with the reason."
    )
