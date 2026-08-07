#!/usr/bin/env python
"""Stop gate (governance G2) — the turn-end contract AND correctness check.

When the agent tries to end its turn this asks two questions:

  1. GOVERNANCE — does `git status` match the task contract? Out-of-scope
     modifications block the stop with a prescriptive reversion instruction.
  2. CORRECTNESS — do the fast offline gates still pass? Added 2026-08-06.

Question 2 exists because until then NOTHING verified correctness at turn end.
The governance check answers "is this in scope", never "does it work", so on any
turn nobody watched closely, "I made the change" and "the change works" were the
same claim backed by nothing. That gap matters more under auto mode, whose
classifier guards INTENT and explicitly not correctness — broken code is not
dangerous, so broken code goes through.

WHY THESE GATES AND NOT THE TEST SUITE. Measured: the five offline checks run in
2.9s total; `tests/test_governance_hooks.py` alone takes 5m07s. A five-minute
turn-end hook is unusable and would be disabled within a day, which is worse than
no hook.

`FAST_GATES` below is the SOURCE OF TRUTH for that set. `validate-local` runs a
superset and names these five explicitly; `test_fast_gates_and_validate_local_agree`
pins the two against each other, because the first version of this docstring and
the skill each declared the OTHER as the reference while listing different scripts
(platform-reviewer at opus).

Both checks block the stop ONCE — the `stop_hook_active` flag prevents infinite
loops, so an agent that ignores the message ends its turn on the second attempt.
That makes this a loud net, not an impassable one. Fails OPEN on unexpected errors.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from task_contract_gate import (  # noqa: E402
    _dirty_outside_task_dir,
    _is_protected,
    _matches_scope,
    _read_contract,
    _repo_root,
)
from _command_utils import read_event  # noqa: E402

# Offline, no network, no warehouse. Ordered cheapest-first so an early failure
# reports fast.
#
# `check_task_artifacts.py` is deliberately ABSENT: it needs a fetched `origin/main`
# and hard-fails on a missing or stale `review.md`, so at turn end it would block
# every turn during the build phase, before the review cycle has run. It belongs in
# `validate-local` and in CI, not here.
FAST_GATES = (
    "scripts/check_layer_contract.py",
    "scripts/check_registry_var_sync.py",
    "scripts/check_competition_type_seed.py",
    "scripts/check_ui_i18n_metrics.py",
    "scripts/check_copy_gate.py",
)
# Generous against a cold filesystem; the measured total is ~2.9s.
GATE_TIMEOUT_S = 90


def _failing_gates(root: str) -> list[tuple[str, str]]:
    """(script, first meaningful output line) for each fast gate that fails.

    A gate whose SCRIPT IS ABSENT is skipped, not reported: this hook also runs in
    worktrees and on branches where a checker legitimately does not exist yet, and a
    hook that cries wolf about a missing file teaches the agent to ignore it.
    """
    failures: list[tuple[str, str]] = []
    for rel in FAST_GATES:
        path = os.path.join(root, rel)
        if not os.path.isfile(path):
            continue
        try:
            proc = subprocess.run(
                [sys.executable, path], cwd=root, capture_output=True,
                timeout=GATE_TIMEOUT_S,
            )
        except Exception:
            continue  # a broken runner must not block the turn (house rule)
        if proc.returncode != 0:
            out = (proc.stdout or b"").decode("utf-8", "replace")
            err = (proc.stderr or b"").decode("utf-8", "replace")
            lines = [ln.strip() for ln in (out + "\n" + err).splitlines() if ln.strip()]
            detail = next((ln for ln in lines if ln.startswith("-") or "FAIL" in ln),
                          lines[0] if lines else f"exit {proc.returncode}")
            failures.append((rel, detail[:300]))
    return failures


def main() -> int:
    event = read_event()
    if event.get("stop_hook_active"):
        return 0
    try:
        root = _repo_root()
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
            print(json.dumps({
                "decision": "block",
                "reason": (
                    "STOP GATE: the tree does not match the task contract. "
                    "Out-of-scope modified files: " + ", ".join(violations[:10]) +
                    ". Before ending the turn: revert each with "
                    "`git checkout -- <file>` (delete untracked strays), or — if "
                    "the change is genuinely needed — amend the contract on a "
                    "clean tree recording the CPO authority, then commit. "
                    "See docs/working_agreement.md §2."
                ),
            }))
            return 0

        # CORRECTNESS. Only reached when the tree is in scope, and only when the turn
        # actually touched something — a conversational turn should not pay 2.9s, and a
        # clean tree cannot have broken a gate that was passing.
        if not _dirty_outside_task_dir(root):
            return 0
        failures = _failing_gates(root)
        if failures:
            detail = "; ".join(f"{rel} -> {msg}" for rel, msg in failures)
            print(json.dumps({
                "decision": "block",
                "reason": (
                    "STOP GATE (correctness): the tree is in scope, but "
                    f"{len(failures)} offline gate(s) FAIL. {detail}. These are the same "
                    "checks CI runs, so ending the turn here ships a known-red branch. "
                    "Fix them, or — if a failure is pre-existing and unrelated — say so "
                    "explicitly with the command output rather than ending silently. "
                    "Run `python <script>` for the full report."
                ),
            }))
    except Exception:
        return 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
