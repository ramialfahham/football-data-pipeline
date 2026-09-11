"""Process health — reports numbers. Decides nothing.

Builder-initiated, not a product decision. It ships because it only READS
artifacts the repo already keeps and prints them. It carries no authority and
sets no policy.

**Whether any number here should have a threshold, and what happens when a
threshold is crossed, is a §10 decision reserved to the product owner.** A
threshold or a sunset rule for withdrawing process would be builder-authored
governance. The constant below is a REFERENCE POINT computed from the log, not a
target and not a trigger.

The one claim the org design rests on is that front-loading a decision removes
review rounds and interruptions of the product owner. This prints the before and
after so that claim can be tested rather than asserted. Acting on the result is
his.

Read-only. Never fails a build.
"""
from __future__ import annotations

import collections
import fnmatch
import json
import pathlib
import re
import subprocess
import sys

REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
ESCALATIONS = REPO_ROOT / ".claude" / "task" / "escalations.log"
REVIEW_REL = ".claude/task/review.md"
ROUTING = REPO_ROOT / ".claude" / "review_routing.json"

# Computed from the log at run time, never hardcoded. An earlier draft carried a
# literal AND a different figure in its docstring AND a third in the handover —
# one quantity, three values, which is how a hand-typed number drifts. The
# pre-split reference point is now derived from the same parser as the post-split
# figure, so the two can never disagree about how they were counted.


def _git(*args: str) -> str:
    """UTF-8 with replacement, never the platform codepage: this repo's history is
    full of multi-byte characters and cp1252 raises on them mid-read. A failed git
    call returns "" rather than None, so callers never regex against None."""
    proc = subprocess.run(["git", *args], cwd=REPO_ROOT, capture_output=True,
                          encoding="utf-8", errors="replace")
    return proc.stdout or ""


# The split shipped on this date. Branches recorded before it are the BASELINE;
# branches after it are what the design is judged on. Averaging over all history
# would mix the two and could never show a change — the first version of this
# script did exactly that and printed IMPROVING because the split's own entry
# added a branch.
SPLIT_DATE = "2026-07-31"


def rulings() -> dict:
    """Rulings recorded in the log, split into before and after the org change."""
    if not ESCALATIONS.is_file():
        return {"before": (0, 0), "after": (0, 0)}
    text = ESCALATIONS.read_text(encoding="utf-8", errors="replace")
    # One entry per `YYYY-MM-DD[/DD] <branch>` header; its rulings are the
    # 'CPO ANSWER' / 'CPO RULING' markers until the next header.
    heads = list(re.finditer(r"^(20\d\d-\d\d-\d\d)(?:/\d\d)? (\S+)", text, flags=re.M))
    tally = {"before": [0, set()], "after": [0, set()]}
    for i, h in enumerate(heads):
        end = heads[i + 1].start() if i + 1 < len(heads) else len(text)
        body = text[h.start():end]
        bucket = "after" if h.group(1) >= SPLIT_DATE else "before"
        tally[bucket][0] += len(re.findall(r"CPO (?:ANSWER|RULING)", body))
        tally[bucket][1].add(h.group(2))
    return {k: (v[0], len(v[1])) for k, v in tally.items()}


def rounds_history() -> list[int]:
    """Every `rounds:` value review.md has ever carried, from its own git log.
    A branch that needed three rounds cost three times the reviewer spend of one."""
    log = _git("log", "--format=%H", "--", REVIEW_REL).split()
    seen = []
    for sha in log:
        blob = _git("show", f"{sha}:{REVIEW_REL}")
        m = re.search(r"^[^\S\n]*rounds:[^\S\n]*(\d+)", blob, flags=re.M)
        if m:
            seen.append(int(m.group(1)))
    return seen


