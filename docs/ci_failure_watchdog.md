# CI Failure Watchdog

## Purpose

Detect CI failures automatically, trigger one immediate auto-recovery attempt, and create a persistent triage record without requiring founder monitoring.

Workflow:
- `.github/workflows/ci-failure-watchdog.yml`

## Tracked workflows

- `ci-validate`
- `ci-data-build`
- `ci-ui`
- `python-ci`
- `security-secrets`
- `board-request-sync`

## Behavior

When a tracked workflow run completes with `failure`:

1. If `run_attempt == 1`, watchdog calls GitHub's `rerun-failed-jobs`.
2. It creates or updates a dedicated issue:
   - Title: `[CI Failure] <workflow> on <branch>`
   - Includes failed run URL, attempt, trigger actor, and rerun outcome.
3. The issue is then visible to board sync automation for prioritization/execution.

## Notes

- This does not attempt speculative code edits.
- It auto-recovers transient failures and guarantees every persistent failure is surfaced as an executable item.
