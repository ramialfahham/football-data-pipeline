#!/usr/bin/env python3
"""Forward normalized brief payload to an executor endpoint."""

from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Forward brief to executor endpoint.")
    parser.add_argument("--brief-json", required=True, help="Path to normalized brief JSON")
    parser.add_argument("--endpoint-url", default="", help="Executor intake endpoint")
    parser.add_argument("--bearer-token", default="", help="Optional bearer token")
    parser.add_argument("--result-out", required=True, help="Output result JSON path")
    return parser.parse_args()


def _post_json(url: str, payload: dict, bearer_token: str) -> tuple[int, str]:
    encoded = json.dumps(payload).encode("utf-8")
    headers = {"Content-Type": "application/json"}
    if bearer_token:
        headers["Authorization"] = f"Bearer {bearer_token}"
    request = urllib.request.Request(url=url, data=encoded, headers=headers, method="POST")
    with urllib.request.urlopen(request, timeout=20) as response:
        body = response.read().decode("utf-8", errors="replace")
        return response.status, body


def main() -> int:
    args = parse_args()
    brief_payload = json.loads(Path(args.brief_json).read_text(encoding="utf-8"))
    result_path = Path(args.result_out)
    result_path.parent.mkdir(parents=True, exist_ok=True)

    if not args.endpoint_url.strip():
        result = {
            "status": "accepted_not_forwarded",
            "reason": "No executor endpoint configured",
            "brief_id": brief_payload.get("brief_id", ""),
        }
        result_path.write_text(json.dumps(result, indent=2), encoding="utf-8")
        print("No executor endpoint configured. Brief accepted locally.")
        return 0

    last_error = ""
    for attempt in range(1, 4):
        try:
            status_code, response_body = _post_json(
                url=args.endpoint_url.strip(),
                payload=brief_payload,
                bearer_token=args.bearer_token.strip(),
            )
            if 200 <= status_code < 300:
                result = {
                    "status": "forwarded",
                    "brief_id": brief_payload.get("brief_id", ""),
                    "executor_status_code": status_code,
                    "executor_response": response_body,
                }
                result_path.write_text(json.dumps(result, indent=2), encoding="utf-8")
                print(f"Forwarded brief to executor endpoint (status={status_code}).")
                return 0
            if status_code in {408, 409, 425, 429} or status_code >= 500:
                last_error = f"HTTP {status_code}: {response_body}"
                time.sleep(2 ** attempt)
                continue
            last_error = f"HTTP {status_code}: {response_body}"
            break
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            last_error = f"HTTP {exc.code}: {body}"
            if exc.code in {408, 409, 425, 429} or exc.code >= 500:
                time.sleep(2 ** attempt)
                continue
            break
        except urllib.error.URLError as exc:
            last_error = f"Network error: {exc.reason}"
            time.sleep(2 ** attempt)
        except TimeoutError:
            last_error = "Timeout while connecting to executor endpoint"
            time.sleep(2 ** attempt)

    result = {
        "status": "forward_failed",
        "brief_id": brief_payload.get("brief_id", ""),
        "error": last_error or "Unknown executor forwarding error",
    }
    result_path.write_text(json.dumps(result, indent=2), encoding="utf-8")
    sys.stderr.write(f"Executor forwarding failed: {result['error']}\n")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
