# Board Request Sync

## Purpose

Keep founder requests visible across chats by auto-populating and updating the existing GitHub Project board from execution activity.

Workflow:
- `.github/workflows/board-request-sync.yml`

Target project title:
- `Matchday IQ - Project Board`

## What it does

- On PR open/update/close:
  - ensures the PR is present on the project board
  - updates `Status` based on PR state
- On issue open/close:
  - ensures the issue is present on the project board
  - updates `Status` based on issue state
- On manual run (`workflow_dispatch`):
  - syncs all open PRs and open issues

## Status mapping

PRs:
- open draft -> `In Progress` (fallback `Todo`)
- open ready -> `In Progress` (fallback `Review`, then `Todo`)
- closed merged -> `Live` (fallback `Done`)
- closed unmerged -> `Blocked` (fallback `Done`)

Issues:
- open -> `Todo` (fallback `In Progress`)
- closed -> `Done` (fallback `Live`)

## Required secret

Repository secret:
- `PROJECT_AUTOMATION_TOKEN`

Token must have scopes needed to update user/org projects.

## Notes

- This replaces label-driven board state updates for daily execution memory.
- Dispatch queue and label-routing workflows remain paused.
