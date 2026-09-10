"""Build a JSON request body for glab api --input.

`--raw-field description=@<path>` did not read the file on this platform -- it sent the
path itself as the value (131 chars). A JSON body leaves no room for that ambiguity.
"""
import json
import sys
from pathlib import Path

here = Path(__file__).parent
src = here / sys.argv[1]
out = here / sys.argv[2]

payload = {"description": src.read_text(encoding="utf-8")}
if len(sys.argv) > 3:
    payload["title"] = sys.argv[3]

out.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
print("payload:", out.name, "| description chars:", len(payload["description"]))
