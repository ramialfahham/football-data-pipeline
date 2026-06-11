#!/usr/bin/env python
"""Stop gate (governance G2) — the turn-end contract check.

When the agent tries to end its turn, compare `git status` against the task
contract. Out-of-scope modifications block the stop ONCE with a prescriptive
reversion instruction (the `stop_hook_active` flag prevents infinite loops).
This is the guaranteed net behind the best-effort shell gates: nothing dirty
and undeclared survives a turn. Fails OPEN on unexpected errors.
"""

from __future__ import annotations

import json
import os
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
    except Exception:
        return 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
