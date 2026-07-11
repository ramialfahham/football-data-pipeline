# Task contract — watch ci-site-v2 + pages-match-preview in the CI-failure watchdog

> Written on a CLEAN tree (branch fix/watchdog-watch-site-and-pages off main @ 4f19d60).
> Follow-up to #670, which added dbt-scheduled and flagged these two for a separate owner decision.
> CPO-directed this conversation 2026-07-11 ("do the follow-ups").

objective: >
  Add the two remaining unwatched significant workflows to the CI-failure watchdog's
  `on.workflow_run.workflows:` list, so a failure of either opens/updates a triage issue like every
  other watched workflow. #670 deferred these for the owner to decide; the owner has now decided to add
  both. Two lines, no other changes:
    - `pages-match-preview` (name: `Deploy match preview (GitHub Pages)`) — a genuine prod-writer:
      `dbt seed` + `dbt run --target prod` + DQ tests on a 07:30 cron, then Pages export/deploy. Same
      high-stakes class as dbt-scheduled; its failure was otherwise only a missable email.
    - `ci-site-v2` (name: `ci-site-v2`) — NOT a prod-writer (the "may also write prod" premise from #670
      is off for this one): it is an `npm run build` check path-filtered to `site_v2/**`, i.e. the v2
      analog of ci-ui, which is already watched. Added for parity — a significant CI workflow whose
      failure should raise an issue.
  Also record the outcome in the handover (`.claude/active_work.md`, artifact-only follow-up commit).
refs: #670 (parent — added dbt-scheduled, flagged these two); CPO-directed 2026-07-11 (this conversation).
  Watchdog: .github/workflows/ci-failure-watchdog.yml.

protected_override: >
  CPO-authorized 2026-07-11 (this conversation, "do the follow-ups") to edit the PROTECTED
  `.github/workflows/` guard path ci-failure-watchdog.yml. Override scope: add exactly two list items to
  the existing `on.workflow_run.workflows:` list — `ci-site-v2` and `"Deploy match preview (GitHub
  Pages)"` (the pages-match-preview workflow's `name:`, since workflow_run keys on `name:` not filename).
  No change to any other workflow, trigger, job, permission, or script.

scope_paths:
  - .github/workflows/ci-failure-watchdog.yml
  - .claude/active_work.md
  - .claude/task/**

decisions_taken: >
  Add both workflows. The owner ("do the follow-ups") approved adding the two deferred candidates from
  #670. Each list entry uses the workflow's exact `name:` field (verified against the source files):
  `ci-site-v2` and `Deploy match preview (GitHub Pages)`. The ci-site-v2 clarification (build-check, not a
  prod-writer) is a factual note, not a new decision — it still belongs on the list for parity with the
  already-watched ci-ui. Pure configuration within the existing watchdog mechanism.

decisions_reserved:
  - (none) — #670's single deferred decision (whether to watch these two) is the one the owner just made.
    No further watchdog candidates remain: all significant workflows are now on the list.

done_when:
  - `on.workflow_run.workflows:` in ci-failure-watchdog.yml contains `- ci-site-v2` and
    `- "Deploy match preview (GitHub Pages)"` alongside the existing seven.
  - Exactly two lines added to the workflow; `git diff` shows nothing else in that file.
  - Each added name matches the `name:` of its source workflow character-for-character.
  - YAML valid; scope-auditor + cto-reviewer (opus, guard path) PASS; review.md diff_sha256 binds; CPO merges.
  - Handover bullet added to `.claude/active_work.md` (artifact-only commit) noting #670 + this PR.

amendments: (none)
