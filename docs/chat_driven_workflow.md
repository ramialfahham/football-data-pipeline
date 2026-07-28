# Chat-Driven Product Workflow

## Active mode

Effective date: `2026-05-20`.

This repository is operating in chat-driven mode until proven:

1. Founder posts a brief in chat.
2. Assistant implements the brief directly in the repo.
3. Assistant opens a PR.
4. `pr-autopilot` enables auto-merge when mergeable.
5. Merge to `main` triggers deploy workflow(s).
6. Assistant confirms live status in chat.

## Hard rules in this mode

- No ticket dispatch machinery.
- No heartbeat automation.
- No idea-intake form routing.
- No automation that reacts to issue labels.

## Board execution memory (active)

To keep requests visible across chats, board sync is active via:

- `.github/workflows/board-request-sync.yml`

Behavior:
- Auto-add open PRs and open issues to `Matchday Pilot - Project Board`
- Auto-update `Status` from item state (for example `In Progress`, `Done`, `Live`)
- No label requirements

## CI failure detection (active)

To avoid founder-only monitoring, CI watchdog is active:

- `.github/workflows/ci-failure-watchdog.yml`

Behavior:
- Detects failed CI runs for core workflows
- Creates/updates a `[CI Failure] ...` issue with run link and next actions

It does not rerun jobs automatically — reruns are a manual decision so transient
(flaky) failures stay visible rather than being silently retried.

## What remains active

- `.github/workflows/pr-autopilot.yml`
- `.github/workflows/pages-match-preview.yml`
- `.github/workflows/board-request-sync.yml`
- `.github/workflows/ci-failure-watchdog.yml`
- `AGENTS.md` and role docs as assistant context

## What is paused

- `.github/workflows/_paused/cursor-dispatch.yml`
- `.github/workflows/_paused/project-status-sync.yml`
- `.github/ISSUE_TEMPLATE/_paused/idea_intake.yml`

These assets are retained for recovery, but excluded from active automation.
