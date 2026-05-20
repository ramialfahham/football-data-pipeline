# PR Autopilot (Controlled Merge Automation)

## What this automates

Workflow: `.github/workflows/pr-autopilot.yml`

- Runs on PR events, hourly schedule, and manual trigger.
- Auto-updates PR branches from `main` when they are behind and updateable.
- Detects merge conflicts and leaves a bot comment marker on the PR.
- Enables GitHub auto-merge (squash) when:
  - PR is not draft
  - PR is not conflicting

Auto-merge then waits for required checks/branch protections and merges automatically when they pass.

---

## Founder workflow (plain language)

1. Team/agents open PRs as usual.
2. Autopilot handles branch update, conflict signaling, and auto-merge enablement.
3. If there is a conflict, autopilot posts a bot comment with next steps.

You stay focused on briefs and outcomes, not merge mechanics.

---

## What is not automated

- Complex conflict resolution still requires an agent/human.
