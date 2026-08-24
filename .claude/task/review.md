# Review — feat/82-metric-docs-blocks-generated — 2026-08-24

diff_sha256: abad7ac7431e19ac65127b01ff5872c5f6f076cbc161ff6a6aaaf087a650519f

rounds: 4

rounds_cap_override: CPO, 2026-08-24: "round 3 found a real test gap, fixed in round 4; not looped on disagreement". scope-auditor ESCALATED rather than ruling, correctly — the override is the CPO's by construction and no reviewer can grant or waive it. It also rejected my own reading (that a found-and-fixed round should not count) as unsupported by the rule text, which says "capped at 3" with no qualifier and is enforced numerically by the gate. I had flagged that my reading was convenient for me; it was, and the CPO's line is recorded instead of an unwritten exception.

⚠ ALL FOUR REVIEWERS FAILED ROUND 1, on four different defects. CI then found a fifth that no
reviewer could have, and platform-reviewer found a sixth in round 3. I found none of them. The
count is the finding, and it is recorded in `escalations.log` rather than softened here.

## football-analytics-expert-reviewer
VERDICT: PASS (round 3)
risks_checked:
- ROUND 1 FAIL: `finishing_efficiency` (team) still said "window" three times after the sweep. The
  guard enumerated three phrasings and the `done_when` verified with THAT SAME PATTERN, so the
  check could only ever agree with the guard. Established why it mattered: the block is wired to a
  season-cumulative model as well as a form-window one.
- Re-read the reworded row against the four things it had to keep — same-coverage constraint,
  [0,1] bound, exclusion reasoning, null policy — all present with the word gone.
- Grepped the seed AND the generated file itself; noted the remaining CSV hits are in
  `interpretation`, which the generator never reads.
- Verified the guard and its test no longer share the narrow definition that made the miss possible.
- All ~35 window removals checked individually; `pass_accuracy_pct`'s "summed rather than averaged"
  checked against that row's own numerator/denominator; the four entity splits judged genuinely
  different metrics.
- ROUND 3: compared the seed's blob hash across rounds (identical), so no content re-review needed;
  confirmed `_same`/`_to_disk` touch only line-ending mechanics.
- Field-by-field: no formula, direction, tier or format changed anywhere in the diff.

## analytics-engineer-reviewer
VERDICT: PASS (round 3)
risks_checked:
- ROUND 1 FAIL: a third seed edit (`contribution_share`) undisclosed, while `acceptance_evidence.md`
  claimed to have accounted for every content change and found exactly two. It had audited the 23
  yml sites and never the seed's own diff. Its framing: the drift this programme exists to prevent,
  reproduced one layer up in the seed itself.
- Verified the "forced by the gate" claim against `check_description_hygiene.py`'s actual regex.
- Swept the rest of the seed diff for further undisclosed content edits — none.
- Re-swept all four split-metric names across the working tree: 0 blank, 0 inline, no fourth site.
- Layer placement: `{{ doc() }}` is a compile-time substitution creating no `ref()`/`source()` and
  no DAG edge, so a seed-sourced description on a core column is documentation, not a violation.
- Information loss judged across all 23 sites individually, including confirming
  `pass_accuracy_pct`'s lost range-test note survives as a real model-level test.
- ROUND 3: confirmed the script's own `import io` is genuinely used, rather than assuming the dead
  import was a repeated defect; confirmed the fix does not reintroduce the MR2 silent-rewrite.

## platform-reviewer
VERDICT: PASS (round 4)
risks_checked:
- ROUND 1 FAIL: `_describe_drift` names added, removed and changed blocks and only "changed" was
  tested. Proved it by hand-running the mutation: the exit code comes from the byte comparison in
  `main()`, so deleting the add/remove branches left everything green.
- ROUND 3 FAIL: `_to_disk`'s CRLF-preservation branch had no test reaching it through a genuine
  write — the test built for it hit the "already up to date" short-circuit and returned first.
  Deleting the branch left all 30 tests green. Reproduced by mutation before fixing.
- ROUND 4: confirmed the production blob hash unchanged so it re-derived nothing; traced the new
  test's control flow to `OUT.write_bytes` rather than the short-circuit; checked the assertion
  ORDER (write-happened, content-present, then endings) as the guard against the same vacuous
  failure mode.
- Judged the non-atomic `write_bytes` acceptable with better reasoning than the contract gave: the
  file is git-tracked, so a truncated write is recoverable without rerunning the generator, and a
  rerun self-heals.
- Judged the unwired `--check`: inert rather than broken, with the residual gap named precisely —
  `check_description_hygiene.py` has no notion of "does the block match the seed".
- CRLF fix, floors, re-run safety, dependencies, credentials, guard paths: all checked.

## scope-auditor
VERDICT: ESCALATE (round 4) — PASS on the diff itself; the round-cap question escalated.
CPO ANSWER: "yes" — record the override, reason "round 3 found a real test gap, fixed in round 4;
not looped on disagreement". Recorded in `rounds_cap_override:` above and in `escalations` below.
risks_checked:
- ROUND 1 FAIL: two edits to `metric_catalogue.csv` were mine, not the CPO's, in a file the
  decision-rights table reserves to him. Flagging them in the evidence was not the same as asking.
- Judged whether the amendment records an answer or wraps reasoning around one: found the answer
  recorded minimally, each edit named with before and after, and the self-critical framing
  attributed to me rather than to the CPO.
- Ruled the `finishing_efficiency` fix sits INSIDE the original window authority rather than needing
  fresh sign-off, because it enforces an instruction already given more completely.
- Read the new `escalations.log` entry in full against the diff and its own findings: six defects
  named, each attributed to whoever caught it, "flagging is not asking" stated as its own point,
  no defect reframed as someone else's fault.
- Confirmed the CI-wiring deferral is recorded with a concrete blocking reason, not dropped.
- Scope and protected paths clean in every round; no credential-shaped content.
- ROUND 4: ruled the diff sound and in scope, and escalated the round-cap question rather than
  settling it, on the grounds that the override is the CPO's to record and not a reviewer's to
  waive.

## escalations
- question: This branch is at round 4, one over the cap of 3, with no `rounds_cap_override`. Does
  the cap count every round mechanically, or does a round that a reviewer used to catch and fix a
  genuine defect not count against it? scope-auditor recommended the former, finding no textual
  support for the exception and noting the builder had flagged his own reading as self-serving.
  CPO ANSWER: "yes" to recording the override, with the reason "round 3 found a real test gap,
  fixed in round 4; not looped on disagreement".
