import json
import pathlib
import re
import sys


def main() -> int:
    if len(sys.argv) != 3:
        print("Usage: extract_preview_json.py <input_terminal_txt> <output_json>")
        return 1

    input_path = pathlib.Path(sys.argv[1])
    output_path = pathlib.Path(sys.argv[2])

    raw = input_path.read_text(encoding="utf-8", errors="ignore")
    clean = re.sub(r"\x1b\[[0-9;]*m", "", raw)
    match = re.search(r"(\{\s*\"node\"\s*:\s*\".*?\"\s*,\s*\"show\"\s*:\s*\[.*?\]\s*\})", clean, re.DOTALL)
    if not match:
        print("Could not find preview JSON block in input.")
        return 2

    parsed = json.loads(match.group(1))
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(parsed, indent=2), encoding="utf-8")
    print(f"Wrote {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
