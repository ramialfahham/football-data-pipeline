#!/usr/bin/env python
"""PreToolUse(Bash) guardrail — git discipline (project-specific wording).

Checks, self-gated against the *actual* command (see _command_utils):
  1. Block agent-initiated `gh pr merge` — merging is the user's call.
  2. Block `git commit --amend` / `--no-verify` / `-n` — history integrity and
     the governance hash-chain depend on append-only, hook-verified commits
     (governance G2; flags matched on quote-stripped text so commit-message
     bodies cannot false-positive).
  3. Block `git config core.hooksPath` — repointing git hooks disables the
     repo's automation.
  4. Nudge the branch-consolidation questions on branch creation.

Fails open: any error or non-matching command exits 0 with no output.
"""

from __future__ import annotations

import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _command_utils import (  # noqa: E402
    bash_command,
    emit_context,
    emit_deny,
    read_event,
    simple_commands,
    strip_quoted_and_heredoc,
)

_GH_PR_MERGE = re.compile(r"gh\s+pr\s+merge\b")
_BRANCH_CREATE = re.compile(r"git\s+(?:checkout\s+-b|switch\s+(?:-c|--create))\b")
_GIT_COMMIT = re.compile(r"git\s+commit\b")
_COMMIT_FORBIDDEN = re.compile(r"(?:^|\s)(--no-verify|--amend|-n)(?=\s|$)")
_HOOKSPATH = re.compile(r"git\s+config\b.*core\.hookspath", re.IGNORECASE)


def main() -> int:
    cmd = bash_command(read_event())
    if not cmd:
        return 0
    stripped = strip_quoted_and_heredoc(cmd)
    parts = list(simple_commands(cmd))
    stripped_parts = list(simple_commands(stripped))

    for part in parts:
        if _GH_PR_MERGE.match(part):
            emit_deny(
                "MERGE BLOCKED: `gh pr merge` is the user's action, not the agent's. "
                "Open the PR, get CI green, and stop — the user merges. "
                "(Only proceed if the user explicitly typed 'merge it' in this thread.) "
                "See docs/working_agreement.md §3."
            )
            return 0

    for part in stripped_parts:
        if _GIT_COMMIT.match(part):
            flag = _COMMIT_FORBIDDEN.search(part)
            if flag:
                emit_deny(
                    f"COMMIT FLAG BLOCKED: `{flag.group(1)}` is not allowed. "
                    "`--amend` rewrites a reviewed commit (history must stay "
                    "append-only for the governance hash-chain); `--no-verify`/`-n` "
                    "skips the repo's git hooks. Make a NEW, hook-verified commit "
                    "instead. See docs/working_agreement.md §2/§3."
                )
                return 0
        if _HOOKSPATH.search(part):
            emit_deny(
                "HOOKS-PATH BLOCKED: repointing `core.hooksPath` disables the "
                "repo's git automation. Not permitted."
            )
            return 0

    for part in parts:
        if _BRANCH_CREATE.match(part):
            emit_context(
                "PreToolUse",
                "BRANCH DISCIPLINE: before branching, run `gh pr list --state open` and ask "
                "(1) is this a hard dependency of an open PR? (2) does a separate branch buy "
                "independent reviewability or an earlier merge path? If hard-dependency AND no "
                "benefit → commit to that branch instead; otherwise a new branch is fine. "
                "Branch from `main` (never with origin/main as the tracking target, which sends "
                "pushes to main). See docs/working_agreement.md §3a.",
            )
            return 0

    return 0


if __name__ == "__main__":
    sys.exit(main())
