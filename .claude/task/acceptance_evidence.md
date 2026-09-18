# Acceptance evidence — GitHub is a read-only mirror of `main`: the docs sweep

Every item run on the staged tree of `docs/github-mirror`, exit codes read bare.

criteria_demonstrated:
  - THE SWEEP IS CLEAN. `grep -rn -i "suspended\|access returns\|account access\|gh\` is dead\|dormant"
    CLAUDE.md README.md .github .claude/skills scripts tests` → the only hits are historical
    sentences in `.github/workflows/README.md` (line 13: the 2026-08 migration happened "after the
    GitHub account was suspended"; line 45: `pages-match-preview.yml` "was dormant-by-decision
    before it was dormant-by-platform") and the compiled `__pycache__` files. No live-state line
    remains that calls GitHub dead, suspended, dormant or "decided when access returns".
  - CLAUDE.MD SAYS THE NEW STATE. Line 9: use `glab`, never `gh`; GitHub is a read-only mirror of
    `main`. Line 259 bullet: "GitHub is a READ-ONLY MIRROR of `main`", GitLab pushes `main` only,
    the token lives in GitLab's mirror settings and only the CPO handles it, Actions disabled at
    the repository level, `.github/workflows/` unedited. Line 285: GitHub Pages gone, the mirror
    hosts nothing. Line 193: `origin` is the mirror, lagging by a cycle.
  - THE WORKFLOWS README SAYS THE SAME AND KEEPS ITS WARNINGS. Header "DISABLED"; the "Why" names
    the 2026-09-18 ruling; the re-arm section is now "Why Actions must STAY disabled" and keeps the
    seven push-triggered workflows, the two crons, the three prod writers table, the concurrency
    paragraph and the "Do not" list unchanged.
  - README CARRIES NO GITHUB ACTIONS BADGE. `grep -n "actions/workflows" README.md` → no hits; the
    CI bullet reads "CI/CD on GitLab (`.gitlab-ci.yml`) ... GitHub carries a read-only mirror of
    `main`"; the sqlfluff line names `validate:governance`.
  - NO WORKFLOW YML CHANGED. `git diff --stat gitlab/main -- .github/workflows/*.yml
    .github/workflows/_paused` → empty output.
  - TESTS GREEN. `python -m pytest tests/test_governance_hooks.py -q -k "default_base or
    governance_base"` → `4 passed, 302 deselected`; the seven test files that read the edited
    docs (`test_governance_doc_parity`, `test_no_dead_issue_refs`, `test_no_host_fingerprint_in_tree`,
    `test_nightly_entrypoint_parity`, `test_materialisation_policy`, `test_alert_policy_recipe`,
    `test_tracker_snapshot`) → `156 passed, 1 skipped`. `python scripts/check_task_artifacts.py`
    → `empty diff · OK`. `grep -rn dormant_origin` over `*.py *.md *.yml` → no hits (the renamed
    test has no other reference).
  - THE MIRROR ITSELF, VERIFIED FROM HERE BEFORE THE EDITS. `git ls-remote origin refs/heads/main`
    → `16db22bf…`, equal to `gitlab/main`; the GitLab remote-mirrors API → `update_status:
    finished`, `last_error: null`, `only_protected_branches: true`; GitHub shows no Actions tab
    (Actions disabled) and no run after the sync.
