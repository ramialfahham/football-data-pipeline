# Review — claude/231-phone-fixes-70f283 — 2026-11-19

diff_sha256: 6a482bc43c7974c190465485833914a9084cb8c2cadd0c691457c50382a86bfd

rounds: 4

rounds_cap_override: round 4 reviews only the changes found by ci_local after round 3 (the filter button floor moved to the Filter bar's buttons, two rule texts split to the sentence limit, the rendered pins lowered from the linux runs); approved in chat, 2026-11-19

Rounds: round 1 found the filter button floor inert, the line count blind to an unbreakable word, and a contract that disagreed with the diff; round 2 found only the Deserved points head scroll at 280px, held for the narrow head wording; round 3 followed the CPO's approval of that wording (approved in chat, 2026-11-19); round 4 is the delta found by ci_local, recorded above.

## scope-auditor
VERDICT: PASS
risks_checked:
- The filter button floor moves from `.seg .seg-btn` to `.fbar > .seg:not(.sel) .seg-btn { min-width: 44px }`, with the two `.fbar` flex rules still non-shrinking: the same B8 ruling declared in decisions_taken, narrowed to the buttons the issue's filter-bar breaks came from; the `.seg-btn` min-height is unchanged; no new mechanism or cost; the pin test expects exactly one `.seg-btn` sizing rule and no shrinking `.fbar` flex rule.
- Registry and doc-sync: the Filter button row has its earlier text and measures again; the new `button-tap` row (`.fbar .seg-btn`, `min-box=44px`) is identical in components.yml and the block_standard.md table; the sentence splits change no wording.
- Baselines: baseline.json, baseline_quick.json and baseline_quick_fi.json only lose or lower pins (Competition overview split removed, Match page scroll 2003 to 1913 and 1077 to 1017, split removed); nothing rises; all are in scope_paths; the pins fall because the defects they counted were fixed, not by cutting coverage.
- The contract's 2026-11-19 amendment for items 1 to 3 names its authority and touches only files in scope_paths; no new §10 decision; the earlier amendments are unchanged.
- No credential or workflow permission change.
- Round 4 is beyond the cap of 3; the rounds_cap_override above records the CPO's approval.

## cto-reviewer
VERDICT: PASS
risks_checked:
- Rounds cap: round 3 was the cap, and a round beyond it is valid only with a `rounds_cap_override:` recorded in review.md; it is recorded above.
- The contract's 2026-11-19 amendment names the three changes with their authority (the coordinator's rulings of 2026-11-18; the repo's pins only fall), adds no scope path, and protected_override still covers every components.yml hunk; the new `button-tap` part splits out the 44px rule the override already named, with no new text style, colour, spacing or corner value.
- Filter button floor: `.seg-btn` is produced only by FilterBar.astro (inside `.fbar`); `CompetitionIndexGrid.astro` mentions it only in a comment; the scoped selector covers every button the approved #231 text names, the legacy mocks being its only other users; the pin test expects exactly one sizing rule and no shrinking `.fbar` flex rule; the Filter button part keeps its earlier text, the 44px sits in `button-tap` (`min-box=44px`) and the design check still measures it; no guard is weakened.
- Pins: every baseline change is a fall (baseline.json: Competition overview split removed, Match page scroll 2003 to 1913 and split removed; baseline_quick.json: Competition overview split removed, Match page scroll 1077 to 1017; baseline_quick_fi.json: Competition overview split and Match page split removed); the component_registry `min-width` pin stays at 28; nothing rises.
- The sentence splits are wording-neutral, and the sentence-length pin of 9 is the check; no hook, workflow, CI or check script is touched; no dependency, cost, credential or permission change.

## platform-reviewer
VERDICT: PASS
risks_checked:
- Filter button floor, system.css: `.fbar > .seg:not(.sel) .seg-btn { min-width: 44px }` (specificity 0,5,0) sits on the Filter bar's buttons only, no other rule sets a width there, and the two `.fbar` flex rules stay non-shrinking (`1 0 auto`, `0 0 auto`), so a button is never narrower than its text; the explicit min-width costs nothing and removes the automatic-floor problem that overlapped the legacy mock's buttons; every real `.seg-btn` is a child of `.fbar > .seg:not(.sel)` (FilterBar.astro), covering both the wrapping and the one-line state; the `filter` measure (scrollWidth against clientWidth) still sends an overflowing row to the dropdown; the component_registry `min-width` pin stays 28.
- Pin test: it asserts exactly one sizing rule on `.seg-btn` (`.fbar > .seg:not(.sel) .seg-btn` with `min-width: 44px`) and rejects any `.fbar` rule whose flex has a nonzero shrink; it fails if the min-width is reverted or moved, or if either flex rule shrinks again. Accepted gap: a rule in a selector that neither starts with `.fbar` nor contains `.seg-btn` could narrow a button; none exists and tests/test_phone_built_pages_231.py is the backstop.
- Registry: `button` has its earlier text and measures; `button-tap` is its own part (`.fbar .seg-btn`, `min-box=44px`); a repeated `class` across parts is already used; `min-box` is an existing measurement kind.
- Rendered pins: all three baselines only fall; platform linux kept; none raised.
- The sentence-length split of the two rule texts keeps the same words; the block standard is regenerated to match; the contract's 2026-11-19 amendment agrees with the diff.
- Rounds cap: round 4 is recorded with the CPO's override above.

## bi-analyst-reviewer
VERDICT: PASS
risks_checked:
- The 44px floor moved from `.seg .seg-btn` to `.fbar > .seg:not(.sel) .seg-btn { min-width: 44px }`; the two later `.fbar` flex rules (`1 0 auto`, `0 0 auto`) never shrink the button, so it keeps its text-width floor and the 44px minimum on top of it, which is what overlapped the legacy mock's buttons; the base `.seg .seg-btn` is back to `flex: 1`; the late block carries no min-width; this keeps the round-1 fix on the one place every built button lives (FilterBar.astro).
- The pin test fits the new CSS (exactly one sizing rule on `.seg-btn`, `.fbar > .seg:not(.sel) .seg-btn` with `min-width: 44px`, and no `.fbar` rule with a non-zero shrink); the regex read against the CSS holds.
- Registry: the Filter button part has its earlier text and measures again; the 44px is its own part, `button-tap` (`.fbar .seg-btn`, `min-box=44px`); no wording of the Filter button part changed.
- The two split rule texts carry the same wording as round 3: no clause added, dropped or changed, only the punctuation split.
- The rendered pins only fall or drop to 0 and none rises; banned_properties 6 to 4 and the min-width pin (28) stand.
- The contract's 2026-11-19 amendment covers items 1 to 3 with its authority; no scope, decision or acceptance text was widened.
- The built-output evidence of rounds 2 and 3 still stands; the only rendering-affecting change is the filter-button rule, which the validate:ui re-run (no matches-hub overlap, scroll count at its pin) already covers.

## escalations
(none)
