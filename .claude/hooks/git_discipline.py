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
import shlex
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
_COMMIT_FORBIDDEN = re.compile(r"(?:^|\s)(--no-verify|--amend|-n)(?=\s|$)")
# Commit-flag ALLOWLIST (CTO finding, G3 review round 2): a denylist of the
# self-staging forms (-a/-am/--include/...) is bypassable via POSIX
# short-option bundling (`-qam`) and long-option prefix abbreviation
# (`--inc`). Inverted: any flag outside this set — and any positional
# pathspec — is denied, so only `git add` + plain `git commit` can reach the
# review hash gate with reviewer-seen content.
_ALLOWED_COMMIT_FLAGS = {
    "-m", "--message", "-F", "--file",       # message (take a value)
    "-q", "--quiet", "-v", "--verbose",
    "-S", "--gpg-sign", "-s", "--signoff",
}
_COMMIT_VALUE_FLAGS = {"-m", "--message", "-F", "--file"}
_HOOKSPATH = re.compile(r"git\s+config\b.*core\.hookspath", re.IGNORECASE)

ROUTING_REL = ".claude/review_routing.json"
REVIEW_REL = ".claude/task/review.md"


def _commit_form_violation(raw: str) -> str | None:
    """Why this `git commit` command is form-denied, or None.

    Tokenizes the RAW command with shlex — the quote-stripped text erases a
    QUOTED pathspec (`git commit -m "x" "path.sql"`), which git commits as
    reviewer-unseen working-tree content (CTO finding, G3 review round 5).
    Walks the tokens after `commit`: `--` or any positional token is a
    pathspec (selects/stages content at commit time); any flag outside
    _ALLOWED_COMMIT_FLAGS is denied by default — covering -a/-am/--all,
    -i/--include, -o/--only, -p/--interactive, their bundled spellings
    (-qam) and prefix abbreviations (--inc) alike.
    """
    try:
        tokens = shlex.split(raw)
    except ValueError:
        return "unbalanced quoting"      # unparseable: fail toward deny
    try:
        i = tokens.index("commit") + 1
    except ValueError:
        return None
    while i < len(tokens):
        tok = tokens[i]
        if tok == "--":
            spec = tokens[i + 1] if i + 1 < len(tokens) else "--"
            return f"pathspec `{spec}`"
        base = tok.split("=", 1)[0]
        if base not in _ALLOWED_COMMIT_FLAGS:
            return f"flag `{tok}`" if tok.startswith("-") else f"pathspec `{tok}`"
        if base in _COMMIT_VALUE_FLAGS and "=" not in tok:
            i += 2                       # the next token is the flag's value
        else:
            i += 1
    return None


def _repo_root() -> str:
    return os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()


def _staged_diff_bytes(root: str) -> bytes:
    import subprocess
    return subprocess.run(
        ["git", "diff", "--staged"], cwd=root, capture_output=True, timeout=30,
    ).stdout


def _staged_paths(root: str) -> list[str]:
    import subprocess
    # -z (NUL-split): with core.quotePath, non-ASCII paths come out quoted
    # and escaped, match no routing pattern, and would silently drop a
    # required reviewer (CTO finding, G3 review round 5).
    out = subprocess.run(
        ["git", "diff", "--staged", "--name-only", "-z"], cwd=root,
        capture_output=True, text=True, timeout=30,
    ).stdout
    return [p.replace("\\", "/") for p in out.split("\0") if p]


