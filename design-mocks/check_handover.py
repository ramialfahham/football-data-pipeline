"""Check a handover before it is written to GitLab issue #157. Run from anywhere.

    python design-mocks/check_handover.py <draft> && glab issue update 157 --description "$(cat <draft>)"

Exit 1 when the draft is over the 16,000 characters the session-start hook injects, or carries a
public network address: the issue is public, and no hook sees a write to it, so the address check
that guarded the handover while it was a file in the repo runs here, with the gate's own
patterns. With no argument it reads the copy the hook saved at session start.
"""
import re as _re
import sys
from collections import Counter
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / ".claude" / "hooks"))
import host_fingerprint_gate as gate  # noqa: E402

MAX_CHARS = 16000


def main(argv):
    p = Path(argv[1]) if len(argv) > 1 else REPO / ".claude" / "handover.cache.md"
    s = p.read_text(encoding="utf-8")
    print("chars:", len(s), "/ %d | headroom" % MAX_CHARS, MAX_CHARS - len(s))

    # NEXT must be a single unbroken run; a duplicated or colliding number means an edit went wrong
    nums = [int(m) for m in _re.findall(r"^(\d+)\. ", s, flags=_re.M)]
    print("NEXT numbering:", nums, "->", "OK" if nums == list(range(0, len(nums))) else "BROKEN")
    print("duplicate lines:", sum(1 for _line, c in
          Counter([ln for ln in s.splitlines() if ln.strip()]).items() if c > 1))

    hits = list(gate.flagged_lines(s))
    for n, kind in hits:
        print("REFUSED: a public %s address on line %d; describe the host instead" % (kind, n))
    if len(s) > MAX_CHARS:
        print("REFUSED: %d characters over the budget the hook injects" % (len(s) - MAX_CHARS))
    return 1 if hits or len(s) > MAX_CHARS else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
