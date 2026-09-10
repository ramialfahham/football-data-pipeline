"""Scan a fetched issue body for stale terms. Reads the glab JSON on stdin, forced to UTF-8,
and writes ASCII-safe output so the cp1252 console cannot blow up on a warning sign."""
import io
import json
import sys

sys.stdin = io.TextIOWrapper(sys.stdin.buffer, encoding="utf-8")
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

d = json.load(sys.stdin)
t = d["description"]
terms = sys.argv[1:] or ["crest", "480px"]

print(d["references"]["short"], "-- scanning for:", ", ".join(terms))
hits = 0
for i, line in enumerate(t.splitlines(), 1):
    low = line.lower()
    if any(term.lower() in low for term in terms):
        hits += 1
        print("  %4d | %s" % (i, line.strip()[:105]))
print("  total lines matching:", hits)
