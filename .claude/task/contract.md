# Task contract — watch dbt-scheduled in the CI-failure watchdog

> Written on a CLEAN tree (branch fix/watchdog-watch-dbt-scheduled off main @ 7fd56f9).
> CPO-directed this conversation 2026-07-11 ("make only that one-line edit, push, open a PR").

objective: >
  Add `dbt-scheduled` to the CI-failure watchdog's `on.workflow_run.workflows:` watch list so a failed
  nightly prod build — ingestion + `dbt build --target prod` + the prod data-quality tests — opens/updates
  a GitHub issue like every other watched workflow. Today `dbt-scheduled` is the ONLY significant workflow
  absent from the list, so its failures (including a DQ test failing on real prod data) have no backstop
  beyond GitHub's default "scheduled workflow failed" email, which is easy to miss. It reads as an
  accidental omission; this closes the alerting blind spot. One line, no other changes.
refs: CPO-directed 2026-07-11 (this conversation). Watchdog: .github/workflows/ci-failure-watchdog.yml;
  the unwatched producer: .github/workflows/dbt-scheduled.yml (nightly cron `0 4 * * *`).

protected_override: >
  CPO-authorized 2026-07-11 (this conversation, "make only that one-line edit ... Follow this repo's own
  working agreement / guardrails") to edit the PROTECTED `.github/workflows/` guard path
  ci-failure-watchdog.yml. Override scope: add exactly one list item (`- dbt-scheduled`) to the existing
  `on.workflow_run.workflows:` list. No change to any other workflow, trigger, job, permission, or script.

scope_paths:
  - .github/workflows/ci-failure-watchdog.yml
  - .claude/task/**

decisions_taken: >
  Add `dbt-scheduled` and only `dbt-scheduled`. This mirrors the six workflows already watched and requires
  no new mechanism — the watchdog already keys off `workflow_run.conclusion == 'failure'` for whatever is in
  the list, so adding a name is pure configuration within the CPO "make only that one-line edit" go.

decisions_reserved:
  - `ci-site-v2` and any `pages` / `pages-match-preview` workflow may ALSO write prod and are likewise absent
    from the watchdog list. Whether to add them is a separate call for the owner — DEFERRED, not decided here.
    Flagged in the PR body; explicitly OUT of this task's scope per the CPO's instruction to change only the
    one line. Escalating it blinded is unnecessary — the CPO already scoped it out and asked only for the note.

done_when:
  - `on.workflow_run.workflows:` in ci-failure-watchdog.yml contains `- dbt-scheduled` alongside the existing six.
  - Exactly one line added; `git diff` shows a single `+  - dbt-scheduled` and nothing else.
  - YAML valid; scope-auditor + cto-reviewer (opus, guard path) PASS; review.md diff_sha256 binds; CPO merges.

amendments: (none)
