# Review — fix/watchdog-watch-dbt-scheduled — 2026-07-11

> Governance G3 review artifact. Required reviewers for the staged paths (review_routing.json):
> scope-auditor (always), cto-reviewer (.github/workflows/**). Blinded reviewers ran cold against the
> cumulative staged branch diff (`.claude/task/review_input.patch`) after Code Lock. cto-reviewer was
> spawned on opus (guard-path override: the diff touches `.github/workflows/**`).

diff_sha256: 9fa56f838ac6017e4633dd474fd3fb22b0ada5037db9430831576fb19ef5395f

## scope-auditor
VERDICT: PASS
risks_checked:
- Protected-path override boundary: contract carries the CPO-authorized override for `.github/workflows/ci-failure-watchdog.yml` scoped to "add exactly one list item (`- dbt-scheduled`) ... no change to any other workflow, trigger, job, permission, or script". The diff shows exactly one added line; both changed files (`ci-failure-watchdog.yml`, `.claude/task/contract.md`) fall inside `scope_paths`; no undeclared or creeping change. Boundary honored, tight.
- Decision rights (§10) + deferred-decision handling: adding a workflow name to an existing watch list is pure configuration within an already-proven mechanism (no new mechanism, no user-visible naming, no changed shipped numbers). The `ci-site-v2` / `pages` prod-writers are correctly recorded in `decisions_reserved` as DEFERRED (flagged for the PR, not silently decided nor silently scoped away); deferring rather than blinded-escalating is defensible because the CPO explicitly scoped the change to the single line.

## cto-reviewer
VERDICT: PASS
risks_checked:
- Silently-dead watch entry (the whole point): `workflow_run.workflows:` keys on the producer's `name:`, not filename. Verified `dbt-scheduled` matches `name: dbt-scheduled` in `.github/workflows/dbt-scheduled.yml:1` character-for-character, and cross-checked all six pre-existing entries against their own `name:` fields — the list is consistently name-keyed, so the new entry actually fires (confirmed by contrast with the deferred `pages-match-preview`, whose name is `Deploy match preview (GitHub Pages)`).
- YAML validity / reparenting: the single added line `- dbt-scheduled` is at 6-space indent, a correct sibling under `on.workflow_run.workflows:`, above `types: [completed]`; still inside `on.workflow_run`, valid parse, no accidental reparent.
- Issue storm / self-trigger / permissions: de-dup by exact title on the default branch yields one open issue that gets comments (not new issues) on repeat nightly failures; `run.name` != `ci-failure-watchdog` avoids the self-ignore false-positive and the watchdog isn't in its own list (no infinite loop); `issues: write` present — no new failure mode.
- Trigger + concurrency edge cases: cron runs only on the default branch so `head_branch`=main and `workflow_run` uses the merged default-branch watchdog; `cancel-in-progress: false` on the shared prod group prevents a concurrency-cancel producing a spurious failure conclusion.
- Scope/guard integrity: diff is exactly one workflow line + the in-scope contract rewrite; `protected_override` quotes the CPO go for this exact guard path and one-item scope; pure config, no new mechanism, not a gate (fail-open N/A), no cost change.

## escalations
(none)
