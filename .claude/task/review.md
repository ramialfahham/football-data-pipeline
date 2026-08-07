# Review — fix/29-post-commit-mr-state — 2026-08-07

diff_sha256: 77505807b41b8277dd9e14fbe001eaa31f4c788a1266e062603186e4fb67d679

rounds: 1

## scope-auditor
VERDICT: PASS
risks_checked:
- Scope: diffed file list (`.claude/task/contract.md`, `.githooks/post-commit`,
  `tests/test_post_commit_hook.py`) against `scope_paths` in contract.md. Exact match, nothing
  touched outside it.
- `protected_override` necessity: read `PROTECTED_PREFIXES`/`PROTECTED_FILES` in
  `.claude/hooks/task_contract_gate.py:66-78` directly rather than accepting the contract's claim.
  `.githooks/` is absent. No override needed.
- `decisions_reserved` on `.githooks/**` joining the PROTECTED set: confirmed the diff makes zero
  edits to `task_contract_gate.py` or any protected-set definition, so the §10 question is
  genuinely left open rather than decided in code under cover of the hook fix.
- The "first test in this suite to shell out to bash" claim, which the NEW MECHANISM declaration
  rests on: traced `run_hook()` in `tests/test_governance_hooks.py:73-80` (it invokes
  `sys.executable`, not bash; its `bash_event()` helper only builds a JSON event payload and never
  shells out) and grepped all of `tests/` for any bash subprocess invocation. Only the new file
  does it. The claim is true and the classification is declared, not smuggled.
- Threshold declarations against the actual diff: the call structure is a like-for-like swap
  (`mr view` to `mr list`), same one-lookup-plus-conditional-create shape. No new external
  surface, no schedule, no service, so NEW MECHANISM and RECURRING COST read correctly as NO.
- The guard-invariant claim that every failure path now falls to CREATE: read the final hook
  logic and confirmed no input returns a false "already open".

## platform-reviewer
VERDICT: PASS
risks_checked:
- Fail-open trace across all four paths of the new conditional (`.githooks/post-commit:26-36`):
  success with a URL prints "already open"; success with empty output falls through and opens;
  a non-zero exit short-circuits `[ $LIST_EXIT -eq 0 ]` regardless of `$MR_URL` content and opens;
  `glab` missing from PATH gives exit 127 and opens. Every failure mode routes to CREATE, never to
  a false "already open". Matches the contract's claim.
- Shell correctness: `LIST_EXIT=$?` is read immediately after the `MR_URL=$(...)` assignment, the
  same idiom the old code used; `"$BRANCH"` is quoted; `// empty` is a correct jq null-coalesce for
  the array-may-be-empty case. No defect found.
- Regression validity of `test_merged_mr_is_not_treated_as_open`: manually traced BOTH hooks
  against the `merged_only` stub payload. The old hook calls `mr view`, gets exit 0 and a non-empty
  URL, prints "already open" and never calls create, so the assertion goes red. A real
  discriminator, not decoration. The other four scenarios trace as already-correct under both old
  and new code and are non-regressing coverage, which is what the file's docstring claims.
- CRLF on `.githooks/post-commit`: 36 CRLF-terminated lines in the working tree, but zero `\r` in
  the git-diff output covering the identical hunk, and `.git/config` has `autocrlf = true` with no
  `.gitattributes`. The committed blob is LF-only and the CRLF is local Windows checkout noise.
  CI's `test:python` runs `image: python:3.11` (Linux, no autocrlf) and executes the LF blob.
- The bash skip is not a hole: CI's `test:python` uses the full `python:3.11` Debian image, not
  `-slim` or `-alpine`, so `/bin/bash` is present, `shutil.which("bash")` resolves and the skip
  never fires in the pipeline that matters.
- Duplicated enforcement: grepped the repo for `glab mr` / `mr view` / `mr list` / `post-commit`
  outside the three changed files. `.claude/hooks/git_discipline.py` and `git_workflow.py` carry
  MR text only as human-facing reminder strings; neither executes an is-this-MR-open predicate.
  No second implementation exists in `.gitlab-ci.yml` or `scripts/` to fall out of sync.
- Dependency hygiene, credentials, build health and hosting: not applicable. No
  `*requirements*.txt` or `package*.json` change, no credential pattern (the `OPEN_URL` constant is
  a non-secret GitLab URL used only as a fixture), no site/build/CI-config surface touched.
- Coverage gaps, noted and not fail-worthy: the stub does not assert that the hook passes
  `--source-branch "$BRANCH"`, which is deliberate per the docstring (it tests the MR-state
  OUTCOME, not which CLI call produced it). The pre-existing `git push` failure path
  (`PUSH_EXIT -ne 0`) remains untested, but it is untouched by this diff.

## escalations
(none)
