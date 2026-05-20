# PR Autopilot (Controlled Merge Automation)

## What this automates

Workflow: `.github/workflows/pr-autopilot.yml`

- Runs on PR events, hourly schedule, and manual trigger.
- Ensures governance labels exist:
  - `cpo-approved`
  - `merge-conflict`
  - `auto-merge-enabled`
- Auto-updates PR branches from `main` when they are behind and updateable.
- Detects merge conflicts and labels PRs with `merge-conflict`.
- Enables GitHub auto-merge (squash) only when:
  - PR is not draft
  - PR has label `cpo-approved`
  - PR does not have label `decision-needed`
  - PR is not conflicting

Auto-merge then waits for required checks/branch protections and merges automatically when they pass.

---

## Founder workflow (plain language)

1. Team/agents open PRs as usual.
2. You only add `cpo-approved` when ready to ship.
3. Autopilot handles branch update, conflict signaling, and auto-merge enablement.
4. If there is a conflict, PR gets `merge-conflict` and a bot comment.

You stay focused on approval and decisions, not merge mechanics.

---

## What is not automated

- Complex conflict resolution still requires an agent/human.
- `decision-needed` PRs are intentionally blocked from auto-merge.

---

## Labels meaning

- `cpo-approved`: founder approved, safe to auto-merge once checks pass.
- `auto-merge-enabled`: automation enabled merge on this PR.
- `merge-conflict`: PR has conflicts that must be resolved before merge.
