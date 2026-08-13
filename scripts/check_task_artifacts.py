#!/usr/bin/env python
"""CI backstop for the governance artifacts (G3).

Local hooks can be bypassed by a misbehaving or misconfigured agent; this
check keeps the gate honest at the PR boundary. For the diff between the PR
branch and the base, it verifies:

  - artifact-only PRs (only bookkeeping paths) pass — but a PR touching
    .claude/task/contract.md is NEVER artifact-only (it authorizes scope; F10/#409);
  - otherwise .claude/task/contract.md and .claude/task/review.md must exist;
  - review.md carries a well-formed 64-hex diff_sha256 that MATCHES the recomputed
    hash of `git diff base...HEAD` excluding the bookkeeping artifacts — binding the
    review to this PR's code + contract (F11/#409);
  - every reviewer required by .claude/review_routing.json for the PR's
    changed paths has a verdict section;
  - no "VERDICT: FAIL"; every "VERDICT: ESCALATE" has a "CPO ANSWER:" in its
    OWN section (per-section pairing, mirroring the local commit gate — an
    answer elsewhere must not mask an unanswered escalation);
  - every "VERDICT: PASS" section says what it examined (>= 1 entry under
    `risks_checked:`). It need not name a defect — CPO 2026-08-01.

Fails CLOSED (non-zero exit) — this is CI, not a guardrail hook.

Usage: python scripts/check_task_artifacts.py [--base <ref>]

The base defaults to the LIVE remote rather than a hardcoded `origin` — see
`default_base()` for why that distinction is not cosmetic.
"""

from __future__ import annotations

import argparse
import fnmatch
import hashlib
import json
import os
import re
import subprocess
import sys

ROUTING = ".claude/review_routing.json"
CONTRACT = ".claude/task/contract.md"
REVIEW = ".claude/task/review.md"

# The CI backstop and the local hooks MUST agree, so CI IMPORTS the hooks' own
# logic rather than re-implementing it. The round-cap placeholder set, the
# `(none)` nullish spelling and the export regex diverged once when hand-copied —
# the exact "the twin didn't get the fix" class this repo has been bitten by. Now
# there is one source: `git_discipline._rounds_gate` decides the round cap.
# `test_governance_hooks` asserts CI reuses it.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".claude", "hooks"))
import git_discipline as _gd            # noqa: E402


def _rounds_error(text: str) -> str | None:
    """Round-cap rule — the SAME decision as the local commit gate, because it is
    literally that function. Non-None means deny."""
    return _gd._rounds_gate(text)


def changed_paths(base: str) -> list[str]:
    # -z (NUL-split) mirrors the local gate: quotePath-escaped non-ASCII
    # paths would match no routing pattern and drop a required reviewer
    out = subprocess.run(
        ["git", "diff", "--name-only", "-z", f"{base}...HEAD"],
        capture_output=True, text=True, check=True,
    ).stdout
    return [p.replace("\\", "/") for p in out.split("\0") if p]


def review_sections(text: str) -> dict[str, str]:
    """Text before the first `##` header is kept as the `_preamble`
    pseudo-section, mirroring the local gate — an ESCALATE written there must
    not escape the per-section pairing."""
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


