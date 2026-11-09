"""Prose restating the guard-path counts and lists must agree with the routing file and the gate.

The count test anchors on today's phrasings, so a count in a new sentence form is not caught.
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
    """The hook module; importing it is side-effect free because `main()` is `__main__`-guarded."""
    sys.path.insert(0, os.path.join(REPO, ".claude", "hooks"))
    import task_contract_gate

    return task_contract_gate


def protected_paths() -> set[str]:
    """The protected set in routing's glob spelling; the gate stores directories as prefixes."""
    gate = _contract_gate()
    return {p.rstrip("/") + "/**" for p in gate.PROTECTED_PREFIXES} | set(gate.PROTECTED_FILES)


def _routing_paths() -> dict:
    return real_routing()["paths"]


def shared_guard_paths() -> set[str]:
    rows = _routing_paths()
    return {p for p in protected_paths() if "platform-reviewer" in rows.get(p, [])}


def cto_alone_guard_paths() -> set[str]:
    return protected_paths() - shared_guard_paths()


def cto_routing_rows() -> set[str]:
    """Every routing row requiring the CTO, wider than the guard set by the dependency class."""
    return {p for p, revs in _routing_paths().items() if "cto-reviewer" in revs}


# --------------------------------------------------------------------------- #
# Text normalisation: whole files, because a claim can straddle a line break.
# --------------------------------------------------------------------------- #
_BLOCKQUOTE = re.compile(r"^[>\s]*>\s?")

# Prose files whose text restates these facts.
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

# Files that record rather than govern, where a superseded number is not drift.
SWEEP_EXEMPT = (".claude/task/", ".claude/active_work.md", "docs/tracker/", "tests/")


def normalise(rel: str) -> str:
    """Whole-file prose, blockquotes stripped, whitespace collapsed; JSON gives `_doc*` keys."""
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
    "thirteen": 13, "fourteen": 14,
}


def _as_int(token: str) -> int | None:
    token = token.strip().lower()
    if token.isdigit():
        return int(token)
    return NUMBER_WORD.get(token)


# --------------------------------------------------------------------------- #
# Guard path identity and counts
# --------------------------------------------------------------------------- #
def test_every_protected_path_is_routed_to_the_cto():
    """The docs treat protected and guard paths as one set; the count tests rest on that."""
    rows = _routing_paths()
    missing = sorted(p for p in protected_paths() if "cto-reviewer" not in rows.get(p, []))
    assert not missing, (
        "PROTECTED paths with no `cto-reviewer` routing row: "
        f"{missing}. Every protected path must confer the CTO, or 'the fourteen guard "
        "paths' stops meaning one thing. Add the row to .claude/review_routing.json "
        "or remove the path from task_contract_gate.py."
    )


def test_the_guard_path_counts_are_what_the_docs_claim():
    """Pins the derived numbers so a source change fails here naming the new value."""
    assert len(protected_paths()) == 14, (
        f"The guard set is now {sorted(protected_paths())}. Every prose site saying "
        "'fourteen' is stale; the count tests below name each one.")
    assert len(shared_guard_paths()) == 7, (
        f"platform-reviewer now shares {sorted(shared_guard_paths())} with the CTO.")
    assert len(cto_alone_guard_paths()) == 7, (
        f"The CTO now reviews {sorted(cto_alone_guard_paths())} alone.")
    assert len(cto_routing_rows()) == 17, (
        f"The CTO now has {len(cto_routing_rows())} routing rows, which is what "
        "north_star.md's role table counts.")
    assert shared_guard_paths() == {
        ".claude/hooks/**", ".github/workflows/**", ".gitlab-ci.yml",
        "scripts/check_design_inventory.py", "scripts/check_page_css.py",
        "scripts/design_inventory.py", "tests/test_design_inventory.py"}, (
        "The set platform-reviewer shares with the CTO changed. Widening it is a "
        "RECURRING COST (a second opus specialist on every commit touching those "
        "paths) and therefore CPO-class — .claude/review_routing.json's own _doc "
        "records a review round that failed for widening it without a cost approval."
    )


# --------------------------------------------------------------------------- #
# Prose counts
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
# Each anchor must match exactly once, so a reworded sentence fails instead of checking nothing.
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
# Prose lists, matched on contents rather than phrasing
# --------------------------------------------------------------------------- #
def _path_tokens() -> list[str]:
    """Both spellings of every protected path, longest first so a glob beats its prefix."""
    tokens = set()
    for glob in protected_paths():
        tokens.add(glob)
        if glob.endswith("/**"):
            tokens.add(glob[:-2])
    return sorted(tokens, key=len, reverse=True)


