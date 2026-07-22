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
    - any edit on the STRUCTURAL SURFACE (raw writers `ingestion/**`, dbt models
      `dbt_project/models/**`, consumption `scripts/export_*.py` / `site*/`) when
      the contract carries no non-placeholder `impact_map` — the end-to-end
      blast-radius map must precede the first structural edit, so diagnosis
      happens before code, not one layer downstream at a time (#518, Appendix A6)

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
# inside an ordinary task contract. .claude/commands/ added per the CPO ruling
# 2026-06-14 (this branch's escalations.log): custom slash commands can embed
# shell, so a command file is the same high-stakes class as a hook — never add
# one inside an ordinary task without protected_override + cto review.
# .mcp.json + .cursor/mcp.json added per the CPO ruling 2026-06-18 (this
# conversation): an MCP-server config auto-launches a command (`uvx dbt-mcp` …)
# every session — the same command-class as .claude/commands/, so it is
# guard-level. No agent may self-grant an MCP server inside an ordinary task;
# it needs protected_override + cto review. Both the Claude Code (.mcp.json)
# and Cursor (.cursor/mcp.json) entry points are covered; .claude/settings.json
# (which can also carry an mcpServers block) is already PROTECTED below.
PROTECTED_PREFIXES = (".claude/hooks/", ".claude/agents/", ".claude/commands/", ".github/workflows/")
PROTECTED_FILES = (
    ".claude/settings.json",
    ".claude/review_routing.json",
    ".mcp.json",
    ".cursor/mcp.json",
)

_EDIT_TOOLS = {"Edit", "Write", "MultiEdit", "NotebookEdit"}

# Interpreter heredocs can write arbitrary files, bypassing the Edit gates.
_SCRIPT_HEREDOC = re.compile(r"\b(python3?|node|perl|ruby|php)\b[^|;&\n]*<<")
# Write operators on the quote/heredoc-stripped command text.
_REDIRECT = re.compile(r"(?<![0-9<>&])>{1,2}\s*([^\s;|&)]+)")
_TEE = re.compile(r"\btee\s+(?:-a\s+)?([^\s;|&]+)")
_SED_I = re.compile(r"\bsed\s+(?:-[a-zA-Z]*\s+)*-i\b[^|;&]*?\s((?:[^\s;|&-][^\s;|&]*\s*)+)$")

_IGNORED_TARGETS = {"/dev/null", "$null", "nul"}

# The STRUCTURAL SURFACE (#518 / Appendix A6): raw writers, dbt models, and the
# consumption layer — where a change ripples across layers, so the contract must
# carry an end-to-end `impact_map` BEFORE the first edit. Trace before code.
_STRUCTURAL_PREFIXES = ("ingestion/", "dbt_project/models/", "site/", "site_v2/")
_EXPORT_RE = re.compile(r"^scripts/export_[A-Za-z0-9_]+\.py$")
# A `<template placeholder>` is not real content; nor is a bare YAML block
# indicator or an empty/(none) line.
_PLACEHOLDER_RE = re.compile(r"^<.*>$")


# Words and markers that carry no content. ONE set, shared by both content
# checks and matched case-folded.
#
# `>` and `|` are YAML block indicators: omitting them let `decisions_reserved: >`
# satisfy the gate on the KEY LINE, so the body was never read. Five of the seven
# keys in this repo's own contract are written `key: >`, so that is the natural
# spelling, not a contrived one.
#
# The set is SHARED because it was not: `_impact_content` rejected `(none)` while
# accepting `none`, `n/a` and `TBD`, so `impact_map: none` satisfied the very
# requirement this task makes load-bearing on every guard edit in the repo. One
# helper got the fix and its twin did not (cto-reviewer, 2026-07-22).
_NULLISH = {"none", "(none)", "n/a", "na", "tbd", "-", "todo", "?"}

# A YAML block-scalar HEADER carries no content: `>`, `|`, and every chomping and
# indentation variant of them (`>-`, `|-`, `>+`, `|+`, `|2`, `|2-`). Matched by
# PATTERN, not by enumeration. `>` and `|` were added to the word list one round
# earlier and `>-` walked straight through it — and `>-` is not contrived, it is
# what this repo's own workflow files use. Enumerating literals loses this race
# by one variant every round; the pattern closes the class (cto-reviewer,
# 2026-07-22, the FOURTH finding of this same class in this function pair).
_BLOCK_HEADER_RE = re.compile(r"^[>|]\d*[+-]?$")


def _is_empty_marker(s: str) -> bool:
    """True when `s` is a nullish word or a bare YAML block-scalar header."""
    return s.lower() in _NULLISH or bool(_BLOCK_HEADER_RE.match(s))


def _impact_content(text: str) -> bool:
    """True when `text` is real impact-map content — not blank, a comment, a bare
    YAML block indicator, a nullish word, or a `<template placeholder>`.

    The leading `-` is stripped like its twin `_reserved_content` does. Sharing
    the `_NULLISH` set but NOT the normalisation left the list spelling open:
    `impact_map:` followed by `  - none` read as `"- none"`, which is in no
    nullish set, so it satisfied the requirement with zero blast-radius trace.
    The inline and block-scalar spellings were caught and the dash list was not,
    even though `scope_paths`, `decisions_reserved` and `done_when` in this
    repo's own contract are all dash lists. Third round of the same word class in
    the same function pair (cto-reviewer, 2026-07-22).
    """
    s = text.strip().lstrip("-").strip()
    if not s or _is_empty_marker(s):
        return False
    if s.startswith("#"):
        return False
    return not _PLACEHOLDER_RE.match(s)


def _reserved_content(text: str) -> bool:
    """True when a `decisions_reserved` line is a real reservation.

    The artifact gate rests on this: publishing a mock IS the product decision,
    so the open questions must be reserved rather than answered by drawing them.
    A contract exists in almost every session, so contract-existence alone would
    make that gate fire essentially never (cto-reviewer, 2026-07-22).

    "Nothing is open" is still a legitimate answer — it just has to be a
    sentence someone can check ("none: the design is CPO-approved as mock X and
    this publishes it unchanged"), not the template's bare `- none`.
    """
    s = text.strip().lstrip("-").strip()
    if not s or _is_empty_marker(s):
        return False
    if s.startswith("#"):
        return False
    return not _PLACEHOLDER_RE.match(s)


# `<...>` placeholders, INCLUDING ones that span lines. The template's spelling
# opens on one line and closes on the next, and `_PLACEHOLDER_RE` is anchored at
# both ends so it never matched either half.
_PLACEHOLDER_SPAN = re.compile(r"<[^<>]*>", re.S)


def _has_real_reservation(lines: list[str]) -> bool:
    """True when a `decisions_reserved` block holds at least one real entry.

    Placeholders are REMOVED from the joined block rather than latched onto line
    by line. The first attempt set an "inside a placeholder" flag on any line
    opening with `<` and cleared it only on a line ending `>`, so an unclosed
    bracket — `- <2s page load is a product call` — swallowed every real
    reservation written after it and then reported the block as "empty or still
    the template's bare `- none`", which is neither. Fail-closed, but crying wolf
    on a true statement is exactly what the sibling deny message was rewritten to
    stop doing (cto-reviewer, 2026-07-22).
    """
    stripped = _PLACEHOLDER_SPAN.sub(" ", "\n".join(lines))
    return any(_reserved_content(line) for line in stripped.splitlines())


def _is_structural(rel: str) -> bool:
    """The structural surface — an impact_map is required before editing here.

    PROTECTED paths are structural too (2026-07-22). They were left out until a
    retrospective measured the consequence: editing a hook needed CPO authority
    but NO blast-radius trace, while a cosmetic label change on a leaf mart
    needed one. That is backwards. `protected_override` answers "may you"; the
    impact_map answers "do you know what breaks" — two different questions, and
    a guard's blast radius is every future task in the repo, which is wider than
    almost any model's. Both are now required here.
    """
    if any(rel.startswith(p) for p in _STRUCTURAL_PREFIXES):
        return True
    if _is_protected(rel):
        return True
    return bool(_EXPORT_RE.match(rel))


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
    """Parse scope_paths, protected_override, and whether a non-placeholder
    impact_map section is present. None when absent."""
    path = os.path.join(root, CONTRACT_REL)
    if not os.path.isfile(path):
        return None
    scope, in_scope_block, override = [], False, False
    in_impact_block, impact_present = False, False
    in_reserved_block, reserved_lines = False, []
    try:
        for raw in open(path, encoding="utf-8", errors="replace"):
            line = raw.rstrip("\n")
            # EVERY top-level key here closes whatever block was open before it
            # opens its own. Two keys used not to, and each was forgeable in its
            # own way. They were hidden by DIFFERENT accidents of the fixtures,
            # which is worth stating precisely, because a wrong reason invites a
            # wrong hardening:
            #   - `decisions_reserved:` returned early and closed nothing, so
            #     `impact_map: <placeholder>` directly above it left the impact
            #     block open and the first reservation was scored as impact-map
            #     content, FORGING the requirement this task adds. Mirror bug on
            #     the other side: reservations under an open `scope_paths:` block
            #     matched the list-item pattern and joined the allowlist. HIDDEN
            #     BY: every fixture carried `decisions_taken:` between the blocks.
            #   - `scope_paths:` did the same to an impact block opened above it,
            #     so any indented non-item line inside the scope list forged the
            #     map. HIDDEN BY something else entirely: no fixture ever put
            #     `impact_map:` ABOVE `scope_paths:` (the suite builds it by
            #     inserting before `decisions_taken:`, i.e. below the scope list),
            #     and no scope list contained a non-item line. Dropping
            #     `decisions_taken:` from between the blocks would NOT have
            #     exercised it.
            # Of the four clears below, only `in_impact_block = False` on
            # `scope_paths:` changes behaviour today; the other three are already
            # covered by the generic column-0 terminators and are kept as
            # insurance against a future reordering.
            # Two earlier versions of THIS COMMENT each carried a false claim,
            # in the task whose subject is statements that stop being true
            # (cto-reviewer, 2026-07-22, rounds 3, 7 and 8).
            mr = re.match(r"^decisions_reserved\s*:(.*)$", line)
            if mr:
                in_scope_block = False
                in_impact_block = False
                in_reserved_block = True
                reserved_lines.append(mr.group(1))
                continue
            if in_reserved_block:
                if line.strip() and not line.startswith((" ", "\t")):
                    in_reserved_block = False    # next top-level key ends it
                else:
                    reserved_lines.append(line)
                    continue
            if re.match(r"^scope_paths\s*:", line):
                in_impact_block = False      # close, like every other top-level key
                in_reserved_block = False
                in_scope_block = True
                continue
            if in_scope_block:
                m = re.match(r"^\s+-\s+(\S+)", line)
                if m:
                    scope.append(m.group(1).replace("\\", "/"))
                    continue
                if line.strip() and not line.startswith((" ", "\t")):
                    in_scope_block = False
            mi = re.match(r"^impact_map\s*:(.*)$", line)
            if mi:
                in_impact_block = True
                if _impact_content(mi.group(1)):
                    impact_present = True
                continue
            if in_impact_block:
                if line.strip() and not line.startswith((" ", "\t")):
                    in_impact_block = False      # next top-level key ends the block
                elif _impact_content(line):
                    impact_present = True
            if re.match(r"^protected_override\s*:", line):
                override = True
    except Exception:
        return None
    return {"scope": scope, "protected_override": override,
            "impact_map_present": impact_present,
            "decisions_reserved_present": _has_real_reservation(reserved_lines)}


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


def _deny_missing_impact_map(rel: str) -> None:
    # Say WHY this specific path is on the surface. Telling the agent that
    # `.claude/hooks/x.py` is a "raw writer, dbt model, or consumption" file is
    # false, and the rational conclusion from a false reason is that the gate is
    # buggy (cto-reviewer, 2026-07-22).
    if _is_protected(rel):
        why = (
            "is a PROTECTED guard path, which is part of the structural surface: "
            "its blast radius is every future task in this repo, wider than most "
            "models. `protected_override` answers 'may you'; this answers 'do you "
            "know what breaks'. Trace what depends on it — which events fire it, "
            "which other hooks or tests import from it, what stops being enforced "
            "if it is wrong — and what happens on failure"
        )
    else:
        why = (
            "is on the STRUCTURAL SURFACE (raw writer, dbt model, or consumption). "
            "Trace end-to-end FIRST and paste EVIDENCE, not assertion: every writer "
            "of the table/model; the downstream lineage to marts/consumption "
            "(`dbt ls --select <model>+` or the dbt-MCP output); the CI layer rules "
            "that apply; the shared-warehouse deploy ordering; the blast radius "
            "(which marts/numbers change, or 'none' with the RAW count / leaf "
            "evidence)"
        )
    emit_deny(
        f"CONTRACT GATE: `{rel}` {why}. The task contract must carry a "
        "non-placeholder `impact_map:` section BEFORE this edit. "
        "Trivial/leaf/cosmetic changes may use a one-line evidenced short-form. "
        "No map -> no edit here. Add it to the contract on a CLEAN tree, then "
        "proceed. See docs/working_agreement.md §2 and Appendix A6 (#518)."
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
            # The impact_map check below this block is unreachable once we
            # return here, so it has to happen INSIDE the branch. Adding
            # protected paths to `_is_structural` alone would have changed
            # nothing (2026-07-22): authority and understanding are separate
            # gates and a protected edit needs both.
            if not contract.get("impact_map_present"):
                _deny_missing_impact_map(rel)
                return
            emit_context(
                "PreToolUse",
                f"CONTRACT GATE: protected path `{rel}` allowed via the contract's "
                "protected_override (CPO-approved governance task) with an "
                "impact_map present. This edit is part of the PR's audit trail.",
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
    if _is_structural(rel) and not contract.get("impact_map_present"):
        _deny_missing_impact_map(rel)
        return


def _gate_artifact(root: str) -> None:
    """Publishing a design is work, and until 2026-07-22 it was the only kind
    with no gate on it at all.

    Every other guard in this repo keys on a repo file path. A published mock is
    neither: it is written to the scratchpad, OUTSIDE the repo, so
    `_gate_file_edit` returns before it reaches any check. That is why three
    player-page mocks were produced and rejected in one day without a contract,
    a routed reviewer or a commit gate ever seeing them — and why one of them
    invented a hero panel and a player rank that does not exist in the data.

    So this gate cannot ask "is the path in scope". It asks two questions it can
    answer honestly: does a contract exist, and does it carry a real
    `decisions_reserved`. The second matters more than it looks. A contract is
    mandatory before any repo edit, so one exists in almost every session, and
    contract-existence alone would make this gate fire essentially never on the
    surface it was built for (cto-reviewer, 2026-07-22). "What belongs on this
    page" is a §10 product decision: it is reserved and escalated, never answered
    by whoever is drawing the page.
    """
    contract = _read_contract(root)
    why = None
    if contract is None:
        why = (
            "publishing an artifact needs a task contract, the same as any other "
            f"work. Write {CONTRACT_REL} first."
        )
    elif not contract.get("decisions_reserved_present"):
        why = (
            "the contract's `decisions_reserved` is empty or still the template's "
            "bare `- none`. Publishing a design without one asserts that nothing "
            "about this page is an open product question, which was untrue every "
            "time it was assumed."
        )
    if why:
        emit_deny(
            f"CONTRACT GATE: {why}\n\n"
            "This gate exists because design was the ONLY surface with no gate on "
            "it, and it is the surface that failed three times on 2026-07-21. A "
            "mock is not a sketch — it is the product decision, made.\n\n"
            "List every open question about WHAT THE PAGE SHOWS in "
            "`decisions_reserved` and escalate it (§10/§11). Do not answer it by "
            "drawing it. If genuinely nothing is open, say so as a checkable "
            "sentence ('none: the design is CPO-approved as mock X and this "
            "publishes it unchanged'), not as a bare `- none`.\n\n"
            "And if a slot, a spec or a rule demands content the data cannot "
            "honestly supply, the rule is wrong: report it and leave the slot "
            "empty. An empty slot is honest; an invented one is a lie with a "
            "border around it."
        )


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
        # The Edit path demands an impact_map on the structural surface; without
        # this the shell path did not, so `echo x >> .claude/hooks/foo.py` with
        # an override and no map was permitted, and neither the post-command
        # check nor the stop gate flags a protected+override file afterwards.
        # A gate enforced on one write path and advertised as general is not a
        # gate (cto-reviewer, 2026-07-22).
        if _is_structural(rel) and not contract.get("impact_map_present"):
            _deny_missing_impact_map(rel)
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
    try:
        event = read_event()
        root = _repo_root()
        if not isinstance(event, dict):      # `null` / `[]`: valid JSON, not an event
            return 0
        hook = event.get("hook_event_name") or ""
        tool = event.get("tool_name") or ""
        if hook == "PostToolUse" and tool == "Bash":
            _gate_bash_post(event, root)
        elif tool == "Artifact" and hook != "PostToolUse":
            # Guarded on the event name like the Bash branches: a PostToolUse
            # Artifact event would otherwise emit a PreToolUse-shaped deny.
            _gate_artifact(root)
        elif tool in _EDIT_TOOLS:
            _gate_file_edit(event, root)
        elif tool == "Bash":
            _gate_bash_pre(event, root)
    except Exception:
        return 0                             # fail open (house rule)
    return 0


if __name__ == "__main__":
    sys.exit(main())
