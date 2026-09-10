"""Size + content check on the handover. Run from anywhere."""
import re as _re
from collections import Counter
from pathlib import Path

p = Path(__file__).resolve().parent.parent / ".claude/active_work.md"
s = p.read_text(encoding="utf-8")
print("chars:", len(s), "/ 16000 | headroom", 16000 - len(s))
print("tail intact:", s.rstrip().endswith("so a spec can overstate its page and pass."))

# NEXT must be a single unbroken run; a duplicated or colliding number means an edit went wrong
nums = [int(m) for m in _re.findall(r"^(\d+)\. ", s, flags=_re.M)]
print("NEXT numbering:", nums, "->", "OK" if nums == list(range(0, len(nums))) else "BROKEN")
print("duplicate lines:", sum(1 for _line, c in
      Counter([ln for ln in s.splitlines() if ln.strip()]).items() if c > 1))

MUST = [
    "PER BOARD, never per row",
    "is the ONLY new key",
    "NO GOALKEEPER BOARD EXISTS",
    "container query on `.board`",
    "Goals \u00b7\n  Assists \u00b7 Passes \u00b7 Key passes",
    "MULTI-COMMIT",
]
STALE = [
    "FIVE boards",
    "Goal contributions",
    "two value columns is PLAYERS ONLY",
    "63 rows",
    "Shots on target faced",
]
# ⚠ Collapse whitespace before matching. A line-based check misses a phrase that straddles
# a line break, which is exactly what the handover itself warns about -- it reported
# "container query on `.board`" as LOST when the text was present, just wrapped.
flat = " ".join(s.split())
for k in MUST:
    print(("  keep  " if " ".join(k.split()) in flat else "  LOST  ") + repr(k[:48]))
for k in STALE:
    print(("  STALE " if " ".join(k.split()) in flat else "  clean ") + repr(k))
