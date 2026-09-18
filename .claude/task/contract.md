# Task contract — GitHub is a read-only mirror of `main`: replace every "dead / suspended / dormant, decided when access returns" line

objective: >
  The GitHub account is back and the CPO ruled (chat, 2026-09-18): GitLab stays the system of
  record (CI, MRs, WIF); GitHub is a read-only push mirror of `main`, pushed from GitLab (set up
  2026-09-18, `Mirror only protected branches`, first sync `16db22bf`); GitHub Actions stay
  disabled (repository setting, confirmed before the first sync). Every line in the tree that
  still says GitHub is dead, suspended, dormant, or "decided when access returns" is replaced
  with that state; the two dead GitHub Actions badges in `README.md` go and its CI line names
  GitLab. Prose and comments only: no workflow is edited or re-enabled, no hook is edited, no
  behaviour changes.

refs: >
  CPO ruling in chat, 2026-09-18 ("GitLab stays the system of record (CI, MRs, WIF); GitHub
  becomes a read-only mirror of `main` pushed from GitLab; GitHub Actions stay off ... one docs
  MR that replaces every 'GitHub is dead / account suspended / dormant, decided when access
  returns' line with the new state — `CLAUDE.md` ... and `.github/workflows/README.md` — and
  says the mirror is read-only and Actions are off. Do not re-enable any workflow."); README
  badges added on his "go, yes fix the readme badges too" (2026-09-18). The sweep that found
  the other spots: `grep -rn -i "suspended\|dormant\|account access\|access returns"`.

scope_paths:
  - CLAUDE.md
  - README.md
  - .github/workflows/README.md
  - .github/ISSUE_TEMPLATE/config.yml
  - .claude/skills/onboard-competition/SKILL.md
  - .claude/skills/validate-local/SKILL.md
  - scripts/check_task_artifacts.py
  - tests/test_governance_hooks.py
  - .claude/task/contract.md
  - .claude/task/review.md
  - .claude/task/review_input.patch
  - .claude/task/acceptance_evidence.md

protected_override: >
  `.github/workflows/README.md` is under a protected path. The CPO named it in the same ruling,
  2026-09-18, in chat: "one docs MR that replaces every ... line with the new state — `CLAUDE.md`
  (the `gh` line, the 'GitHub is RETAINED but DORMANT' bullet, the GitHub Pages line) and
  `.github/workflows/README.md` — and says the mirror is read-only and Actions are off. Do not
  re-enable any workflow." Only the README in that directory changes; every `.yml` there stays
  byte-identical. The MR head declares the locked file; his merge is the approval.

impact_map: >
  writers: none — `.github/workflows/README.md` is prose read by people; no workflow, hook,
    script or test parses it (`grep -rn "workflows/README" --include=*.py --include=*.yml .`
    → only `CLAUDE.md` links to it).
  downstream: none — GitHub Actions are disabled at the repository level, so no file in
    `.github/workflows/` can fire; the mirror pushes `main` and nothing runs on arrival
    (verified: no Actions tab, no run, after the first sync of `16db22bf`).
  layer_rules: n/a — no dbt path in scope.
  deploy_order: none — no warehouse, site or CI job changes; the mirror carries the merged
    `main` to GitHub on its own within its cycle.
  blast_radius: `scripts/check_task_artifacts.py` and `tests/test_governance_hooks.py` change
    docstring/comment text and one test's name and assertion messages; `default_base()` logic is
    untouched and `python -m pytest tests/test_governance_hooks.py -q -k default_base` stays green.
    The two hook comments that also say "dormant" (`.claude/hooks/git_discipline.py:446`,
    `.claude/hooks/comment_history_gate.py:39`) are deliberately NOT in scope: a comment-only edit
    is not worth widening the protected surface; they are named in the MR head.

decisions_taken: >
  One historical sentence is kept as written: `.github/workflows/README.md` "Why" opens with "The
  project migrated from GitHub to GitLab in 2026-08, after the GitHub account was suspended" — it
  says why the migration happened, not what GitHub is now, and rewording a true past fact to dodge
  a grep would be the wrong fix. The README's two dead GitHub Actions badges are removed with no
  GitLab badge in their place:
  the GitLab pipeline badge returns 404 to an anonymous viewer because the project's pipelines are
  not public (`public_jobs: false`), and making job logs public is a separate settings decision
  for the CPO. Everything else is a rewording of a known fact to the ruled state.

decisions_reserved:
  - Whether to make GitLab pipelines public so a CI badge can show on the mirror (`public_jobs`) — CPO, settings surface.
  - Whether to delete the ~70 pre-migration branches still on GitHub — CPO; the mirror neither writes nor deletes them.
  - `docs/operations_guide.md` §"GitHub Actions" and `docs/development_workflow.md:62` still describe GitHub Actions as live CI (stale since 2026-08, before this ruling); a rewrite of the operations runbook, not a line swap — out of scope, named in the MR head.

done_when:
  - `grep -rn -i "suspended\|access returns\|account access\|gh\` is dead" CLAUDE.md README.md .github .claude/skills scripts tests --include=*.md --include=*.py --include=*.yml` returns exactly one hit, the historical sentence at `.github/workflows/README.md` "Why" named in `decisions_taken`; every other hit in the sweep described a current state and is gone.
  - `CLAUDE.md` says GitHub is a read-only mirror of `main` pushed from GitLab, Actions off, `glab` for everything; `.github/workflows/README.md` says the same and keeps every "do not" and the prod-write warning.
  - `README.md` carries no badge pointing at github.com/…/actions and its CI bullet names GitLab CI.
  - `git diff --stat gitlab/main -- .github/workflows/*.yml .github/workflows/_paused` is empty.
  - `python -m pytest tests/test_governance_hooks.py -q` green; `python scripts/check_task_artifacts.py` green.

amendments: (none)
