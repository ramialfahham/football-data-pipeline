# Task contract — PROJECT_AUTOMATION_TOKEN scope audit (#413, audit F18 follow-up)

> Audit the board-sync PAT (`PROJECT_AUTOMATION_TOKEN`) and document the exact
> least-privilege scope it needs, derived from the workflow's actual operations.
> F18 ruling: the board-sync mechanism is KEPT (CPO approved 2026-06-12); this is
> the agreed security follow-up. Docs-only, non-protected — part of the CPO-granted
> autonomous non-protected backlog (2026-06-13, see escalations.log).
> See docs/working_agreement.md §2.

objective: >
  Read-only audit. Enumerate every operation `board-request-sync.yml` performs with
  PROJECT_AUTOMATION_TOKEN, derive the minimum token scope, and write that scope into
  the active doc so the CPO can rotate the secret to least privilege. Findings this
  session (verified against the workflow source + repo facts):
    - The token authenticates ALL github-script calls in board-request-sync.yml
      (the `github-token:` override replaces GITHUB_TOKEN for the whole step).
    - Operations: ProjectsV2 READ (user/org projectsV2 + fields) and ProjectsV2 WRITE
      (addProjectV2ItemById, updateProjectV2ItemFieldValue); repository Issues READ
      (repository.issue + issues.listForRepo); repository Pull requests READ
      (repository.pullRequest + pulls.list). No contents/blob reads, no writes to
      issues/PRs/contents.
    - Repo is PUBLIC and USER-owned (ramialfahham, not an org) — the org projectsV2
      path is a NOT_FOUND fallback; the board is a user-owned ProjectV2.
  Therefore least privilege is a FINE-GRAINED PAT (owner ramialfahham, this repo only):
  Projects = Read and write; Issues = Read-only; Pull requests = Read-only; Metadata =
  Read-only (mandatory). Nothing else. The classic `repo, project` currently prescribed
  in docs/project_status_sync.md is over-scoped on two counts: full `repo` (public repo
  needs no repo scope / at most public_repo) and classic `project` (account/org-wide,
  not single-project).

refs: audit F18 (#413); docs/audits/2026-06_alignment_audit.md (F18 row + ruling table).

scope_paths:
  - docs/board_request_sync.md
  - docs/project_status_sync.md
  - .claude/task/contract.md

decisions_taken: >
  Docs-only security-audit deliverable within the CPO-granted autonomous non-protected
  backlog (2026-06-13). No code/workflow change — the .github/workflows path is protected
  and needs no edit (the workflow's own `permissions:` block governs GITHUB_TOKEN, not the
  PAT; the PAT scope is set in GitHub secret settings, a CPO action outside the tree). The
  recommended scope is mechanically derived from the workflow's actual API calls, not a
  product/mechanism choice.

decisions_reserved:
  - The actual secret rotation (applying the scope, regenerating the token) is a CPO
    action in GitHub settings — outside the tree, NOT done here.
  - Keep it surgical: document the scope on the active doc + supersede the stale classic
    guidance on the paused doc. Do NOT edit the workflow, change behaviour, or re-describe
    the board mechanism. If a reviewer finds the derived scope is wrong (too narrow / too
    broad) or that an operation needs a scope not listed, STOP and correct before commit.

done_when:
  - docs/board_request_sync.md "Required secret" section states the exact least-privilege
    fine-grained PAT scope (owner + this-repo-only; Projects RW; Issues R; Pull requests R;
    Metadata R), notes the classic fallback is broader/discouraged, and explains rotation
    is a CPO settings action.
  - docs/project_status_sync.md's broad classic `repo, project` guidance is superseded by a
    pointer to the active doc's least-privilege scope (the PAT is shared).
  - no workflow / code change; markdown renders.
  - reviewers: scope-auditor (always) + cto-reviewer (voluntary — security/CI-token domain,
    not path-required since only docs/ change) — PASS.

amendments: (none)
