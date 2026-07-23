# Review — chore/trim-guardrails — 2026-07-22

> Required reviewers per `.claude/review_routing.json`: `scope-auditor` (always) + `cto-reviewer`
> (`.claude/hooks/**`, `.claude/settings.json`, `tests/**`, `scripts/**`). Opus floor APPLIES: guard
> paths are touched.
>
> **WHAT THIS CHANGES.** A staff-level AI-engineering review of the `.claude/` machinery found its
> core strong (the hash-bound blinded review, the self-gating hooks) but three parts over-scoped,
> "the machinery defending itself against itself". The CPO ruled (AskUserQuestion): "Trim the weak
> parts, then reframe." This is the trim, four reductive cuts:
> 1. DELETE `plain_language_gate.py` and its Stop wiring. A 232-line hook that blocked the agent's
>    own chat message on an em dash; its author had already flagged it disposable. The CPO's
>    no-em-dash PREFERENCE survives as a norm in the handover and `working_agreement.md`; only the
>    machine gate goes.
> 2. DEMOTE the `consulted:` field shipped one day ago in #807. Remove its enforcement from the
>    contract gate (parse + three deny sites) and the CI backstop; keep the intent as a norm. A
>    considered PARTIAL REVERSAL of #807, on the review's recommendation, logged in `escalations.log`.
> 3. COMPRESS the multi-round "forgery archaeology" comments in `task_contract_gate.py`; keep the
>    `_BLOCK_HEADER_RE` pattern that closed the class.
> 4. SPEED the test suite from ~11 min to ~4: the `repo` fixture builds a git repo once and copies it
>    per test instead of six subprocesses each.
>
> KEPT, and this is the point of the trim rather than a teardown: the hash-bound review, the
> contract/scope gate, the impact_map gate, the layer gate, the round cap, the blinded reviewer cast,
> and the fail-open discipline.
>
> **HONESTY ABOUT #807.** Demoting `consulted:` undoes part of a change I built and the CPO approved
> earlier the same day. That is recorded plainly in the contract's `decisions_taken (3)` and in
> `escalations.log` as a considered reversal on the expert review's recommendation, not thrash. The
> banked lesson: a guard that cannot pass its own proportionality test should not ship, even one I
> built hours ago.
>
> **VERIFIED BY EXECUTION.** Full suite 215 passing (244 minus exactly the 29 removed cases: 11
> consulted, 13 plain-language, 5 fail-open params that named the deleted hook), in ~4 minutes down
> from ~11. Layer contract passes; `settings.json` is valid JSON; the CI backstop imports and runs.
> The removal was swept repo-wide: zero executable or config references to `plain_language` or a
> `consulted:` machine-field remain, only the intended prose norms.
>
> **NOT VERIFIED.** No dbt, no warehouse. `pytest tests/` runs in `python-ci.yml` on every PR, so CI
> re-runs the same suite closed.

diff_sha256: 37583d5be059b6301362b84a6747e8b78eaf83acd14cf9062ca7363b2c0a843d
rounds: 1

## scope-auditor
VERDICT: PASS
risks_checked:
- Authority and §10 honesty. Confirmed the `escalations.log` entry records a discrete CPO AskUserQuestion ruling "Trim the weak parts, then reframe" covering all four cuts, that `protected_override` quotes it, that the no-em-dash preference is explicitly retained as a norm rather than silently dropped, and that the partial reversal of #807 is recorded honestly in both the contract and the log rather than slipped in.
- Only-authorized-cuts. Verified nothing beyond the four named items was removed: the impact_map gate and every Edit/shell check remain, the round-cap parity test is retained, and the test-count drop is fully explained by the removed consulted and plain-language tests rather than by dropping coverage of a kept gate.
- Scope: every touched file inside `scope_paths`, no new path, and the contract itself carries a real `consulted:` norm-note rather than the deleted field.

## cto-reviewer
VERDICT: PASS
risks_checked:
- The half-removed-gate failure mode, swept repo-wide: `consulted|plain_language` returns zero matches across every `.py`/`.yml`/`.json`, and the machine identifiers appear only in the patch and the contract's own description. The parser-removed-but-deny-sites-left brick state does not exist; parser and all three deny sites are gone together.
- The impact_map gate intact on both write paths: still parsed, still denied-on-absence on the Edit protected branch, the Edit structural branch and the shell path, with the allow-context message corrected to "impact_map present"; traced the parser against the real contract's leftover consulted norm-block and confirmed impact_map_present still computes True.
- `stop_gate.py` still fires and is independent: it imports only surviving helpers from `task_contract_gate`, has no reference to the deleted hook, and its Stop wiring is preserved as valid JSON with no trailing comma.
- CI/local parity: the now-unused `import task_contract_gate` and the `_structural`/`_consulted_present` helpers are removed cleanly, the round cap still delegates to `git_discipline._rounds_gate`, and the parity test dropped exactly the assertions that would now crash while keeping the rest.
- Fixture isolation: `_repo_template` is only ever the copytree source, every test mutates its own copy's `.git`, author identity is set before the copy, and the copied `.git` is relocatable; test-count arithmetic (244 − 29 = 215) checks out.
- Fail-direction, cost and secrets: hooks still fail open, CI fails closed, the change is cost-reducing, no dependency or permission change, `shutil` is stdlib.

## escalations
- question: How far to trim the guardrail machinery before reframing the README around it? Three paths offered: trim the weak parts then reframe; cut only the plain-language gate and speed the suite; or reframe only. Recommended trimming the weak parts, because the review's strongest framing depends on the machinery being defensible.
  CPO ANSWER: "Trim the weak parts, then reframe" (AskUserQuestion, 2026-07-22), the option whose text named all four cuts. Full record, including the staff review that motivated it, is the entry for this branch in `.claude/task/escalations.log`.
