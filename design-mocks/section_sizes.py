"""Size of each handover section, largest first -- so a trim targets the real weight. Reads the
draft named as the argument, else the copy of GitLab issue #157 the session-start hook saved."""
import io
import re
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

p = (Path(sys.argv[1]) if len(sys.argv) > 1
     else Path(__file__).resolve().parent.parent / ".claude/handover.cache.md")
s = p.read_text(encoding="utf-8")
parts = re.split(r"\n(?=## )", s)
rows = []
for p in parts:
    head = p.splitlines()[0][:66]
    rows.append((len(p), head))
for n, head in sorted(rows, reverse=True):
    print("%5d  %s" % (n, head))
print("-----\ntotal:", len(s), "| over by", len(s) - 16000)
