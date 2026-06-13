# CI Failure Watchdog

## Purpose

Detect CI failures automatically and create a persistent triage record without requiring founder monitoring.

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

1. It creates or updates a dedicated issue:
   - Title: `[CI Failure] <workflow> on <branch>`
   - Includes failed run URL, attempt, and trigger actor.
2. The issue is then visible to board sync automation for prioritization/execution.

The watchdog does not rerun jobs. Reruns are a manual decision so transient (flaky)
failures stay visible rather than being silently retried. It holds only `issues: write`
(plus `contents: read`); it does not carry `actions: write`.

## Notes

- This does not attempt speculative code edits.
- It guarantees every CI failure is surfaced as an executable item; recovery (rerun or fix) is a manual decision.
