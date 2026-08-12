# Review — fix/61-alert-policy-apply-loop — 2026-08-12

diff_sha256: fda126a564fac6dea5a5e0379e5f0414497c6207df142993c23d81d3f8fce583

rounds: 6

rounds_cap_override: >
  THREE separate CPO grants, each recorded in `.claude/task/escalations.log` BEFORE the round
  it authorises, and each verified there by `scope-auditor`:
    · round 4 — "One more round" (AskUserQuestion, 2026-08-12)
    · round 5 — "go" (in-thread, 2026-08-12, as part of an agreed sequencing plan)
    · round 6 — "Fix both, one scoped round, then stop" (AskUserQuestion, 2026-08-12)
  WHY IT RAN LONG, stated plainly rather than excused: the RECIPE fix passed early and never
  regressed. Every round after the first failed on the TEST, and every failure was a real,
  demonstrated bypass — the guard kept reproducing, one level up, the same defect it polices
  (a literal standing in for something the file already knows). Rounds 2-5 each ended with a
  working counterexample, not a reviewer opinion. Round 6 was explicitly SCOPED by the CPO to
  closing the two round-5 findings, with the standing instruction that anything new is filed
  as its own issue rather than opening a seventh round. Nothing new was found.

<!--
Round-by-round, kept because the progression is the useful record:
  1  scope-auditor FAIL   — stale review_input.patch (previous task's diff); the generator
                            writes to stdout and takes no --base, so the file was never written.
     platform FAIL        — the guard matched only the RETIRED bash idiom; the fixed recipe is
                            Python, so every pattern was already unreachable.
  2  scope-auditor FAIL   — contract claimed a CPO ruling given "after being shown the three
                            proposed fixes". The sequence was backwards. Corrected; item 3
                            relabelled a BUILDER decision; escalations.log added to scope_paths.
     platform FAIL        — the AST check inspected only the loop's iterable and `break`. Four
                            rewrites reproduced #61 and passed: hoisted slice, `continue`,
                            generator filter, post-loop DELETE.
  3  platform FAIL        — executing the recipe against TODAY'S file cannot tell "iterates
                            everything" from "bounded at today's count". `[:3]` passed.
  4  platform FAIL        — count-independence held only on the CREATE branch; a bound inside
                            the UPDATE branch passed all ten tests.
  5  scope-auditor PASS
     platform FAIL        — every "larger" fixture used 5, so a bound of 5 hid; and no test
                            ever inspected a PATCH's URL, so a recipe aiming every update at
                            one victim resource passed everything.
  6  both PASS.
-->

## scope-auditor
VERDICT: PASS
risks_checked:
- Confirmed the cumulative patch touches exactly `contract.md`, `escalations.log`,
  `deploy/nightly/README.md` and `tests/test_alert_policy_recipe.py`, all four declared in
  `scope_paths`. No path outside it, at any round.
- Verified all three `rounds_cap_override` grants exist in `escalations.log`, each following
  the findings it answers and preceding the round it authorises. No retrospective citation.
- Verified the corrected `decisions_taken` matches what `escalations.log` records, clause by
  clause, after the round-2 FAIL: the ruling is "go ahead" given to #61 AS FILED, and item 3
  (idempotency) is labelled a BUILDER decision with its reasoning exposed, not a quoted ruling.
- Attacked the item-3 §10 classification against every decision-rights row and Appendix A3:
  it stays manual and documentary — no automation, no CI wiring, no new file — and the line
  the contract draws (script-form = CPO-class, prose-form = not) is the same line the builder's
  own reverted first attempt shows was live and enforced, not merely asserted.
- Re-checked at rounds 5 and 6 whether the growing test file crossed into the reserved "apply
  step becomes a real script" territory: it creates no new file, no new dependency and no new
  CI job; the recipe is exec'd only inside `tests/` against a stubbed API. Line not crossed.
- Checked the diff for credential-shaped content at every round: none (stub token only).

## platform-reviewer
VERDICT: PASS
risks_checked:
- Traced its own round-5 counterexample `pol["name"] = list(existing.values())[0]["name"]`
  against the new `test_every_patch_targets_the_resource_named_in_its_own_body`: with
  `_as_existing()` now assigning distinct ids, both the per-name id comparison and the
  distinct-resource check fire. Exposed at any N >= 2, not a size-4 fluke.
- Traced its own round-5 counterexample `written_count >= 5` against
  `_SIZES = [1, 2, 3, 5, 8, 17]` on both the create- and update-parametrised tests: survives
  only at exactly 5 (a conceded boundary, not a hidden one) and is caught at 8 and 17.
- Agreed with the builder's stated limit rather than letting it pass silently: a parametrised
  test proves the property only at the sizes tested; a bound of >= 18 would still pass. What
  the change buys is that a surviving bound is no longer a number anyone writes by accident,
  unlike 3 (the real count) or 5 (the suite's former single stress size, shown exploitable).
- Attempted to construct a create+update interaction bug that hides at the mixed test's fixed
  size of 5; could not produce a working counterexample not already subsumed by the
  parametrised per-branch tests, and declined to report a hypothesis as a finding.
- Checked `_as_existing`'s id extraction (`rsplit("/", 1)[1]`) is applied identically on the
  expected and actual sides, so the comparison is not accidentally tautological.
- Confirmed `import pytest` / `parametrize` add no dependency and need no requirements change;
  the file is picked up by the existing unconditional `pytest tests/` in `.gitlab-ci.yml`.
- Earlier rounds, still standing: PATCH URL construction from a real resource name; `name` set
  on the update branch and absent on the create branch; `strip()` removing `_`-prefixed keys at
  every nesting depth; `assert len(chans) == 1` failing closed; the removed Windows `curl`
  warning no longer applying anywhere in the file; `tempfile`/`chdir` restored via `finally`
  before the temp directory is deleted, on both the success and exception paths; `# noqa: S102`
  justified because the exec'd source is a fixed version-controlled repo path and `urlopen` is
  replaced rather than wrapped, so no live network path exists.

## escalations
- question: >
    The review loop hit its documented cap of 3 rounds with an open, demonstrated finding.
    Continue, ship a reduced scope, or park the branch?
  CPO ANSWER: "One more round" (AskUserQuestion, 2026-08-12) — authorising round 4.
- question: >
    Round 4 was itself an override and failed on a new defect. Continue again?
  CPO ANSWER: "go" (in-thread, 2026-08-12), given as part of an agreed sequencing plan that
    named it "one small test fix and a final review round" — authorising round 5.
- question: >
    Round 5 failed with two more findings. The recipe fix is solid and reviewed; it is the
    test that keeps failing. Fix both and run one scoped round, fix only the serious one, or
    park the branch?
  CPO ANSWER: "Fix both, one scoped round, then stop" (AskUserQuestion, 2026-08-12) —
    authorising round 6, scoped to closing the two findings, with anything new to be filed as
    its own issue rather than opening a seventh round.