# A gap wider than this ends a list.
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


# Runs that are prose arguments rather than enumerations of the guard set, scoped per file.
PROSE_SUBSETS = {
    ".claude/agents/cto-reviewer.md": {
        frozenset({".claude/settings.json", ".mcp.json", ".cursor/mcp.json"}):
            "the config trio that carries env blocks and tokens",
    },
    ".claude/agents/platform-reviewer.md": {
        frozenset({".claude/hooks/**", ".github/workflows/**", ".gitlab-ci.yml"}):
            "the territory sentence, whose `scripts/` and `tests/` already hold the design checks",
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
        frozenset({".claude/hooks/**", ".claude/settings.json"}):
            "where a project hook lives and where it is wired",
    },
    "docs/roles/platform_reliability.md": {
        frozenset({".claude/hooks/**", ".github/workflows/**"}):
            "the CTO's PRE-split routing, described in the past tense",
    },
}

# Incomplete lists that cannot be fixed in the same task, for example on a protected path; empty
# is the steady state, and test_known_incomplete_lists_have_not_been_fixed retires an entry.
KNOWN_INCOMPLETE: dict = {}


def _allowed_runs(rel: str) -> dict:
    """Every path set a run in this file may be; any other run is a partial or drifted list."""
    allowed = {
        frozenset(protected_paths()): "all fourteen guard paths",
        frozenset(cto_alone_guard_paths()): "the seven the CTO reviews alone",
        frozenset(shared_guard_paths()): "the seven platform shares",
    }
    allowed.update(PROSE_SUBSETS.get(rel, {}))
    return allowed


@pytest.mark.parametrize("rel", COVERED_FILES)
def test_every_protected_path_list_is_complete(rel):
    """Reads whatever lists the file holds, so a new list in a covered document is checked."""
    text = normalise(rel)
    allowed = _allowed_runs(rel)
    for position, run in _runs(text):
        if (rel, run) in KNOWN_INCOMPLETE:
            continue
        assert run in allowed, (
            f"{rel}: a list of protected paths near {text[max(0, position - 70):position + 190]!r}\n"
            f"  holds {sorted(run)}\n"
            f"  which is no derived set. Missing from the full fourteen: "
            f"{sorted(protected_paths() - run) or 'nothing'}. "
            "Complete the list, or add it to PROSE_SUBSETS with the reason it is "
            "legitimately a subset."
        )


@pytest.mark.parametrize("key", sorted(KNOWN_INCOMPLETE, key=str),
                         ids=[k[0] for k in sorted(KNOWN_INCOMPLETE, key=str)])
def test_known_incomplete_lists_have_not_been_fixed(key):
    """Fails once the recorded defect is corrected, so an exemption cannot outlive it."""
    rel, run = key
    assert any(r == run for _, r in _runs(normalise(rel))), (
        f"{rel} no longer contains the incomplete list {sorted(run)}. If it was "
        f"fixed, delete this entry from KNOWN_INCOMPLETE.\n  Recorded reason: "
        f"{KNOWN_INCOMPLETE[key]}"
    )


def test_the_platform_role_row_names_only_the_shared_guard_paths():
    text = normalise("docs/north_star.md")
    row = re.search(r"\| \[Platform and Reliability\][^|]*\|[^|]*\|([^|]*)\|", text)
    assert row, "The Platform and Reliability row is no longer parseable in north_star.md."
    named = {p for p in protected_paths() if p in row.group(1)}
    assert named == shared_guard_paths(), (
        f"north_star.md's Platform row names guard paths {sorted(named)}, "
        f"but routing gives it {sorted(shared_guard_paths())}."
    )


# --------------------------------------------------------------------------- #
# Unclassified claims
# --------------------------------------------------------------------------- #
# The claim shapes in use; every match must be covered by COUNT_SITES or HISTORICAL.
CLAIM_SHAPES = (
    r"\b(\w+) guard paths?\b",
    r"`cto-reviewer` on all (\w+)",
    r"`platform-reviewer` on exactly (\w+)",
    r"on exactly (\w+) of them",
    r"other (\w+) go to cto-reviewer",
)

# Superseded numbers quoted on purpose, as exact snippets so a regression cannot hide.
HISTORICAL = (
    "three documents claiming BOTH reviewers on all EIGHT guard paths",
    'three documents claiming "both on all eight"',
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
    """A document that restates the guard-path facts must be in COVERED_FILES."""
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
