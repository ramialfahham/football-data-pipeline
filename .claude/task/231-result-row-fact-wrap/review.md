# Review — claude/231-result-row-fact-wrap — 2026-11-19

diff_sha256: 1dadff56b9e241bc2dae1302b10742178e44b7392277a953fcb91a2719191ff1

rounds: 2

Rounds: round 1 passed on all four reviewers; the platform reviewer noted that the new registry part measured the `.cn` box, which holds its own content and would pass with the fix reverted; round 2 is the delta, the part measuring its `.club` box (174px of content in 146px at 260px before the fix, 146px in 146px after).

## scope-auditor
VERDICT: PASS
risks_checked:
- Scope: the four files outside the task folder (system.css, components.yml, block_standard.md, tests/test_phone_fixes_231.py) are in scope_paths; no baseline fixture is touched.
- Protected override: the components.yml change adds one part measured `fits` and no text style, colour, spacing or corner value; the override names its approval and the visual-details authority, and its text names the `.club` measure.
- Rule narrowing: `.club .cn` leaves the Name in whole words selector, whose measure splits at spaces only; the new part measures overflow instead, stated in its rule text.
- No new mechanism, cost or decision; decisions_reserved is none; the contract and evidence amendments of round 2 widen no scope, decision or acceptance text.
- No credential or workflow permission change; approved_design names the page issues where `.club .cn` renders.

## cto-reviewer
VERDICT: PASS
risks_checked:
- No new mechanism, dependency or cost: one CSS rule, one registry part, one test; decisions_taken says so and the diff agrees.
- Guard authority on docs/design/components.yml: protected_override and a substantive impact_map are present.
- Guard weakening: moving the measure from `.cn` to `.club` makes the check stricter; the measurement kind is unchanged and nothing is downgraded.
- Class `cn` kept with selector `.club` keeps the pinned unlisted-class count from rising; no other part uses `.club`.
- No secrets or permission change.

## platform-reviewer
VERDICT: PASS
risks_checked:
- Fit-script interaction: a name that breaks at a hyphen makes the line count 2, so a row still steps from fit-one to fit-two; fit-two ends with a row-level scrollWidth check.
- Selector reach: `.cn` is emitted only by ResultRow.astro; the new rule (0,3,0) beats `.nb`; its declarations are on the non-visual list, so no unchecked-property pin rises.
- Round-1 note closed: the `fits` measure now sits on the `.club` box, which scrolls in the defect state and fails with the fix reverted; the Python source pin is a second pin.
- No hook, workflow, CI, dependency, credential, hosting or build change; re-run safe.
- Residual: `fits` is strict to the pixel; the measured 146/146 and 166/166 show no false failure.

## bi-analyst-reviewer
VERDICT: PASS
risks_checked:
- Blast radius: `.club .cn` is emitted only in ResultRow.astro (result, meeting, goal and scorer rows); a name that fits is unchanged, and the 280 and 320px sweep counts are identical before and after.
- A no-break unit of initial and surname can also break at its space where it alone is wider than its line; before it overflowed, so this is not a defect, and the sample has none.
- Registry and generated table agree; the new part is bound to a real element; no text style, colour, spacing or corner value is added.
- The test pins the one rule, its two declarations and no width property.
- No metric, label, string, null-handling, percentage or window change.

## escalations
(none)
