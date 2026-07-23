# Review — chore/review-economics — 2026-07-22

> Required reviewers per `.claude/review_routing.json`: `scope-auditor` (always) + `cto-reviewer`
> (`.claude/hooks/**`, `.claude/agents/**`, `tests/**`, `scripts/**`). Opus floor APPLIES: guard
> paths are touched, so every cto round ran at opus.
>
> **WHAT THIS CHANGES.** It cuts the review friction that the CPO named after #806: the process "has
> to be more economic. otherwise we will not build the website in time." Three enforced mechanisms,
> in the files that describe the review process: (1) DELTA RE-REVIEW in all six briefs — after round
> one a reviewer sees only what changed since its own PASS and refuses when that delta is too large;
> (2) a ROUND CAP of 3 in the commit gate and the CI backstop, past which the builder stops and
> brings findings to the CPO unless `rounds_cap_override:` records the CPO saying continue; (3) a
> `consulted:` contract field on the structural surface, so domain findings surface before the build
> rather than in review round three. Two docs and both templates were swept to agree.
>
> **THE ROUNDS, and this task ate its own dogfood.** Three rounds, and the change was in force on
> itself by round two.
> Round 1: scope-auditor PASS. cto-reviewer FAIL at opus with four findings, all correct and all the
> same root cause — the CI backstop RE-IMPLEMENTED the round-cap and nullish/structural logic with
> hand-copied constants instead of importing the hooks', and the copies had already diverged: the CI
> override check accepted `tbd`/`none` the local gate rejects (F1), the CI nullish set omitted
> `(none)` (F2), an empty `rounds_cap_override:` absorbed the following `## header` as its reason in
> BOTH gates (F3), and a comment claimed a lockstep test that did not exist while the export regex had
> already drifted (F4). That is the exact "the twin didn't get the fix" class this repo keeps being
> bitten by, committed by me inside the change meant to reduce it.
> Round 2 (delta): the fix was the CLASS, not the four instances. The CI backstop now imports
> `git_discipline` and `task_contract_gate` and delegates — its `_rounds_error` is one line calling
> `_gd._rounds_gate`, structural and consulted checks call the edit gate's own functions, and the
> hand-copied constants are deleted, so no copy remains to drift. The newline-absorption bug was
> fixed at its single source (`[^\S\n]*`). A parity test asserts the one remaining nullish pair is
> identical and would fail on re-divergence. Both reviewers PASS. The cto noted, non-blocking, that
> the shell-write path enforced impact_map but not consulted.
> Round 3 (delta): closed that asymmetry — the shell path now enforces the identical pair the Edit
> path does. Both reviewers PASS on the one-line delta.
>
> **THE PATTERN, said plainly because it is the whole reason this task exists.** The friction the CPO
> felt was not one bad process. Across today it was me: three §10 misclassifications, two guards
> weakened to make my own change pass, and every re-review run at full depth because scoping to the
> delta was never a rule. This change makes the delta a rule, bounds the loop, and pushes domain
> knowledge before the build. It cannot stop me making the mistakes, but it makes each round cheaper
> and each loop shorter, which is what the CPO asked for. The rest of the owed economics item —
> reviewer model in the routing file, reviewers as peers — is explicitly NOT done here and stays owed.
>
> **VERIFIED BY EXECUTION.** The full governance suite is 244 passing, up from 215 at the start of the
> branch: the new tests drive the REAL hooks as subprocesses, exercise the deny and allow direction of
> each rule plus the placeholder and nullish rejections, prove the empty-override and word-placeholder
> holes are closed, and assert the six briefs are byte-identical and the CI backstop reuses the
> canonical logic. Layer contract passes; both schema-free doc and template edits are plain markdown.
>
> **NOT VERIFIED.** No dbt, no warehouse: this change touches none. `pytest tests/` runs in
> `python-ci.yml` on every PR with no path filter, so CI re-runs the same suite closed.

diff_sha256: 15b2508a5407f61b1ef0a942f841536bba5eed55e19493145ec00d697a47bb18
rounds: 3

## scope-auditor
VERDICT: PASS
risks_checked:
- Authority and §10. Confirmed the escalations.log entry records a discrete CPO AskUserQuestion ruling "Delta re-review, round cap, consult first", that the change is squarely inside it, and that `protected_override` is present and quotes it. Judged the round-2 and round-3 fixes to take no new decision: both are internal refactors reaching the same verdict, and the shell-path change applies the already-approved consulted rule to a second write path.
- Scope across all three rounds: every touched file inside `scope_paths`, no new path added, each amendment absent because none was needed (no scope widened, no claim became false).
- The contract's own new field: it carries a real `consulted:` ("nobody, because platform-only, its reviewer is the same cto that reviews the build"), which is honest for a platform-and-governance change rather than a dodge.
- Doc-sync: both `working_agreement.md` and `agent_guardrails.md` are updated to describe the delta review, the round cap and the consulted field, so no doc describes a superseded process.

## cto-reviewer
VERDICT: PASS
risks_checked:
- The CI-import fix at root cause: confirmed the backstop calls the hooks' own functions and holds no surviving copy of the deleted constants (grepped `STRUCTURAL_PREFIXES`, `EXPORT_RE`, `_real_field`, a local `_NULLISH` — none remain), so the F1/F2/F4 divergences cannot recur.
- Fail-closed direction: the CI module-level `import git_discipline`/`task_contract_gate` raise before `main()` on failure, exiting non-zero, which the workflow treats as a job failure — correct for a backstop — while the local commit gate still fails open via its own try/except. Both polarities correct.
- F3 regex: `[^\S\n]*` is horizontal-whitespace-only and `(.+)$` without DOTALL cannot cross a newline, so an empty `rounds_cap_override:` yields no capture and denies, while a same-line `rounds: 3` and a real override still capture; robust on CRLF because the trailing `\r` is stripped.
- The parity test genuinely fails on re-divergence, not merely passes now: traced its assertions, including `set(gd._NULLISH_WORDS) == set(tcg._NULLISH)` and the `tbd`/`(none)` override rejections and the structural/protected classifications.
- Round 3, the shell-path symmetry: the new `consulted` check sits after the scope, protected and impact_map checks in `_gate_bash_pre`, mirroring the Edit path, so both write paths now enforce the identical pair on the structural surface; its test drives a real bash redirect and fails without the added line.

## escalations
- question: How far to cut the review friction before the team page? Four paths offered: delta re-review + round cap + consult first; mechanical only; the full recast; or nothing. Recommended the first, because it attacks both round count and round cost and pays back on the next page, where mechanical-only leaves round count untouched.
  CPO ANSWER: "Delta re-review, round cap, consult first" (AskUserQuestion, 2026-07-22). Full record is the entry for this branch in `.claude/task/escalations.log`.