def _load_routing(root: str) -> dict | None:
    import json
    try:
        with open(os.path.join(root, ROUTING_REL), encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def _required_reviewers(paths: list[str], routing: dict) -> set[str]:
    import fnmatch
    required = set(routing.get("always") or [])
    for path in paths:
        for pattern, reviewers in (routing.get("paths") or {}).items():
            if fnmatch.fnmatch(path, pattern):
                required.update(reviewers)
    return required


def _artifact_only(paths: list[str], routing: dict) -> bool:
    import fnmatch
    pats = routing.get("artifact_only") or []
    return bool(paths) and all(
        any(fnmatch.fnmatch(p, pat) for pat in pats) for p in paths
    )


def _review_sections(text: str) -> dict[str, str]:
    """Map '## section' name -> section body. Text before the first header is
    kept as the `_preamble` pseudo-section so an ESCALATE written there cannot
    escape the per-section pairing (CTO finding, G3 review round 4)."""
    sections, name, buf = {}, "_preamble", []
    for line in text.splitlines():
        m = re.match(r"^##\s+(\S+)", line)
        if m:
            sections[name] = "\n".join(buf)
            name, buf = m.group(1), []
        else:
            buf.append(line)
    sections[name] = "\n".join(buf)
    return sections


def _commit_gate(root: str) -> str | None:
    """Reason to deny the commit, or None when the gate passes (governance G3)."""
    import hashlib
    paths = _staged_paths(root)
    if not paths:
        return None                      # nothing staged: let git complain
    routing = _load_routing(root)
    if routing is None:
        return None                      # no routing file: gate not active (fail open)
    if _artifact_only(paths, routing):
        return None                      # bookkeeping commit: exempt
    review_path = os.path.join(root, REVIEW_REL)
    if not os.path.isfile(review_path):
        return (
            "REVIEW GATE: no review artifact. Run the review cycle first "
            "(stage -> blinded reviewers -> write .claude/task/review.md per "
            ".claude/task/REVIEW_TEMPLATE.md), then commit."
        )
    text = open(review_path, encoding="utf-8", errors="replace").read()
    m = re.search(r"diff_sha256:\s*([0-9a-fA-F]{64})", text)
    live = hashlib.sha256(_staged_diff_bytes(root)).hexdigest()
    if not m or m.group(1).lower() != live:
        return (
            "REVIEW GATE: staged diff has changed since the reviewers ran "
            "(hash mismatch). Re-run the reviewers against the current staged "
            f"diff and update review.md (live hash: {live})."
        )
    if "VERDICT: FAIL" in text:
        return "REVIEW GATE: a reviewer verdict is FAIL. Fix the findings and re-run the cycle."
    if text.count("VERDICT: ESCALATE") > text.count("CPO ANSWER:"):
        return (
            "REVIEW GATE: an ESCALATE verdict has no recorded CPO ANSWER. "
            "Escalate blinded (working_agreement.md §11), record the answer "
            "in review.md, then commit."
        )
    sections = _review_sections(text)
    for name, body in sections.items():
        # per-section pairing: one CPO answer elsewhere must not mask another
        # unanswered escalation (scope-auditor boundary note, G3 first review)
        if "VERDICT: ESCALATE" in body and "CPO ANSWER:" not in body:
            return (
                f"REVIEW GATE: section `{name}` carries an ESCALATE without a "
                "CPO ANSWER in that section. Record the answer next to the "
                "question, then commit."
            )
    for reviewer in sorted(_required_reviewers(paths, routing)):
        body = sections.get(reviewer)
        if body is None or ("VERDICT:" not in body):
            return (
                f"REVIEW GATE: required reviewer `{reviewer}` has no verdict for "
                "the staged paths (see .claude/review_routing.json). Run it and "
                "record its section in review.md."
            )
        if "VERDICT: PASS" in body:
            # count only bullets after the risks_checked: marker — a stray
            # bullet list above it must not satisfy the quota (CTO, round 3)
            _, _, risks_block = body.partition("risks_checked:")
            risks = re.findall(r"^\s*-\s+\S", risks_block, flags=re.MULTILINE)
            if len(risks) < 2:
                return (
                    f"REVIEW GATE: `{reviewer}` PASS without two named risks — "
                    "malformed verdict (no free passes). Re-run the reviewer."
                )
    return None


def main() -> int:
    if "--staged-hash" in sys.argv:
        import hashlib
        print(hashlib.sha256(_staged_diff_bytes(_repo_root())).hexdigest())
        return 0
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
        # Commit detection is token-exact and deliberately LOOSE (CTO finding,
        # G3 review round 3): enumerating git's global options (-p, -C, -c,
        # --git-dir <x>, ...) under-matches, and an unmatched spelling skips
        # the whole gate. Any `git ... commit ...` invocation enters here;
        # the form check below then requires the spelling to be exactly
        # `git commit ...` — over-triggering is fail-closed, under-triggering
        # is a gate bypass.
        tokens = part.split()
        if len(tokens) >= 2 and tokens[0] == "git" and "commit" in tokens[1:]:
            if len(stripped_parts) > 1:
                # The staged-diff hash is verified at PreToolUse time; a
                # sibling command in the same call (`git add x && git commit`)
                # would mutate the index AFTER the check and commit
                # reviewer-unseen content (CTO finding, G3 review round 4).
                emit_deny(
                    "COMMIT FORM BLOCKED: `git commit` must be the SOLE "
                    "command in the Bash call — a chained sibling command "
                    "(e.g. `git add x && git commit`) can restage content "
                    "after the review hash was verified. Run staging, review "
                    "and commit as separate calls. See "
                    "docs/working_agreement.md §2."
                )
                return 0
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
            if tokens[1] != "commit":
                emit_deny(
                    f"COMMIT FORM BLOCKED: `{tokens[1]}` between `git` and "
                    "`commit` — git global options can repoint or repage the "
                    "invocation past the review gate, so the only allowed "
                    "spelling is exactly `git commit ...`. (If this was not a "
                    "commit command, quote the word 'commit' or use the "
                    "`--flag=value` form.) See docs/working_agreement.md §2."
                )
                return 0
            # sole-command rule above guarantees this part IS the whole call,
            # so the un-stripped `cmd` is safe to tokenize for the flag walk
            violation = _commit_form_violation(cmd)
            if violation:
                emit_deny(
                    f"COMMIT FORM BLOCKED: {violation} is outside the allowed "
                    "commit form — pathspecs and flags beyond the message/"
                    "quiet/verbose/sign set select or stage content AT COMMIT "
                    "TIME, after the review hash was computed, so the commit "
                    "would carry reviewer-unseen changes. Stage with `git add "
                    "<files>`, run the review cycle, then plain `git commit -m "
                    "...` (quoted message). See docs/working_agreement.md §2."
                )
                return 0
            try:
                reason = _commit_gate(_repo_root())
            except Exception:
                reason = None            # fail open (house rule)
            if reason:
                emit_deny(reason)
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
