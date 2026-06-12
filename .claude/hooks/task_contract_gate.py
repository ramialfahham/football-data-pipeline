#!/usr/bin/env python
"""Task-contract gate (governance G2).

Drift is made mechanically impossible: every unit of work declares a contract
(`.claude/task/contract.md`) with a file-scope allowlist, and this gate denies:

  PreToolUse Edit|Write|MultiEdit
    - any repo-file edit when no contract exists
    - any edit outside the contract's scope_paths
    - edits to PROTECTED paths (the guards themselves) unless the contract
      carries an explicit `protected_override` naming the CPO approval
    - edits to the contract itself while the tree is dirty (clean-tree rule:
      amendments are discrete events, never mixed into code changes)

  PreToolUse Bash (best effort — shell is not fully parseable)
    - script heredocs (`python - <<EOF` …) that bypass the Edit-tool gates
    - write operators (>, >>, tee, sed -i) targeting repo files outside scope

  PostToolUse Bash (the ironclad net)
    - after every shell command, `git status` is compared against the contract;
      out-of-scope modifications trigger a prescriptive reversion instruction.

Paths OUTSIDE the repo are not governed (memory, plan files, temp). Fails OPEN
on unexpected errors (house rule) — the Stop gate and the PR artifact trail are
the backstops. See docs/working_agreement.md §2/§10 and docs/agent_guardrails.md.
"""

from __future__ import annotations

import fnmatch
import os
import re
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _command_utils import (  # noqa: E402
    bash_command,
    emit_context,
    emit_deny,
    read_event,
    strip_quoted_and_heredoc,
)

CONTRACT_REL = ".claude/task/contract.md"
TASK_DIR_REL = ".claude/task/"
# .claude/agents/ added per the CPO's recorded escalation answer (G3 review,
# 2026-06-12): the reviewer definitions are governance artifacts like the
# routing file — the builder must never be able to weaken its own adversary
# inside an ordinary task contract.
PROTECTED_PREFIXES = (".claude/hooks/", ".claude/agents/", ".github/workflows/")
PROTECTED_FILES = (".claude/settings.json", ".claude/review_routing.json")

_EDIT_TOOLS = {"Edit", "Write", "MultiEdit", "NotebookEdit"}

# Interpreter heredocs can write arbitrary files, bypassing the Edit gates.
_SCRIPT_HEREDOC = re.compile(r"\b(python3?|node|perl|ruby|php)\b[^|;&\n]*<<")
# Write operators on the quote/heredoc-stripped command text.
_REDIRECT = re.compile(r"(?<![0-9<>&])>{1,2}\s*([^\s;|&)]+)")
_TEE = re.compile(r"\btee\s+(?:-a\s+)?([^\s;|&]+)")
_SED_I = re.compile(r"\bsed\s+(?:-[a-zA-Z]*\s+)*-i\b[^|;&]*?\s((?:[^\s;|&-][^\s;|&]*\s*)+)$")

_IGNORED_TARGETS = {"/dev/null", "$null", "nul"}


def _repo_root() -> str:
    return os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()


def _rel_in_repo(path: str, root: str) -> str | None:
    """Repo-relative forward-slash path, or None when outside the repo."""
    try:
        rel = os.path.relpath(os.path.abspath(path), os.path.abspath(root))
    except ValueError:                      # different drive on Windows
        return None
    rel = rel.replace("\\", "/")
    if rel.startswith(".."):
        return None
    return rel


def _read_contract(root: str) -> dict | None:
    """Parse the contract's scope_paths + protected_override. None when absent."""
    path = os.path.join(root, CONTRACT_REL)
    if not os.path.isfile(path):
        return None
    scope, in_scope_block, override = [], False, False
    try:
        for raw in open(path, encoding="utf-8", errors="replace"):
            line = raw.rstrip("\n")
            if re.match(r"^scope_paths\s*:", line):
                in_scope_block = True
                continue
            if in_scope_block:
                m = re.match(r"^\s+-\s+(\S+)", line)
                if m:
                    scope.append(m.group(1).replace("\\", "/"))
                    continue
                if line.strip() and not line.startswith((" ", "\t")):
                    in_scope_block = False
            if re.match(r"^protected_override\s*:", line):
                override = True
    except Exception:
        return None
    return {"scope": scope, "protected_override": override}


def _matches_scope(rel: str, scope: list[str]) -> bool:
    for pat in scope:
        if fnmatch.fnmatch(rel, pat):
            return True
        if pat.endswith("/") and rel.startswith(pat):
            return True
    return False


def _is_protected(rel: str) -> bool:
    return rel in PROTECTED_FILES or any(rel.startswith(p) for p in PROTECTED_PREFIXES)


def _dirty_outside_task_dir(root: str) -> list[str]:
    try:
        out = subprocess.run(
            ["git", "status", "--porcelain", "-uall"], cwd=root,
            capture_output=True, text=True, timeout=15,
        ).stdout
    except Exception:
        return []
    files = []
    for line in out.splitlines():
        f = line[3:].strip().strip('"').replace("\\", "/")
        if " -> " in f:
            f = f.split(" -> ")[-1]
        if f and not f.startswith(TASK_DIR_REL):
            files.append(f)
    return files


