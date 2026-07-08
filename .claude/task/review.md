# Review — fix/667-prod-writer-concurrency — 2026-07-08

> Machine-checked review artifact (governance G3). Required reviewers for the staged paths
> (review_routing.json): scope-auditor (always), cto-reviewer (.github/workflows/**). Follow-up to #668 —
> serialises the three prod-writing workflows under one shared `prod-warehouse-write` concurrency group
> (issue #667). Concurrency-only change; the three protected workflow edits are covered by protected_override.

diff_sha256: 7869591be6d45c329f5026d4cc8467e5eb7f068fd3a407a0e8b4b9f24e4828a2

## scope-auditor
VERDICT: PASS
risks_checked:
- All modified paths ⊆ scope_paths; the three protected `.github/workflows/` edits are covered by the contract's protected_override, and the diff is concurrency-only — triggers, path filters, the `gate` job, required-check logic, ingest skip, and dbt targets/steps are untouched. Group naming is GitHub-Actions mechanics, not a §10 class.
- ci-data-build's group formula `${{ pull_request && 'ci-data-build-write-ci' || 'prod-warehouse-write' }}` routes all three event types correctly (PR → own ci group; push/dispatch → shared prod group); an inverted formula would serialise PRs with prod and re-introduce the MERGE race — verified correct.

## cto-reviewer
VERDICT: PASS
risks_checked:
- The shared group name is character-identical (`prod-warehouse-write`) across all three files, and GitHub's concurrency namespace is flat/repo-scoped regardless of workflow-vs-job level — so the three prod-writers genuinely serialise as one; pages is job-level on `build` (sibling to permissions/defaults), structurally separate from the workflow-level `pages-match-preview` group and the untouched `deploy` job.
- `cancel-in-progress: false` on all four blocks (a queued run never cancels an in-flight prod MERGE); ci-data-build's PR arm resolves to the distinct `ci-data-build-write-ci`, so PR builds are not pulled into prod serialization. No permissions/secrets/cost drift; the only side effect is bounded queuing latency (no billable minutes while queued).

## escalations
(none)