def default_base() -> str:
    """The ref to diff against when no `--base` is given.

    `origin` names two different repositories. Inside GitLab CI the clone sets it
    to the GitLab project, which is why `.gitlab-ci.yml` passes `--base origin/...`
    explicitly and is CORRECT to do so. On a working copy here, `origin` is the
    GitHub remote — dormant while account access is unavailable — and it sat 27
    commits behind `gitlab/main` on 2026-08-07. So the bare command diffed against a
    stale tree and reported required reviewers that were not required at all
    (GitLab #24).

    This is a PREFERENCE, not a retirement. GitHub is kept, and how it is used is
    decided when access returns. `GOVERNANCE_BASE` still overrides everything, and
    if `origin` becomes the live remote again this returns to `origin/main` with no
    code change — either by unsetting the `gitlab` remote or by setting the env var.

    Resolved AFTER parsing, so the subprocess call never runs on the CI path where
    `--base` is passed explicitly.
    """
    env = os.environ.get("GOVERNANCE_BASE")
    if env:
        return env
    try:
        remotes = subprocess.run(
            ["git", "remote"], capture_output=True, text=True, timeout=10,
        ).stdout.split()
    except Exception:
        return "origin/main"
    return "gitlab/main" if "gitlab" in remotes else "origin/main"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default=None)
    args = ap.parse_args()
    if args.base is None:
        args.base = default_base()

    paths = changed_paths(args.base)
    if not paths:
        print("check_task_artifacts: empty diff — OK")
        return 0

    with open(ROUTING, encoding="utf-8") as f:
        routing = json.load(f)

    artifact_pats = routing.get("artifact_only") or []
    # F10 (#409): a PR touching contract.md is never artifact-exempt (it authorizes scope).
    never = routing.get("artifact_only_never") or []
    is_never = any(fnmatch.fnmatch(p, pat) for p in paths for pat in never)
    if not is_never and all(
        any(fnmatch.fnmatch(p, pat) for pat in artifact_pats) for p in paths
    ):
        print("check_task_artifacts: artifact-only PR — OK")
        return 0

    errors: list[str] = []
    if not os.path.isfile(CONTRACT):
        errors.append(f"missing {CONTRACT} (every code PR carries its task contract)")
    if not os.path.isfile(REVIEW):
        errors.append(f"missing {REVIEW} (every code PR carries its review verdicts)")
    if errors:
        print("check_task_artifacts: FAIL\n  - " + "\n  - ".join(errors))
        return 1

    text = open(REVIEW, encoding="utf-8", errors="replace").read()
    m = re.search(r"diff_sha256:\s*([0-9a-fA-F]{64})", text)
    if not m:
        errors.append("review.md has no well-formed diff_sha256")
    else:
        # F11 (#409): bind review.md to THIS PR's code. Recompute the hash over the
        # branch diff EXCLUDING the bookkeeping artifacts — the same bytes the local gate
        # hashes. --no-renames + --no-abbrev keep rename detection off and blob SHAs full.
        # A code-then-stale-review ordering (the #405 false-green) fails here.
        #
        # ⚠ `--raw`, NOT the rendered patch (#63). This is the CI HALF of a pair that must
        # agree byte for byte with `git_discipline.py::_staged_diff_bytes`; change one and
        # every commit is falsely rejected. The rendered patch is a PRESENTATION format
        # whose bytes vary with git version, platform and diff settings, so this check and
        # its local twin produced different hashes for provably identical commits and
        # `validate:governance` could not pass at all. `--raw` emits mode, blob SHAs,
        # status and path; blob SHAs are content hashes, identical on every platform and
        # git version. Nothing is weakened: the rendered patch is derived FROM those blobs.
        excludes = routing.get("hash_exclude_paths") or []
        pathspec = (["--", "."] + [f":(exclude){p}" for p in excludes]) if excludes else []
        diff = subprocess.run(
            ["git", "diff", "--raw", "--no-renames", "--no-abbrev", f"{args.base}...HEAD"]
            + pathspec,
            capture_output=True, check=True,
        ).stdout
        recomputed = hashlib.sha256(diff).hexdigest()
        if m.group(1).lower() != recomputed:
            errors.append(
                "review.md diff_sha256 does not match this PR's code+contract diff "
                f"(recomputed {recomputed}) — the review is not bound to this PR (F11)")
    rounds_err = _rounds_error(text)
    if rounds_err:
        errors.append(rounds_err)
    if "VERDICT: FAIL" in text:
        errors.append("review.md contains VERDICT: FAIL — unresolved findings")
    # SECONDARY (coarse) backstop only — F12/#421. The per-section loop below is the
    # AUTHORITATIVE check for unanswered escalations (it can't be fooled by an answer in a
    # different section). This global count is a cheap sanity net; keep it adjacent to the
    # per-section loop and never rely on it alone.
    if text.count("VERDICT: ESCALATE") > text.count("CPO ANSWER:"):
        errors.append("an ESCALATE verdict lacks a recorded CPO ANSWER (global backstop)")
    sections = review_sections(text)
    for name, body in sections.items():
        # per-section pairing (AUTHORITATIVE), same rule as the local commit gate: one
        # section's answer must not mask another's unanswered escalation
        if "VERDICT: ESCALATE" in body and "CPO ANSWER:" not in body:
            errors.append(
                f"section `{name}` has an ESCALATE without a CPO ANSWER in that section")

    required = set(routing.get("always") or [])
    for path in paths:
        for pattern, reviewers in (routing.get("paths") or {}).items():
            if fnmatch.fnmatch(path, pattern):
                required.update(reviewers)
    for reviewer in sorted(required):
        body = sections.get(reviewer)
        if body is None or "VERDICT:" not in body:
            errors.append(f"required reviewer `{reviewer}` has no verdict section")
        elif "VERDICT: PASS" in body:
            # A PASS must say what was EXAMINED; it need not name a defect.
            # This floor MUST equal `git_discipline._commit_gate`'s — it was 2 here and
            # 1 there for the length of one review round, which meant a reviewer taking
            # the CPO's 2026-08-01 permission ("it's allowed to approve and not invent
            # some finding") committed locally and then reddened CI, fail-closed, with a
            # message quoting a rule that no longer existed.
            # Entries count only after the risks_checked: marker, mirroring the local
            # gate — stray bullets above it must not satisfy the floor.
            _, _, risks_block = body.partition("risks_checked:")
            if len(re.findall(r"^\s*-\s+\S", risks_block, flags=re.MULTILINE)) < 1:
                errors.append(
                    f"`{reviewer}` PASS with nothing under `risks_checked:` — a pass "
                    "must state what was examined, even when it found nothing"
                )

    if errors:
        print("check_task_artifacts: FAIL\n  - " + "\n  - ".join(errors))
        return 1
    print(f"check_task_artifacts: OK ({len(paths)} changed paths, "
          f"{len(required)} required reviewers)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
