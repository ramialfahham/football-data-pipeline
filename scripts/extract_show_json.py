"""Extract dbt show --output json blob from a log file into app-ready matchday_insights.json."""
import json
import pathlib
import re
import sys


def main() -> int:
    if len(sys.argv) != 3:
        print("Usage: extract_show_json.py <dbt_show_log.txt> <output.json>")
        return 1
    raw_text = pathlib.Path(sys.argv[1]).read_text(encoding="utf-8", errors="ignore")
    clean = re.sub(r"\x1b\[[0-9;]*m", "", raw_text)
    start = clean.find('{\n  "node"')
    if start == -1:
        start = clean.find('{"node"')
    if start == -1:
        print("Could not find JSON object start.")
        return 2
    brace = 0
    end = None
    for pos in range(start, len(clean)):
        ch = clean[pos]
        if ch == "{":
            brace += 1
        elif ch == "}":
            brace -= 1
            if brace == 0:
                end = pos
                break
    if end is None:
        print("Could not find balanced JSON object.")
        return 3
    obj = json.loads(clean[start : end + 1])
    out = pathlib.Path(sys.argv[2])
    out.write_text(json.dumps(obj, indent=2), encoding="utf-8")
    print(f"Wrote {out} ({len(obj.get('show', []))} rows)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
