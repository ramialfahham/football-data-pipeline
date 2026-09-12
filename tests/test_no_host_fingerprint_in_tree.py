"""A live host's network address has no place in the repo — the guard, both halves.

Half one is `.claude/hooks/host_fingerprint_gate.py`: it denies an `Edit`, `Write` or
`MultiEdit` whose written text puts a public IPv4 or IPv6 literal into any file inside the repo,
task artifacts included. Half two is the pin below: the tracked tree holds zero such literals,
and this test fails the build if one appears.

Everything here imports the hook's own patterns and range test, so the CI count and the
edit-time deny cannot drift apart. Every sample address is BUILT at runtime from integers, never
written as a literal, because a literal public address in this file would itself be a flagged
line — the hook reads text, not intent, and this file is inside the repo.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys

import pytest

REPO = os.path.normpath(os.path.join(os.path.dirname(__file__), ".."))
HOOKS = os.path.join(REPO, ".claude", "hooks")
sys.path.insert(0, HOOKS)
import host_fingerprint_gate as gate  # noqa: E402

HOOK = os.path.join(HOOKS, "host_fingerprint_gate.py")


def v4(*octets: int) -> str:
    return ".".join(str(o) for o in octets)


def v6(*groups: str) -> str:
    return ":".join(groups)


PUBLIC_V4 = v4(203, 0, 113, 7)            # the documentation range: public-shaped, nobody's host
PUBLIC_V6 = v6("2a01", "4f9", "c013", "24af", "", "1")


def _run(event, cwd: str) -> str:
    env = dict(os.environ, CLAUDE_PROJECT_DIR=cwd)
    r = subprocess.run(
        [sys.executable, HOOK],
        input=event if isinstance(event, str) else json.dumps(event),
        capture_output=True, text=True, cwd=cwd, env=env, timeout=60,
    )
    assert r.returncode == 0, r.stderr
    return r.stdout


def _denied(out: str) -> bool:
    return '"permissionDecision": "deny"' in out


def _write_event(path: str, content: str) -> dict:
    return {"hook_event_name": "PreToolUse", "tool_name": "Write",
            "tool_input": {"file_path": path, "content": content}}


# ---------------------------------------------------------------- the pattern, both ways

@pytest.mark.parametrize("literal", [
    PUBLIC_V4,
    v4(8, 8, 8, 8),
    v4(37, 27, 14, 1),
    v4(172, 32, 0, 1),                    # one past the private block
    v4(1, 2, 3, 4),                       # the accepted false positive: a bare version string
])
def test_a_public_ipv4_is_flagged(literal):
    assert list(gate.flagged_lines(f"host {literal} here")) == [(1, "IPv4")]


@pytest.mark.parametrize("template", [
    "The runner's address is {}.",          # glued to a full stop — the ordinary prose case
    "({})",
    "`{}`",
    "{}:22",
    "http://{}/path",
    "{}",
    "address={}",
    "at {},",
])
def test_a_public_ipv4_is_flagged_whatever_surrounds_it(template):
    assert list(gate.flagged_lines(template.format(PUBLIC_V4))) == [(1, "IPv4")]


@pytest.mark.parametrize("literal", [
    v4(127, 0, 0, 1),
    v4(10, 1, 2, 3),
    v4(172, 16, 0, 1),
    v4(172, 31, 255, 255),
    v4(192, 168, 1, 1),
    v4(169, 254, 1, 1),
    v4(224, 0, 0, 1),
    v4(0, 0, 0, 0),
    v4(255, 255, 255, 255),
])
def test_a_non_public_ipv4_passes(literal):
    assert gate.IPV4.search(literal), "the pattern must SEE it — the range test is what passes it"
    assert list(gate.flagged_lines(f"bind {literal}")) == []


@pytest.mark.parametrize("text", [
    "version 1.7.19 of the tool",
    "v" + v4(1, 2, 3, 4) + "-rc1",
    "at 2026-09-12 07:51:22",
    "the score was 3.2.1",
    v4(256, 1, 1, 1),
    v4(1, 2, 3, 4) + ".5",
])
def test_things_shaped_like_numbers_but_not_addresses_pass(text):
    assert list(gate.flagged_lines(text)) == []


def test_a_global_ipv6_is_flagged_and_short_colon_runs_are_not():
    assert list(gate.flagged_lines("box " + PUBLIC_V6)) == [(1, "IPv6")]
    assert list(gate.flagged_lines(v6("2001", "db8", "", "1"))) == [(1, "IPv6")]
    assert list(gate.flagged_lines("at 2026:12:30 it ran")) == []
    assert list(gate.flagged_lines("fe80::1 is link-local")) == []
    assert list(gate.flagged_lines("sha " + "2a01" + "4f9c" * 8)) == []


def test_line_numbers_and_kinds_are_reported_per_line():
    text = f"one\n{PUBLIC_V4}\nthree\n{PUBLIC_V6}\n"
    assert list(gate.flagged_lines(text)) == [(2, "IPv4"), (4, "IPv6")]


# ---------------------------------------------------------------- the hook as the harness runs it

@pytest.fixture
def repo(tmp_path):
    (tmp_path / ".claude" / "task").mkdir(parents=True)
    (tmp_path / "docs").mkdir()
    return tmp_path


@pytest.mark.parametrize("rel", ["docs/operations_guide.md", ".claude/task/review.md",
                                 "scripts/x.py", "README.md"])
def test_a_public_address_is_denied_anywhere_inside_the_repo(repo, rel):
    out = _run(_write_event(str(repo / rel), f"the box is at {PUBLIC_V4}\n"), str(repo))
    assert _denied(out)
    reason = json.loads(out)["hookSpecificOutput"]["permissionDecisionReason"]
    assert rel.replace("\\", "/") in reason and "line 1 (IPv4)" in reason
    assert PUBLIC_V4 not in reason, "the deny must not echo the value"


def test_an_edit_and_a_multiedit_are_checked_on_their_new_strings(repo):
    path = str(repo / "docs" / "x.md")
    edit = {"hook_event_name": "PreToolUse", "tool_name": "Edit",
            "tool_input": {"file_path": path, "old_string": "a", "new_string": PUBLIC_V6}}
    multi = {"hook_event_name": "PreToolUse", "tool_name": "MultiEdit",
             "tool_input": {"file_path": path, "edits": [
                 {"old_string": "a", "new_string": "fine"},
                 {"old_string": "b", "new_string": f"at {PUBLIC_V4}"}]}}
    assert _denied(_run(edit, str(repo)))
    assert _denied(_run(multi, str(repo)))


def test_a_loopback_or_private_address_passes(repo):
    text = f"serve on {v4(127, 0, 0, 1)}:8899 and {v4(192, 168, 0, 10)}\n"
    assert _run(_write_event(str(repo / "docs" / "x.md"), text), str(repo)) == ""


def test_a_path_outside_the_repo_is_not_governed(repo, tmp_path_factory):
    outside = tmp_path_factory.mktemp("memory") / "note.md"
    assert _run(_write_event(str(outside), f"box {PUBLIC_V4}\n"), str(repo)) == ""


@pytest.mark.parametrize("junk", ["", "not json", "null", "[]", '{"tool_name": 5}',
                                  '{"tool_input": {"file_path": 3}}'])
def test_malformed_input_fails_open(junk, repo):
    assert _run(junk, str(repo)) == ""


def test_the_hook_is_wired_beside_the_other_edit_time_gates():
    with open(os.path.join(REPO, ".claude", "settings.json"), encoding="utf-8") as f:
        settings = json.load(f)
    groups = [g for g in settings["hooks"]["PreToolUse"]
              if any("host_fingerprint_gate.py" in h["command"] for h in g["hooks"])]
    assert len(groups) == 1
    assert set(groups[0]["matcher"].split("|")) >= {"Edit", "Write", "MultiEdit"}


# ---------------------------------------------------------------- the pin

def _tracked_text_files() -> list[str]:
    out = subprocess.run(["git", "ls-files", "-z"], cwd=REPO, capture_output=True,
                         text=True, check=True).stdout
    return [p for p in out.split("\0") if p]


def _scan_tree() -> tuple[list[tuple[str, int]], list[tuple[str, int]]]:
    """(public hits, non-public IPv4 sightings) over every tracked text file."""
    public, seen = [], []
    for rel in _tracked_text_files():
        path = os.path.join(REPO, rel)
        try:
            with open(path, "rb") as f:
                raw = f.read()
        except OSError:
            continue
        if b"\0" in raw:
            continue
        text = raw.decode("utf-8", errors="replace")
        for n, _kind in gate.flagged_lines(text):
            public.append((rel, n))
        for n, line in enumerate(text.splitlines(), 1):
            if gate.IPV4.search(line) and not any(
                    gate.ipv4_is_public(m.group(0)) for m in gate.IPV4.finditer(line)):
                seen.append((rel, n))
    return public, seen


def test_the_tracked_tree_holds_no_public_address():
    """The pin, measured two-sided: zero public literals, and the walk is proven to see files by
    the non-public address lines it passes over (today the mocks README's loopback preview
    server) — at least one, wherever the tree happens to keep them."""
    public, seen = _scan_tree()
    assert public == [], f"public address literals in the tree: {public}"
    assert seen, "the walk saw no address-shaped line at all — is it reading the tree?"


def test_definition_is_imported_not_copied():
    """This file must not carry its own address pattern — every check above goes through the
    hook's `IPV4`, `IPV6` and `ipv4_is_public`, so a change to the definition changes the pin."""
    with open(__file__, encoding="utf-8") as f:
        src = f.read()
    assert "import host_fingerprint_gate as gate" in src
    compiled = "re." + "compile("
    assert compiled not in src.replace('"re." + "compile("', "")
    assert ("def " + "ipv4_is_public") not in src