def activation(n: int = 150) -> tuple[int, collections.Counter]:
    """How often each reviewer is REQUIRED. A role at 0% is dead by construction;
    a role near 100% is not a specialist. Both are design defects — and the whole
    reason the org exercise happened was a role that had never fired once.

    SEEDED FROM THE AGENT FILES, not from the routing table. A `Counter` only ever
    holds keys it was incremented for, so an earlier version could never surface a
    zero and the dead-role branch below was unreachable — while a dead role existed
    in the repo. Seeding from `.claude/agents/*.md` also catches the hole the
    contract's own blast_radius names: a reviewer with NO routing row at all, and a
    routing row naming a reviewer with no brief (nothing else in the repo checks
    that a reviewer name is real)."""
    routing = json.loads(ROUTING.read_text(encoding="utf-8"))
    always, paths = routing.get("always") or [], routing.get("paths") or {}
    briefs = {p.stem for p in (REPO_ROOT / ".claude" / "agents").glob("*.md")
              if p.stem != "README"}
    routed = set(always) | {r for revs in paths.values() for r in revs}
    hits = collections.Counter({name: 0 for name in briefs | routed})
    total = 0
    for sha in _git("log", "--format=%H", "-n", str(n)).split():
        files = _git("diff-tree", "--no-commit-id", "--name-only", "-r", sha).split()
        if not files:
            continue
        total += 1
        req = set(always)
        for f in files:
            for pattern, reviewers in paths.items():
                if fnmatch.fnmatch(f, pattern):
                    req.update(reviewers)
        for r in req:
            hits[r] += 1
    return total, hits


def main() -> int:
    print("PROCESS HEALTH\n" + "=" * 58)

    r = rulings()
    bn, bb = r["before"]
    an, ab = r["after"]
    base = (bn / bb) if bb else 0.0
    print(f"\nCPO rulings, BEFORE the org change ({SPLIT_DATE})")
    print(f"  {bn} across {bb} branches   = {base:.2f}/branch   <- reference point")
    print("\nCPO rulings, SINCE the org change")
    if ab == 0:
        print("  none recorded yet.")
    else:
        print(f"  {an} across {ab} branches   = {an / ab:.2f}/branch")
        if ab < 3:
            print("  note: the first post-split entry is the org change ITSELF, whose")
            print("    rulings are the design, not process overhead.")
    print("\n  NO TARGET IS SET HERE. Whether these numbers should carry a threshold,")
    print("  and what follows from crossing one, is the CPO's call (§10). This")
    print("  script reports; it does not judge and it does not withdraw a guard.")

    hist = rounds_history()
    if hist:
        print(f"\nReview rounds observed      n={len(hist)}  max={max(hist)}  "
              f"mean={sum(hist) / len(hist):.2f}")
        dist = collections.Counter(hist)
        for k in sorted(dist):
            print(f"  round {k}                   {dist[k]}")
    else:
        print("\nReview rounds observed      none recorded yet")

    total, hits = activation()
    routing = json.loads(ROUTING.read_text(encoding="utf-8"))
    routed = set(routing.get("always") or []) | {
        r for revs in (routing.get("paths") or {}).values() for r in revs}
    briefs = {p.stem for p in (REPO_ROOT / ".claude" / "agents").glob("*.md")
              if p.stem != "README"}
    if not total:
        # Seeding the counter makes the loop below always run, which un-hides a
        # ZeroDivisionError that is otherwise unreachable. Realistic shape: a
        # `fetch-depth: 1` checkout of a merge commit,
        # where `diff-tree` without `-m` prints nothing for every commit it sees.
        print("\nReviewer activation: no file-bearing commits in range, nothing to "
              "report. (A shallow clone or a merge-only range does this.)")
        return 0
    print(f"\nReviewer activation over the last {total} commits")
    for name, c in hits.most_common():
        flag = ""
        if c == 0:
            flag = ("  <- DEAD: fires on nothing"
                    + ("" if name in routed else " (NO ROUTING ROW)"))
        elif c == total and name != "scope-auditor":
            flag = "  <- fires on everything: not a specialist"
        if name not in briefs:
            flag += "  <- ROUTED BUT NO BRIEF FILE"
        print(f"  {c * 100 // total:>3}%  {c:>3}/{total}  {name}{flag}")

    print("\nNOT MEASURABLE YET, stated rather than silently omitted:")
    print("  - gate denials per branch: hooks deny in-session and record nothing.")
    print("  - reviewer FAILs per branch: review.md is overwritten each round, so")
    print("    only the final verdict survives in git, never the FAILs that led to it.")
    print("  Both need a hook to append a line when it fires. Not built; not claimed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
