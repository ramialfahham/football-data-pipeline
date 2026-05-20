#!/usr/bin/env python3
"""Normalize Slack/chat brief payloads for executor intake."""

from __future__ import annotations

import argparse
import json
import re
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path


SCHEMA_VERSION = "2026-05-20"
BRIEF_ID_PATTERN = re.compile(r"^[a-zA-Z0-9._:-]{3,120}$")
MAX_TITLE_LEN = 160
MAX_BODY_LEN = 16000


class ValidationError(Exception):
    """Raised when payload validation fails."""


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _trimmed(value: str | None) -> str:
    return (value or "").strip()


def _validate_required_str(value: str | None, field: str) -> str:
    parsed = _trimmed(value)
    if not parsed:
        raise ValidationError(f"Missing required field: `{field}`.")
    return parsed


def _validate_brief_id(brief_id: str) -> str:
    if not BRIEF_ID_PATTERN.match(brief_id):
        raise ValidationError(
            "Invalid `brief_id`. Use 3-120 chars from [a-zA-Z0-9._:-]."
        )
    return brief_id


def _validate_webhook_url(url: str | None) -> str:
    parsed = _validate_required_str(url, "routing.response_webhook_url")
    if not (
        parsed.startswith("https://hooks.slack.com/")
        or parsed.startswith("https://hooks.slack-gov.com/")
    ):
        raise ValidationError(
            "Invalid `routing.response_webhook_url`. Expected a Slack incoming webhook URL."
        )
    return parsed


def _load_dispatch_payload(raw_json: str) -> dict:
    if not raw_json.strip():
        raise ValidationError("`client_payload` is empty for repository_dispatch.")
    try:
        parsed = json.loads(raw_json)
    except json.JSONDecodeError as exc:
        raise ValidationError(f"`client_payload` is not valid JSON: {exc}") from exc
    if not isinstance(parsed, dict):
        raise ValidationError("`client_payload` must be a JSON object.")
    return parsed


def _build_manual_payload(args: argparse.Namespace) -> dict:
    return {
        "schema_version": SCHEMA_VERSION,
        "brief_id": args.manual_brief_id or f"manual-{uuid.uuid4().hex[:12]}",
        "source": "chat",
        "brief": {
            "title": args.manual_title,
            "body": args.manual_body,
        },
        "requested_by": {
            "id": args.manual_requested_by or "manual-workflow-dispatch",
            "display_name": args.manual_requested_by_display or "Manual dispatch",
        },
        "routing": {
            "channel_id": args.manual_channel_id or "",
            "thread_ts": args.manual_thread_ts or "",
            "response_webhook_url": args.manual_response_webhook_url or "",
        },
    }


def _normalize(payload: dict, event_name: str, repository: str) -> dict:
    schema_version = _validate_required_str(payload.get("schema_version"), "schema_version")
    if schema_version != SCHEMA_VERSION:
        raise ValidationError(
            f"Unsupported `schema_version`: {schema_version}. Expected {SCHEMA_VERSION}."
        )

    source = _validate_required_str(payload.get("source"), "source").lower()
    if source not in {"slack", "chat"}:
        raise ValidationError("`source` must be either `slack` or `chat`.")

    brief = payload.get("brief")
    if not isinstance(brief, dict):
        raise ValidationError("Missing required object: `brief`.")
    title = _validate_required_str(brief.get("title"), "brief.title")
    body = _validate_required_str(brief.get("body"), "brief.body")
    if len(title) > MAX_TITLE_LEN:
        raise ValidationError(f"`brief.title` exceeds {MAX_TITLE_LEN} characters.")
    if len(body) > MAX_BODY_LEN:
        raise ValidationError(f"`brief.body` exceeds {MAX_BODY_LEN} characters.")

    requested_by = payload.get("requested_by")
    if not isinstance(requested_by, dict):
        raise ValidationError("Missing required object: `requested_by`.")
    requester_id = _validate_required_str(requested_by.get("id"), "requested_by.id")
    requester_name = _trimmed(requested_by.get("display_name")) or requester_id

    routing = payload.get("routing")
    if not isinstance(routing, dict):
        raise ValidationError("Missing required object: `routing`.")
    channel_id = _trimmed(routing.get("channel_id"))
    thread_ts = _trimmed(routing.get("thread_ts"))
    response_webhook_url = _trimmed(routing.get("response_webhook_url"))

    if source == "slack":
        channel_id = _validate_required_str(channel_id, "routing.channel_id")
        thread_ts = _validate_required_str(thread_ts, "routing.thread_ts")
        response_webhook_url = _validate_webhook_url(response_webhook_url)

    brief_id = _validate_brief_id(
        _validate_required_str(payload.get("brief_id"), "brief_id")
    )

    return {
        "schema_version": SCHEMA_VERSION,
        "brief_id": brief_id,
        "source": source,
        "submitted_at": _now_iso(),
        "repository": repository,
        "received_via": event_name,
        "requested_by": {
            "id": requester_id,
            "display_name": requester_name,
        },
        "brief": {
            "title": title,
            "body": body,
        },
        "routing": {
            "channel_id": channel_id,
            "thread_ts": thread_ts,
            "response_webhook_url": response_webhook_url,
        },
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Normalize Slack/chat brief payloads.")
    parser.add_argument("--event-name", required=True, help="GitHub event name")
    parser.add_argument("--client-payload-json", default="", help="Dispatch payload JSON")
    parser.add_argument("--repository", required=True, help="owner/repo")
    parser.add_argument("--out", required=True, help="Output JSON file")
    parser.add_argument("--summary-out", required=True, help="Output summary markdown file")

    parser.add_argument("--manual-title", default="")
    parser.add_argument("--manual-body", default="")
    parser.add_argument("--manual-brief-id", default="")
    parser.add_argument("--manual-requested-by", default="")
    parser.add_argument("--manual-requested-by-display", default="")
    parser.add_argument("--manual-channel-id", default="")
    parser.add_argument("--manual-thread-ts", default="")
    parser.add_argument("--manual-response-webhook-url", default="")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        if args.event_name == "repository_dispatch":
            payload = _load_dispatch_payload(args.client_payload_json)
        elif args.event_name == "workflow_dispatch":
            payload = _build_manual_payload(args)
        else:
            raise ValidationError(
                f"Unsupported event `{args.event_name}`. Use repository_dispatch or workflow_dispatch."
            )

        normalized = _normalize(payload, event_name=args.event_name, repository=args.repository)
    except ValidationError as exc:
        sys.stderr.write(f"Brief payload validation failed: {exc}\n")
        return 1

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(normalized, indent=2), encoding="utf-8")

    summary_lines = [
        "### Slack bridge intake",
        f"- brief_id: `{normalized['brief_id']}`",
        f"- source: `{normalized['source']}`",
        f"- received_via: `{normalized['received_via']}`",
        f"- requested_by: `{normalized['requested_by']['display_name']}`",
        f"- title: `{normalized['brief']['title']}`",
    ]
    if normalized["routing"]["channel_id"]:
        summary_lines.append(f"- channel_id: `{normalized['routing']['channel_id']}`")
    if normalized["routing"]["thread_ts"]:
        summary_lines.append(f"- thread_ts: `{normalized['routing']['thread_ts']}`")
    summary_lines.append("- response_webhook_url: `[redacted]`")

    summary_path = Path(args.summary_out)
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text("\n".join(summary_lines) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
