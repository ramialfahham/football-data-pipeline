"""The tracker's backup in the repo has one writer — the guard, both halves.

`docs/tracker/gitlab_snapshot.md` is written only by `scripts/snapshot_tracker.py`. Half one is
`.claude/hooks/tracker_snapshot_gate.py`, which denies an `Edit`, `Write` or `MultiEdit` under
`docs/tracker/`. Half two is the checksum pin below: the header's sha256 must equal the body's,
so any change that did not also rewrite the header fails CI. That is self-consistency, not
provenance — a deliberate shell write that recomputes the header passes, and is forbidden by
rule. The routing entries keep a refresh out of the review patch and the review hash, so the
file is never a reviewed diff — which is exactly why nothing else may touch it.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import sys

import pytest

REPO = os.path.normpath(os.path.join(os.path.dirname(__file__), ".."))
HOOKS = os.path.join(REPO, ".claude", "hooks")
sys.path.insert(0, HOOKS)
import tracker_snapshot_gate as gate  # noqa: E402

sys.path.insert(0, os.path.join(REPO, "scripts"))
import snapshot_tracker  # noqa: E402

HOOK = os.path.join(HOOKS, "tracker_snapshot_gate.py")
SNAPSHOT = os.path.join(REPO, "docs", "tracker", "gitlab_snapshot.md")
HEADER_RE = re.compile(r"<!-- snapshot: (\d{4}-\d\d-\d\d \d\d:\d\d UTC) · sha256\(body\): ([0-9a-f]{64}) -->")


def _split(text: str) -> tuple[str, str]:
    head, _, body = text.partition("\n\n")
    return head, body


# ---------------------------------------------------------------- the checksum pin

def test_the_committed_snapshot_is_exactly_what_the_script_wrote():
    with open(SNAPSHOT, encoding="utf-8") as f:
        text = f.read()
    head, body = _split(text)
    assert snapshot_tracker.BANNER in head, "the banner names the file for what it is"
    m = HEADER_RE.search(head)
    assert m, "the header carries the UTC stamp and the body's sha256"
    assert hashlib.sha256(body.encode("utf-8")).hexdigest() == m.group(2), (
        "the body was changed without rewriting the header — regenerate with scripts/snapshot_tracker.py")


def test_a_single_character_change_breaks_the_checksum(tmp_path):
    with open(SNAPSHOT, encoding="utf-8") as f:
        text = f.read()
    head, body = _split(text)
    digest = HEADER_RE.search(head).group(2)
    mutated = body[:200] + ("x" if body[200] != "x" else "y") + body[201:]
    assert hashlib.sha256(mutated.encode("utf-8")).hexdigest() != digest


def test_render_is_deterministic_and_groups_by_milestone():
    milestones = [{"id": 2, "iid": 2, "title": "2 · B", "state": "active", "description": "b"},
                  {"id": 1, "iid": 1, "title": "1 · A", "state": "active", "description": "a"}]
    issues = [
        {"iid": 5, "title": "five", "state": "opened", "created_at": "2026-09-01T00:00:00Z",
         "labels": [], "description": "body 5", "milestone": {"id": 2}},
        {"iid": 3, "title": "three", "state": "closed", "created_at": "2026-08-01T00:00:00Z",
         "closed_at": "2026-08-02T00:00:00Z", "labels": ["bug"], "description": "body 3",
         "milestone": {"id": 1}},
        {"iid": 4, "title": "four", "state": "opened", "created_at": "2026-08-01T00:00:00Z",
         "labels": [], "description": "", "milestone": None},
    ]
    a = snapshot_tracker.render(milestones, issues)
    b = snapshot_tracker.render(list(reversed(milestones)), list(reversed(issues)))
    assert a == b, "input order must not change the output"
    assert a.index("## 1 · A") < a.index("### #3 three") < a.index("## 2 · B") < a.index("### #5 five")
    assert a.index("## No milestone") < a.index("### #4 four")
    assert "closed · created 2026-08-01 · closed 2026-08-02 · labels: bug" in a


# ---------------------------------------------------------------- the hook as the harness runs it

def _run(event, repo: str) -> str:
    env = dict(os.environ, CLAUDE_PROJECT_DIR=repo)
    r = subprocess.run([sys.executable, HOOK],
                       input=event if isinstance(event, str) else json.dumps(event),
                       capture_output=True, text=True, cwd=repo, env=env, timeout=60)
    assert r.returncode == 0, r.stderr
    return r.stdout


def _denied(out: str) -> bool:
    return '"permissionDecision": "deny"' in out


@pytest.fixture
def repo(tmp_path):
    (tmp_path / "docs" / "tracker").mkdir(parents=True)
    (tmp_path / "docs" / "tracker" / "gitlab_snapshot.md").write_text("x\n", encoding="utf-8")
    return tmp_path


@pytest.mark.parametrize("tool,extra", [
    ("Write", {"content": "hand edit\n"}),
    ("Edit", {"old_string": "x", "new_string": "y"}),
    ("MultiEdit", {"edits": [{"old_string": "x", "new_string": "y"}]}),
])
def test_every_write_under_the_folder_is_denied(repo, tool, extra):
    path = str(repo / "docs" / "tracker" / "gitlab_snapshot.md")
    out = _run({"tool_name": tool, "tool_input": {"file_path": path, **extra}}, str(repo))
    assert _denied(out)
    reason = json.loads(out)["hookSpecificOutput"]["permissionDecisionReason"]
    assert "scripts/snapshot_tracker.py" in reason


@pytest.mark.parametrize("spelling", ["Docs/Tracker", "DOCS/TRACKER", "docs/Tracker"])
def test_a_differently_cased_spelling_of_the_folder_is_denied(repo, spelling):
    """On Windows these name the same folder as `docs/tracker`, and relpath keeps the caller's
    case past the shared prefix — so the check must fold case or the hook is a spelling away
    from silent."""
    path = os.path.join(str(repo), *spelling.split("/"), "gitlab_snapshot.md")
    assert _denied(_run({"tool_name": "Write", "tool_input": {"file_path": path, "content": "n"}}, str(repo)))


def test_a_new_file_under_the_folder_is_denied_too(repo):
    path = str(repo / "docs" / "tracker" / "notes.md")
    assert _denied(_run({"tool_name": "Write", "tool_input": {"file_path": path, "content": "n"}}, str(repo)))


@pytest.mark.parametrize("rel", ["docs/north_star.md", "docs/trackers/x.md", "README.md",
                                 ".claude/task/review.md", "scripts/snapshot_tracker.py"])
def test_every_other_path_passes(repo, rel):
    path = str(repo / rel)
    assert _run({"tool_name": "Write", "tool_input": {"file_path": path, "content": "ok"}}, str(repo)) == ""


def test_a_path_outside_the_repo_passes(repo, tmp_path_factory):
    outside = tmp_path_factory.mktemp("elsewhere") / "docs" / "tracker" / "gitlab_snapshot.md"
    outside.parent.mkdir(parents=True)
    assert _run({"tool_name": "Write", "tool_input": {"file_path": str(outside), "content": "ok"}}, str(repo)) == ""


@pytest.mark.parametrize("junk", ["", "not json", "null", "[]", '{"tool_name": 5}',
                                  '{"tool_input": {"file_path": 3}}'])
def test_malformed_input_fails_open(junk, repo):
    assert _run(junk, str(repo)) == ""


def test_is_governed_is_the_same_test_the_hook_uses(repo, monkeypatch):
    monkeypatch.setenv("CLAUDE_PROJECT_DIR", str(repo))
    assert gate.is_governed(str(repo / "docs" / "tracker" / "gitlab_snapshot.md"))
    assert not gate.is_governed(str(repo / "docs" / "tracker.md"))


# ---------------------------------------------------------------- wiring and routing

def test_the_hook_is_wired_beside_the_other_edit_time_gates():
    with open(os.path.join(REPO, ".claude", "settings.json"), encoding="utf-8") as f:
        settings = json.load(f)
    groups = [g for g in settings["hooks"]["PreToolUse"]
              if any("tracker_snapshot_gate.py" in h["command"] for h in g["hooks"])]
    assert len(groups) == 1
    assert set(groups[0]["matcher"].split("|")) >= {"Edit", "Write", "MultiEdit"}


def test_a_snapshot_refresh_is_never_a_reviewed_diff():
    """The three routing lists: excluded from the hash, excluded from the patch, artifact-only
    for the commit gate — and never in `artifact_only_never`, which would make it reviewed."""
    with open(os.path.join(REPO, ".claude", "review_routing.json"), encoding="utf-8") as f:
        routing = json.load(f)
    for key in ("hash_exclude_paths", "review_exclude_paths", "artifact_only"):
        assert "docs/tracker/**" in routing[key], key
    assert not any(p.startswith("docs/tracker") for p in routing["artifact_only_never"])
