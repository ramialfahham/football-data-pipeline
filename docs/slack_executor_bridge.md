# Slack-to-Executor Bridge

> PAUSED 2026-05-20 — Slack intake is disabled; chat-driven briefs are the active path.
> Archived workflow location: `.github/workflows/_paused/slack-executor-bridge.yml`.

## Purpose

Accept a brief from Slack and route it into the same execution path used for chat briefs:

`brief -> executor -> PR -> autopilot merge -> deploy -> Slack thread confirmation`

This bridge does not create tickets, labels, or board updates.

## Active workflow

- None (workflow paused)

Triggers:
- `repository_dispatch` with `event_type=slack_executor_brief`
- optional manual `workflow_dispatch` for dry-run testing

## Interface contract (payload shape)

The bridge expects `client_payload` in this exact shape:

{
  "schema_version": "2026-05-20",
  "brief_id": "slack-20260520-001",
  "source": "slack",
  "requested_by": {
    "id": "U01234567",
    "display_name": "Rami"
  },
  "brief": {
    "title": "Short title",
    "body": "Full implementation brief text"
  },
  "routing": {
    "channel_id": "C01234567",
    "thread_ts": "1716227770.123456",
    "response_webhook_url": "https://hooks.slack.com/services/..."
  }
}

Notes:
- `response_webhook_url` is used to post callbacks to the same Slack thread.
- The URL is redacted from workflow summaries.
- `brief_id` is the idempotency key and must be stable for retries.

## Error handling

- Validation errors (missing/invalid fields) fail fast in `normalize_brief.py`.
- Executor forwarding retries 3 times on transient errors (`408`, `409`, `425`, `429`, `5xx`, network failures).
- If forwarding still fails:
  - workflow run fails
  - bridge posts a `failed` update to the same Slack thread (if webhook is present)
- If no executor endpoint secret is configured:
  - brief is accepted and stored as an artifact
  - workflow succeeds with status `accepted_not_forwarded`

## Slack-side wiring (exact steps)

Do only this on Slack side when you are ready:

1. Create a dedicated channel, for example `#product-briefs`.
2. Create/enable an Incoming Webhook for that channel in your Slack app.
3. In Slack Workflow Builder (or your Slack automation tool), trigger on new message in the channel.
4. Add an HTTP step that calls GitHub Repository Dispatch:
   - URL: `https://api.github.com/repos/ramialfahham/football-data-pipeline/dispatches`
   - Method: `POST`
   - Headers:
     - `Authorization: Bearer <GITHUB_DISPATCH_TOKEN>`
     - `Accept: application/vnd.github+json`
     - `Content-Type: application/json`
   - Body:
     {
       "event_type": "slack_executor_brief",
       "client_payload": {
         "schema_version": "2026-05-20",
         "brief_id": "<stable-unique-id>",
         "source": "slack",
         "requested_by": {
           "id": "<slack-user-id>",
           "display_name": "<slack-display-name>"
         },
         "brief": {
           "title": "<message-title>",
           "body": "<full-brief-text>"
         },
         "routing": {
           "channel_id": "<channel-id>",
           "thread_ts": "<thread-ts>",
           "response_webhook_url": "<incoming-webhook-url>"
         }
       }
     }
5. Store the GitHub dispatch token in Slack secret storage (do not hardcode it in plain text).
6. When unpaused, post a test brief and confirm workflow `slack-executor-bridge` appears in GitHub Actions.

## Repo-side secrets for forwarding to executor

Optional (for full automation into an executor endpoint):
- `CURSOR_EXECUTOR_BRIDGE_URL`
- `CURSOR_EXECUTOR_BRIDGE_TOKEN`

Without these, the bridge still accepts Slack briefs and stores normalized payload artifacts.

## Until Slack is wired

Chat-pasted briefs remain the primary path and follow the same no-ticket flow.
