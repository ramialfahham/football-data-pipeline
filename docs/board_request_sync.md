# Board Request Sync

## Purpose

Keep founder requests visible across chats by auto-populating and updating the existing GitHub Project board from execution activity.

Workflow:
- `.github/workflows/board-request-sync.yml`

Target project title:
- `Matchday Pilot - Project Board`

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

### Least-privilege scope (audit F18 / #413)

The token authenticates **every** API call this workflow makes — the `github-token:`
input replaces the default `GITHUB_TOKEN` for the whole step, so the workflow's own
`permissions:` block (`contents/pull-requests/issues: read`) governs nothing here; the
PAT's own scope is what matters.

What the workflow actually does with it:

| Operation | API | Access needed |
|-----------|-----|---------------|
| List the user's ProjectsV2 + Status field/options | GraphQL `user.projectsV2` (org path is a NOT_FOUND fallback) | Projects: **read** |
| Read whether a PR/issue is already a board item | GraphQL `projectItems` sub-field of `repository.pullRequest` / `repository.issue` | Projects: **read** |
| Add a PR/issue to the board | GraphQL `addProjectV2ItemById` | Projects: **write** |
| Set the board item's Status | GraphQL `updateProjectV2ItemFieldValue` | Projects: **write** |
| Read a PR's state/draft/merged | GraphQL `repository.pullRequest`; REST `pulls.list` | Pull requests: **read** |
| Read an issue's state | GraphQL `repository.issue`; REST `issues.listForRepo` | Issues: **read** |

It never reads file contents and never writes to issues, PRs, or contents. Note that the
`projectItems` sub-field embedded in the PR/issue queries is governed by the **Projects**
permission, not by Issues / Pull requests — so Projects: read is required for the
existence check as well as for the writes.

**Use a fine-grained PAT** (the board is a **user-owned** ProjectV2 on `ramialfahham`,
and this is a **public** repo):

- **Resource owner:** `ramialfahham`
- **Repository access:** Only select repositories → `ramialfahham/football-data-pipeline`
- **Repository permissions:** Issues → **Read-only**; Pull requests → **Read-only**;
  Metadata → **Read-only** (mandatory baseline, auto-selected)
- **Account permissions:** Projects → **Read and write**
- Nothing else — no Contents, no Administration, no Workflows, no org permissions.

Note the split: the Issues / Pull requests / Metadata permissions above are
**repository** permissions and are limited to the one selected repo; **Projects** is an
**account** permission and applies to all ProjectsV2 the owner has — GitHub does not let
it be narrowed to a single project. That is unavoidable for either token type (see the
classic note below) and is the one permission that is account-wide by design.

A **classic** PAT works but is broader than needed and is **not recommended**: the only
classic scope that allows ProjectsV2 writes is `project`, which grants access to **all**
projects across the account (not just this board), and there is no narrower classic
project-write scope. If a classic token must be used, pair `project` with at most
`public_repo` (this repo is public) — **not** full `repo`. The older
`docs/project_status_sync.md` setup note that prescribes `repo, project` is superseded by
this section.

### Rotation

Setting/regenerating the token is a repo-admin action in GitHub settings
(`Settings → Secrets and variables → Actions → PROJECT_AUTOMATION_TOKEN`) — done by the
CPO, not by automation. This document specifies the scope to apply; it does not and
cannot change the live secret.

## Notes

- This replaces label-driven board state updates for daily execution memory.
- Dispatch queue and label-routing workflows remain paused.
- CI watchdog issues created by `ci-failure-watchdog` are also auto-added and status-synced.
