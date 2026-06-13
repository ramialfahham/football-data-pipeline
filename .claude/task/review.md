# Review — governance/gate-integrity-409 — 2026-06-13

> #409 (F10/F11) + #421 (F12) gate-integrity bundle. CPO gate-lift + fix picks recorded in
> escalations.log (2026-06-13): F10=(a) stop exempting contract.md; F11=(a) hash
> branch-diff-excluding-artifacts (CI recomputes); F12 demote the redundant global check.
> Protected paths under protected_override. Required reviewers: scope-auditor (always) +
> cto-reviewer (.claude/hooks/**, scripts/**, review_routing.json; opus-on-guards).
> Three cold iterations: iter-1 PASS/PASS with two cto findings (untested local==CI
> invariant; stale REVIEW_TEMPLATE caption) — addressed; iter-2 cto ESCALATE (the invariant
> test covered only adds; blob-abbrev length unpinned) — resolved by --no-abbrev on both diff
> sides + a modified-base-file end-to-end test; iter-3 both PASS against the hash below.

diff_sha256: 367bfb63b83114e8cedfc9cf0b2fc8d54fda18909ce0ef29ea756526da611708

## scope-auditor
VERDICT: PASS
risks_checked:
- Authorization + strictness (highest-stakes guard change): the CPO gate-lift and the
  F10(a)/F11(a) fix picks are recorded in .claude/task/escalations.log (2026-06-13) and the
  contract carries protected_override naming them; every change STRENGTHENS the gate
  (artifact_only_never carves contract.md out of the exempt lane; hash_exclude_paths +
  CI recompute bind the review to the PR) — nothing loosens routing, broadens artifact_only,
  or adds a bypass. Diff touches only the declared scope_paths.
- Faithfulness + hole-closure with tests: F10 (contract.md never artifact-exempt) enforced
  identically in git_discipline.py and check_task_artifacts.py; F11 binds code+contract via
  the excluded-diff hash, recomputed by CI; F12 demotes the global escalate-count to a
  commented secondary while the per-section loop stays authoritative. New tests prove the
  closed holes: contract-only commit denied (local + CI), stale review hash rejected by CI
  (#405), and the load-bearing local-==-CI invariant end-to-end over a MODIFIED base file.

## cto-reviewer
VERDICT: PASS
risks_checked:
- F11 byte-equivalence (load-bearing): all three diff sites (git_discipline _staged_diff_bytes,
  check_task_artifacts recompute, test branch_hash) use identical `--no-renames --no-abbrev`
  + the same `:(exclude)` pathspec. For identical content the local staged diff and the CI
  `base...HEAD` recompute are byte-identical across all shapes — new file, MODIFIED
  base-resident file (base blob == HEAD-side old blob; --no-abbrev removes abbreviation-length
  divergence; --no-renames removes rename-detection divergence), and excluded bookkeeping.
  The invariant is UNCONDITIONAL for the supported single-substantive-commit flow and
  test-locked end-to-end by test_local_staged_hash_equals_ci_recompute (add + modify +
  excluded together). Residual vectors (split/amended commits, diverged base) all fail CLOSED.
- F10 dual-gate consistency + F12 + fail-mode/scope: contract.md is in artifact_only_never in
  BOTH gates and deliberately NOT in hash_exclude_paths (so it is hashed); other bookkeeping
  stays exempt+excluded — locked by three tests. F12 keeps the global check as a commented
  SECONDARY backstop with the per-section loop AUTHORITATIVE (no weakening). Fail polarity is
  correct: local gate fails OPEN (try/except → no self-lockout; _hash_exclude_pathspec(None)
  safe), CI fails CLOSED (check=True + non-zero on error). Only declared scope_paths;
  protected_override present; no allowlist/sole-command/escalation logic weakened.

## escalations
(none — iter-2 cto ESCALATE on the invariant's test coverage + unpinned abbreviation was
resolved by hardening (--no-abbrev on both diff sides; the end-to-end test now modifies a
base-resident file), not escalated to the CPO — it was a fixable robustness gap, not a
CPO-class decision. Both reviewers PASS in iter-3. The same-PR self-binding is verified
post-commit by running check_task_artifacts against the PR's own diff.)
