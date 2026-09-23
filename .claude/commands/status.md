---
description: Snapshot of where work stands — branch, tree, open MRs + CI, and the active handover.
allowed-tools: Bash(git branch --show-current), Bash(git status --short), Bash(git log --oneline -5), Bash(glab mr list *), Bash(glab ci list *), Bash(glab issue view 157), Read(.claude/handover.cache.md)
---

Give the user a fast, read-only situational snapshot. Be concise — short sections, no
preamble — and do NOT start any work.

## Branch & working tree
- Branch: !`git branch --show-current`
- Uncommitted changes: !`git status --short`
- Recent commits: !`git log --oneline -5`

## Open MRs
!`glab mr list --output json --jq '.[] | {mr: .iid, branch: .source_branch, title, merge_status: .detailed_merge_status}'`

## Recent pipelines
!`glab ci list --per-page 10`

Summarize each open MR as one line: `!<n> <title> [branch] — CI: <status of that branch's latest pipeline, or "none" if no pipeline ran>`.
Match pipelines to MRs by branch name; GitLab reports MR merge status and pipeline status separately.

## Active handover
The handover is GitLab issue #157. Read it with `glab issue view 157`; if GitLab cannot be
reached, read `.claude/handover.cache.md` (the copy saved at session start) and say so. Report
ONLY: the _Last updated_ line, the **NEXT** actions, and any live **Do NOT** items. Do not
reproduce the whole handover.

## Bottom line
Close with 2–3 plain-English lines: where things stand and the single most likely next
action. This command is reporting only — take no action.