def _deny_no_contract(rel: str) -> None:
    emit_deny(
        f"CONTRACT GATE: no task contract exists, so `{rel}` may not be edited. "
        f"Write {CONTRACT_REL} first (objective, scope_paths, decisions_reserved, "
        "done_when — template: .claude/task/TEMPLATE.md), state it to the CPO, then "
        "proceed. See docs/working_agreement.md §2."
    )


def _deny_out_of_scope(rel: str) -> None:
    emit_deny(
        f"CONTRACT GATE: `{rel}` is OUTSIDE the contract's scope_paths. Out of "
        "contract = drift. Either stop and ask the CPO, or amend the contract "
        "(allowed only on a clean tree, recording the CPO authority in "
        "`amendments:`) and then proceed. See docs/working_agreement.md §2/§10."
    )


def _deny_protected(rel: str) -> None:
    emit_deny(
        f"CONTRACT GATE: `{rel}` is a PROTECTED governance path (the guards "
        "themselves). It is editable only in a dedicated CPO-approved governance "
        "task whose contract carries `protected_override` naming that approval. "
        "See docs/working_agreement.md §2."
    )


def _gate_file_edit(event: dict, root: str) -> None:
    path = (event.get("tool_input") or {}).get("file_path") or ""
    if not path:
        return
    rel = _rel_in_repo(path, root)
    if rel is None:                          # outside repo: memory, plans, temp
        return
    contract = _read_contract(root)

    if rel == CONTRACT_REL:
        dirty = _dirty_outside_task_dir(root)
        if dirty:
            emit_deny(
                "CONTRACT GATE: the contract may only be (re)written on a CLEAN "
                "tree — amendments are discrete events, never mixed into code "
                "changes. Dirty files: " + ", ".join(dirty[:10]) +
                ". Commit or revert them first. See docs/working_agreement.md §2."
            )
        return
    if rel.startswith(TASK_DIR_REL):
        return
    if _is_protected(rel):
        if contract and contract["protected_override"] and _matches_scope(rel, contract["scope"]):
            emit_context(
                "PreToolUse",
                f"CONTRACT GATE: protected path `{rel}` allowed via the contract's "
                "protected_override (CPO-approved governance task). This edit is "
                "part of the PR's audit trail.",
            )
            return
        _deny_protected(rel)
        return
    if contract is None:
        _deny_no_contract(rel)
        return
    if not _matches_scope(rel, contract["scope"]):
        _deny_out_of_scope(rel)
        return


def _shell_write_targets(cmd: str) -> list[str]:
    """Best-effort file targets of write operators in a shell command."""
    text = strip_quoted_and_heredoc(cmd)
    targets = []
    for m in _REDIRECT.finditer(text):
        targets.append(m.group(1))
    for m in _TEE.finditer(text):
        targets.append(m.group(1))
    for m in _SED_I.finditer(text):
        targets.extend(m.group(1).split())
    return [t for t in targets if t.lower() not in _IGNORED_TARGETS]


def _gate_bash_pre(event: dict, root: str) -> None:
    cmd = bash_command(event)
    if not cmd:
        return
    if _SCRIPT_HEREDOC.search(cmd):
        emit_deny(
            "CONTRACT GATE: script heredocs (`python - <<EOF` …) bypass the "
            "Edit-tool gates and are not allowed for file changes. Use the "
            "Edit/Write tools. See docs/working_agreement.md §2 (anti-pattern A5 "
            "family)."
        )
        return
    contract = _read_contract(root)
    for target in _shell_write_targets(cmd):
        if "$" in target or "`" in target:
            emit_deny(
                f"CONTRACT GATE: shell write with unparseable target `{target}` — "
                "the gate cannot verify its scope. Use the Edit/Write tools, or "
                "redirect to an absolute path outside the repo."
            )
            return
        rel = _rel_in_repo(target if os.path.isabs(target) else os.path.join(root, target), root)
        if rel is None or rel.startswith(TASK_DIR_REL):
            continue
        if _is_protected(rel) and not (contract and contract["protected_override"]):
            _deny_protected(rel)
            return
        if contract is None:
            _deny_no_contract(rel)
            return
        if not _matches_scope(rel, contract["scope"]):
            _deny_out_of_scope(rel)
            return


def _gate_bash_post(event: dict, root: str) -> None:
    """The ironclad net: after any shell command, flag out-of-scope changes."""
    contract = _read_contract(root)
    dirty = _dirty_outside_task_dir(root)
    if contract:
        violations = [
            f for f in dirty
            if not _matches_scope(f, contract["scope"])
            and not (_is_protected(f) and contract["protected_override"])
        ]
    else:
        violations = dirty
    if violations:
        emit_context(
            "PostToolUse",
            "CONTRACT GATE VIOLATION: files modified outside the contract scope: "
            + ", ".join(violations[:10])
            + ". Revert each with `git checkout -- <file>` (or add untracked "
            "files to the contract via a clean-tree amendment with CPO "
            "authority). You may not proceed to other work or end the turn "
            "until the tree matches the contract.",
        )


def main() -> int:
    event = read_event()
    root = _repo_root()
    try:
        hook = event.get("hook_event_name") or ""
        tool = event.get("tool_name") or ""
        if hook == "PostToolUse" and tool == "Bash":
            _gate_bash_post(event, root)
        elif tool in _EDIT_TOOLS:
            _gate_file_edit(event, root)
        elif tool == "Bash":
            _gate_bash_pre(event, root)
    except Exception:
        return 0                             # fail open (house rule)
    return 0


if __name__ == "__main__":
    sys.exit(main())
