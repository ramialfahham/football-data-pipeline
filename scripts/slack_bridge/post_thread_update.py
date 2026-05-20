#!/usr/bin/env python3
"""Post status updates back to a Slack thread via incoming webhook."""

from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Post update to Slack thread webhook.")
    parser.add_argument("--brief-json", required=True, help="Path to normalized brief JSON")
    parser.add_argument("--status", required=True, choices=["received", "failed", "shipped"])
    parser.add_argument("--message", required=True, help="Status message")
    parser.add_argument("--shipped-url", default="", help="Optional shipped URL")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    brief_payload = json.loads(Path(args.brief_json).read_text(encoding="utf-8"))
    routing = brief_payload.get("routing", {})
    webhook_url = (routing.get("response_webhook_url") or "").strip()

    if not webhook_url:
        print("No response webhook URL set. Skipping Slack callback.")
        return 0

    parts = [f"*Status:* `{args.status}`", args.message]
    if args.shipped_url.strip():
        parts.append(f"Shipped to: {args.shipped_url.strip()}")
    text = "\n".join(parts)

    payload = {"text": text}
    thread_ts = (routing.get("thread_ts") or "").strip()
    if thread_ts:
        payload["thread_ts"] = thread_ts

    req = urllib.request.Request(
        url=webhook_url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as response:
            if response.status < 200 or response.status >= 300:
                raise RuntimeError(f"Unexpected Slack webhook status {response.status}")
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, RuntimeError) as exc:
        sys.stderr.write(f"Slack callback failed: {exc}\n")
        return 1

    print("Slack callback posted.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
