# Review — fix/watchdog-watch-site-and-pages — 2026-07-11

> Governance G3 review artifact. Required reviewers for the staged paths (review_routing.json):
> scope-auditor (always), cto-reviewer (.github/workflows/**). Blinded reviewers ran cold against the
> cumulative staged branch diff (`.claude/task/review_input.patch`) after Code Lock. cto-reviewer was
> spawned on opus (guard-path override: the diff touches `.github/workflows/**`).
>
> Process note (transparency): the first scope-auditor pass FAILed because `.claude/active_work.md` was
> declared in scope_paths/done_when but absent from the reviewed diff (it had been planned as a separate
> post-review commit). Fixed by folding the handover edit INTO this reviewed commit; scope-auditor was
> re-run and PASSes. `.claude/active_work.md` is in `hash_exclude_paths`, so the diff_sha256 below is
> unchanged (it covers the workflow + contract only), and it does not route to cto-reviewer — whose review
> covers the workflow, which is byte-identical to what it saw. cto-reviewer's verdict therefore stands.

diff_sha256: e621ad6b391abb8634d88eeef71c045118c293f49b177f204607d41daf3c23e4

## scope-auditor
VERDICT: PASS
risks_checked:
- Protected-path scope drift on the watchdog file: the diff touches the protected `.github/workflows/ci-failure-watchdog.yml`. Verified it adds exactly the two authorized list items to `on.workflow_run.workflows:`, with no change to triggers, permissions, job definitions, or the github-script — a hidden mechanism/trigger/permission injection would be a critical breach; the surgical limitation to the two named override items rules out drift.
- Handover artifact completeness and accuracy (the prior-round FAIL): verified `.claude/active_work.md` is now present in the diff, the change is confined to a handover bullet (no code/config smuggled as a doc edit), and it accurately records both workflows (pages-match-preview as prod-writer; ci-site-v2 as build-check for parity with the already-watched ci-ui) and the decision chain (#670 flagged both → CPO "do the follow-ups"). Decision rights: the CPO named both items in the protected_override, so adding them — including ci-site-v2 despite the corrected "not a prod-writer" premise — is executing granted scope, not a builder-manufactured §10 decision.

## cto-reviewer
VERDICT: PASS
risks_checked:
- Name-match (workflow_run keys on `name:` not filename): verified both entries against source `name:` fields character-for-character — `ci-site-v2`==`ci-site-v2` (ci-site-v2.yml:6) and `"Deploy match preview (GitHub Pages)"`==`Deploy match preview (GitHub Pages)` (pages-match-preview.yml:1; parens, spaces, GitHub capitalization all identical). Neither entry is silently dead. Double-quoting resolves to the exact literal and is correct/harmless.
- YAML placement: both new items are 6-space-indented siblings under `on.workflow_run.workflows:`, directly above `types: [completed]`, still inside `workflow_run` (no reparenting of `types`/`workflow_dispatch`); the list now has 9 entries. Parses cleanly.
- De-dup / issue-storm / parentheses in title: title is exact-string matched (`item.title === issueTitle`), so `[CI Failure] Deploy match preview (GitHub Pages) on main` de-dups correctly despite parentheses; body wraps the name in backticks so parens render literally. Repeated cron/main failures comment on the one open issue rather than spawning duplicates. No storm.
- Trigger/noise profile: `ci-site-v2` is PR+push — but `ci-validate`, `ci-ui`, `python-ci` are already PR-triggered watched producers, so this adds no new noise class; `ci-site-v2` is path-filtered to `site_v2/**` (narrower than existing). Fork-PR issue creation is possible but is the same already-accepted behavior, with no permission widening in this diff. `pages-match-preview` failures (prod dbt/DQ) are exactly the intended high-stakes alerts, mirroring the already-watched `dbt-scheduled`.
- Self-trigger / permissions / guard integrity: the watchdog (`ci-failure-watchdog`) is not in its own list and has a self-ignore-by-name guard; neither new producer loops back. `permissions:` (contents:read, issues:write) and the github-script are untouched. Contract carries `protected_override` quoting the CPO authorization ("do the follow-ups", 2026-07-11); #670 deferred the watch decision to the owner and the owner made it, so no §10 mechanism/product decision is left to approve. Non-blocking pre-existing gap noted: no automated test asserts watched names still match producer `name:` fields (covered here by manual verification, which passed).

## escalations
(none)
