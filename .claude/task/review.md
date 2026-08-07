# Review — fix/25-review-exclude-trailer — 2026-08-07

diff_sha256: 5c8797fddf0035ee0a883a8bd843744ca669b22e30dfc35523196ad0e2e97313

rounds: 3

> HASH REBOUND after rebasing onto `main` at `177df80`, which is !18 (#29) merged. NOT a fourth
> round, and the distinction matters: the REVIEWED CONTENT is unchanged. !18 and this branch touch
> disjoint code — `.githooks/post-commit` + `tests/test_post_commit_hook.py` there,
> `.claude/hooks/git_discipline.py` + `tests/test_governance_hooks.py` here — and the conflict was
> only that both rewrote the same three per-task artifacts (`contract.md`, `review.md`,
> `review_input.patch`), which are per-task by design. Resolved by taking this task's versions;
> !18's are spent and already merged.
>
> The hash moved because `contract.md`'s BASE side changed, not its content: `main` now carries
> !18's contract, so the same final text produces a different diff. The number above is not
> `--staged-hash` on an increment, which is the documented second-commit trap. The branch was
> collapsed with `git reset --soft` to a single staged set, so the local hash and CI's
> `git diff base...HEAD` recompute are the same computation over the same bytes. Confirmed both
> ways: `check_task_artifacts.py` recomputed `5c8797fd…` before the rebind, and `--staged-hash`
> printed the identical value after the collapse.

## scope-auditor
VERDICT: PASS
risks_checked:
- Round 1 FAILed: the `impact_map`'s "what imports it" claimed *"Nothing else in the tree imports
  the module"* while `tests/test_governance_hooks.py` imports it at `:438` and `:2798`. Re-ran
  `grep -rln "import git_discipline" --include="*.py"` in round 2 and it returns exactly the two
  files the corrected field now names. Closed.
- Cross-checked the corrected field's list of 12 reference-only files against an independent
  tree-wide grep (15 files, minus 2 importers, minus the self-referential `review_input.patch`) —
  exact match, no omissions or padding.
- Confirmed the false text was NOT also in `escalations.log`, narrowing its own round-1 finding,
  which had named both files.
- Round 3: counted the five new tests in the diff by name and matched each against the corrected
  `done_when` per-test red/green claim. Both exemptions are structurally true, not asserted —
  `test_no_trailer_when_no_excluded_path_changed` asserts ABSENCE so it is green either side of
  the fix, and `test_excluded_trailer_failure_is_loud_not_silent` calls a function that does not
  exist in the unfixed tree.
- Traced the tightened fail-loud assertion against `_staged_stat`'s exact f-string: the trailer's
  `why` contains the bare word "trailer" but never the phrase `review patch trailer`, so the
  assertion is pinned to the structural token and would go red if `section` were emptied.
- Diffed `scope_paths` (six entries), `protected_override` and the `escalations.log` entry against
  round 2 — byte-identical. `amendments:` still `(none)`. No authority widened, no file touched
  outside `scope_paths`.
- Judged that recording the second #904-class drift in `done_when` is additive bookkeeping in a
  file already in scope, following this contract's own round-2 precedent of recording rather than
  silently rewording, not scope creep.
- ⚠ SURFACED, NOT ACTED ON, and carried here rather than dropped: the module-level comment above
  the new test block still reads "THREE of the four go red" and does not mention the fifth test
  added in round 2. Not false about the four it describes, and unchanged region text under
  delta-review discipline, so it was not raised as a finding. See "Owed" below.
- No Bash access in this session, so `652 passed, 1 skipped` is taken as reported and
  cross-checked only against the test names and behaviour visible in the diff.

## cto-reviewer
VERDICT: PASS
risks_checked:
- `protected_override` present and its cited authority real: read the `escalations.log` entry
  `## 2026-08-07 fix/25-review-exclude-trailer` on disk. It exists, is not a forward reference,
  and its bounds match the contract word for word. `.claude/hooks/` is genuinely in
  `PROTECTED_PREFIXES` (`task_contract_gate.py:66`). Naming the protected file literally rather
  than pointing at `scope_paths` is the safer form given open #18.
- The NEW MECHANISM reclassification is correct, and would have been raised had the builder not
  raised it: `_excluded_trailer` is structurally the same emitter, in the same file, with the same
  reach as the one that made `review_summarise_paths` a new mechanism at `escalations.log:1117`.
- Approval adequacy checked independently, because `:1108` bars a reviewer from converting a
  declaration into an approval. `.claude/active_work.md:35` — main's content, not edited by this
  branch — already records #25's fix as *"the MANIFEST the other exclusion list has"*, so "start
  #25" instructed this mechanism rather than being retrofitted to it. That is the exact gap that
  sank the 2026-08-06 precedent.
- Hash separation verified rather than accepted: `--staged-hash` returns through
  `_staged_diff_bytes` / `_hash_exclude_pathspec`; `--review-patch` is a separate branch through
  `_review_patch_bytes`. No call path connects them.
- Guard direction: the CLI fails CLOSED, the PreToolUse hook path cannot reach the new code
  (`_review_patch_bytes` has one caller), so the hook's fail-open invariant is untouched.
- The `_staged_stat` extraction stays inside the granted override: same protected file,
  behaviour-preserving, and load-bearing rather than cosmetic — the manifest's reason string was
  reworded in the same round, and without the structural `section` token that rewording would have
  silently unpinned `test_manifest_failure_is_loud_not_silent`.
- RECURRING COST tested against the live trap: `.gitlab-ci.yml`'s `data_paths` contains neither
  `.claude/**` nor `tests/**`, so merging fires no `data:build:main`. One extra pytest case in an
  already-running job is not a crossing.
- Round 3: verified all five test names exist verbatim and that stating the claim per test rather
  than as one number is what makes it falsifiable by grep.
- ⚠ OWN MISS, RECORDED: the false `impact_map` should have been caught here as well as by the
  scope auditor, and was reachable from evidence already produced in round 1. Rule adopted for
  protected-path reviews: every falsifiable sentence in an `impact_map` gets one command run
  against it. Round 3 extended it — `done_when` is authority too, and routing a drifted claim in
  it to another reviewer was the wrong call.

## platform-reviewer
VERDICT: PASS
risks_checked:
- Round 1 FAILed on a name collision: the new `_review_patch` helper shadowed the module-level
  `_review_patch(repo) -> str` at `:2495`, so four pre-existing tests received a
  `CompletedProcess` where they expected a string and errored. Those four pin that exclusion still
  hides paperwork, that `escalations.log` still reaches reviewers, that the patch is cumulative,
  and that code plus `contract.md` still reach reviewers. Confirmed closed in round 2 by
  enumerating all 129 module-level `def`s and checking for repeats: `_review_patch` appears once.
  The five new test names and the two new helpers are unique.
- Round 1 FAILed second on the trailer's fail-loud path having no test, so a
  `try/except: return b""` would leave the suite green while re-creating #25's ambiguity. Closed
  by `test_excluded_trailer_failure_is_loud_not_silent`, which drives the real branch via
  malformed pathspec magic rather than inspecting source — the failure mode its sibling carries a
  scar from.
- Refactor equivalence checked argument by argument: the git argv is byte-identical, the
  empty-list short-circuit still skips `_base_commit`, and the RuntimeError still carries the path
  list, exit code, caller reason and the under-reporting tail.
- Round 3: the tightened assertion genuinely bites. With `section` emptied the message reads
  `review patch  failed for …` and goes red, which the bare-word form could not do. The phrase
  appears nowhere in the `why` prose or in `paths`, so it has exactly one source.
- Keyword binding at both call sites forecloses the positional-swap class; `_staged_stat` has no
  positional-only marker, both names are legal keywords, and the `why` strings are byte-identical
  to round 2 so the manifest pin cleared earlier is intact.
- Trailer correctness: bytes/str boundary clean, encoded once; every stat line is prefixed `#   `
  so a hostile filename cannot inject a fake diff header; git quoting escapes control characters
  before `splitlines()`; all current `review_exclude_paths` entries are literal paths, so
  `-- <path>` and `:(exclude)<path>` select the same files.
- Cumulative semantics: `git diff --staged <base> -- <paths>` is base-to-index, so a handover
  edited in an earlier commit on the branch is still named — the case that produced occurrence 3.
- Dependencies, credentials, permissions, build and hosting: nothing in the diff.

## escalations
(none)

## Owed, carried forward rather than dropped
- The module-level comment above the new test block says "THREE of the four go red" and predates
  the fifth test added in round 2. It is incomplete rather than false, no reviewer raised it as a
  finding, and correcting it would move the hash and require a FOURTH round, which is past the cap
  and therefore the CPO's call. Surfaced to him with the MR rather than fixed silently.
