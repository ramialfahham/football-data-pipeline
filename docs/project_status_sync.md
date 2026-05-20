# Project Status Sync Setup

> PAUSED 2026-05-20 — board-status automation is disabled in favor of chat-driven delivery.
> Archived workflow location: `.github/workflows/_paused/project-status-sync.yml`.

## Purpose

Automatically move Project board status columns from issue state and labels:

- `agent-running` -> `In Progress`
- `decision-needed` or `blocked` -> `Blocked`
- closed issue -> `Done`
- default open issue -> `Todo`

Workflow: `.github/workflows/project-status-sync.yml`

---

## One-time secret setup

Add this repository secret:

- Name: `PROJECT_AUTOMATION_TOKEN`
- Value: GitHub personal access token (classic)
- Scopes: `repo`, `project`

Settings path:

- `https://github.com/ramialfahham/football-data-pipeline/settings/secrets/actions`

---

## Board title requirement

The workflow targets the Project titled:

- `Matchday IQ - Project Board`

If you rename the project, update `PROJECT_BOARD_TITLE` in the workflow file.

---

## Triggers

Runs automatically on:

- issue opened/reopened/edited/labeled/unlabeled/closed
- hourly schedule
- manual `workflow_dispatch`

---

## Founder usage

You do not manually move cards between `Todo`, `In Progress`, `Blocked`, and `Done` anymore.

The automation does it based on ticket labels and state.
