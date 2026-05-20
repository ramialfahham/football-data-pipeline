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
- No board-status automation.
- No heartbeat automation.
- No idea-intake form routing.
- No automation that reacts to issue labels or board state.

## What remains active

- `.github/workflows/pr-autopilot.yml`
- `.github/workflows/pages-match-preview.yml`
- `AGENTS.md` and role docs as assistant context

## What is paused

- `.github/workflows/_paused/cursor-dispatch.yml`
- `.github/workflows/_paused/project-status-sync.yml`
- `.github/ISSUE_TEMPLATE/_paused/idea_intake.yml`

These assets are retained for recovery, but excluded from active automation.
