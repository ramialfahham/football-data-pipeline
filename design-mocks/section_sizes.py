"""Size of each handover section, largest first -- so a trim targets the real weight."""
import io
import re
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

s = (Path(__file__).resolve().parent.parent / ".claude/active_work.md").read_text(encoding="utf-8")
parts = re.split(r"\n(?=## )", s)
rows = []
for p in parts:
    head = p.splitlines()[0][:66]
    rows.append((len(p), head))
for n, head in sorted(rows, reverse=True):
    print("%5d  %s" % (n, head))
print("-----\ntotal:", len(s), "| over by", len(s) - 16000)
