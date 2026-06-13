# Review — chore/pat-scope-audit-413 — 2026-06-13

> #413 (audit F18 follow-up): document the least-privilege scope for the board-sync PAT
> `PROJECT_AUTOMATION_TOKEN`. READ-ONLY audit, docs-only, non-protected. Within the CPO
> standing autonomous-backlog grant (escalations.log 2026-06-13, names "#413 PAT audit
> (read-only)"). Required reviewer: scope-auditor (always). cto-reviewer run VOLUNTARILY
> (security/CI-token domain; not path-required since only docs/ changed).
>
> iter-1 (hash a63695a…): both PASS, but cto-reviewer surfaced a real accuracy defect —
> the operation table attributed the `projectItems` sub-field reads to Issues/Pull-requests
> permission when on a fine-grained PAT that sub-field is governed by the Projects
> permission. Fixed (split the table row; added the account-vs-repository permission note).
> iter-2 (hash below): cto-reviewer PASS; scope-auditor FAIL on ONE point — claimed the
> markdown anchor `…f18--413` (double hyphen) was broken. That finding is FALSE: GitHub's
> github-slugger deletes `/` in place and converts the two surrounding spaces to two
> hyphens (deterministically reproduced; cto-reviewer independently verified the same).
> The diff is correct as-is — "fixing" the anchor to a single hyphen would BREAK it, so the
> diff was NOT changed. iter-3 cross-examination: scope-auditor re-ran on the unchanged
> hash, traced the algorithm itself, and confirmed PASS. Both PASS against the hash below.

diff_sha256: 6222a50b19e5aced8d9c72f0425b72a2f381e929fe8aa68334f6fcb014ef327d

## scope-auditor
VERDICT: PASS
risks_checked:
- Authorization + §10: the task is explicitly named in the recorded STANDING CPO GRANT
  (escalations.log 2026-06-13) and mandated by the F18 ruling ("KEEP + PAT-scope audit
  follow-up | #413"). The change documents the scope an EXISTING mechanism already needs
  (mechanically derived from the workflow's API calls) — no product/metric/naming/mechanism
  decision, no behaviour change. No §10.
- Scope discipline + protected paths: only the three scope_paths files changed
  (docs/board_request_sync.md, docs/project_status_sync.md, .claude/task/contract.md). The
  protected `.github/workflows/**` is NOT touched — the workflow needs no edit (PAT scope is
  a GitHub-secret setting, a CPO action outside the tree). Surgical per decisions_reserved:
  scope on the active doc, pointer superseding the stale classic guidance on the paused doc;
  the board mechanism is not re-described.
- Contested anchor (cross-examined, iter-3): traced github-slugger on
  `### Least-privilege scope (audit F18 / #413)` — lowercase → delete `(` `)` `/` `#` in place
  → spaces→hyphens (the two spaces around the deleted `/` become `--`, not collapsed) →
  `least-privilege-scope-audit-f18--413`. The pointer in project_status_sync.md targets
  exactly that anchor — it RESOLVES. The iter-2 "broken anchor" FAIL was a false-positive on
  a verifiable fact. Both docs mutually consistent; all done_when items satisfied.

## cto-reviewer
VERDICT: PASS
risks_checked:
- Scope completeness vs source: independently enumerated every PAT-authenticated call in
  board-request-sync.yml — loadUserProjects, loadOrgProjects, addProjectV2ItemById,
  updateProjectV2ItemFieldValue, repository.pullRequest+projectItems, repository.issue+
  projectItems, rest.pulls.list, rest.issues.listForRepo (core.summary uses GITHUB_STEP_SUMMARY,
  no PAT scope). Recommended Projects RW + Issues R + Pull requests R + Metadata R covers all
  exactly: nothing missing, nothing over-granted.
- projectItems attribution (iter-1 defect, now fixed): `projectItems` on a PR/issue node is
  governed by the Projects permission, not Issues/PR — the corrected table attributes it to
  Projects: read, and the new account-vs-repository note (Projects = account-wide; Issues/
  PRs/Metadata = repo-scoped) matches the actual fine-grained PAT model.
- user-owned vs org claim: verified against loadUserProjects (primary) + loadOrgProjects
  (try/catch on "Could not resolve to an Organization") — board is a user-owned ProjectV2;
  org path is the NOT_FOUND fallback. (Noted: both paths fire unconditionally — the prose
  "fallback" slightly understates the laziness, but the required scope is unaffected.)
- classic-PAT + permissions-block claims: `project` is the only classic write scope for
  ProjectsV2 (account-wide, no narrowing); `public_repo` (not full `repo`) suffices for reads
  on this public repo; the workflow-level `permissions:` block governs only the unused
  GITHUB_TOKEN, not the injected PAT. All accurate.
- No protected-path edit: diff is docs-only (docs/*.md + .claude/task/contract.md); no
  .github/workflows/** or other guard path touched.
- Markdown anchor: verified `#least-privilege-scope-audit-f18--413` resolves to the heading
  per github-slugger (double-hyphen from ` / ` is correct).

## escalations
(none — iter-1 accuracy defect (projectItems table attribution) fixed in-cycle; iter-2
scope-auditor anchor FAIL was a false-positive on a verifiable fact, refuted by deterministic
github-slugger reproduction + cto-reviewer's independent check + scope-auditor's own iter-3
re-trace. Diff unchanged between iter-2 and iter-3; both reviewers PASS against the locked hash.
The actual PAT rotation remains a CPO action in GitHub secret settings, outside the tree.)
