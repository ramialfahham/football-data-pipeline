#!/usr/bin/env python3
"""Replace FEEDBACK_ENDPOINT placeholder in match preview HTML (e.g. GitHub Actions before Pages upload)."""

from __future__ import annotations

import pathlib
import sys

PLACEHOLDER = (
    'const FEEDBACK_ENDPOINT = "https://script.google.com/macros/s/REPLACE_WITH_DEPLOYMENT_ID/exec";'
)


def main() -> int:
    if len(sys.argv) != 3:
        print("Usage: inject_feedback_endpoint.py <path-to-index.html> <apps-script-exec-url>", file=sys.stderr)
        return 1
    path = pathlib.Path(sys.argv[1])
    url = sys.argv[2].strip().rstrip("/")
    if not url.startswith("https://script.google.com/macros/s/") or "/exec" not in url:
        print("URL must be like https://script.google.com/macros/s/<id>/exec", file=sys.stderr)
        return 2
    text = path.read_text(encoding="utf-8")
    if PLACEHOLDER not in text:
        print(f"{path}: placeholder not found (skip or already injected)", file=sys.stderr)
        return 0
    escaped = url.replace("\\", "\\\\").replace('"', '\\"')
    replacement = f'const FEEDBACK_ENDPOINT = "{escaped}";'
    path.write_text(text.replace(PLACEHOLDER, replacement, 1), encoding="utf-8")
    print(f"Injected FEEDBACK_ENDPOINT into {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
