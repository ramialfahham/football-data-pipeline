# Review — feat/243-component-checks

diff_sha256: a5626d4ca073cb18b067c9358df72266e9d2fc257d55938de48074b17ef27b09

rounds: 3

## scope-auditor
VERDICT: PASS
risks_checked:
- All changed files are inside scope_paths; the contract is unchanged in round 2, so no amendment needs authority.
- Every reading the checks apply (the banned list with break-word, the widths, the languages, per-page counting, the baseline that only falls) is in decisions_taken with its approval; decisions_reserved is none and the diff decides nothing outside it.
- The new mechanism (the count baseline read by the two existing checks) and the recurring cost (validate:ui renders 183 more pages per run) are declared; no CI job, CI file change or dependency is added.
- Appendix A: no invented metric, no product decision written into docs, no unilateral mechanism; no page or export file is touched, so approved_design none holds.
- The added Markdown sentences carry one topic each and no history; the round-2 doc sentence does not contradict decisions_taken.
- Round 3: rendered.pages now holds 25 entries from validate:ui's counts.json; keys are the five known counts, values positive, static section untouched; done_when's third line is met.

## platform-reviewer
VERDICT: PASS
risks_checked:
- Round 1 FAIL (the exit-code wiring was untested) is closed: compare_rendered is a pure function pinned in rose, equal, fell, platform-mismatch and narrower-run cases, and lint.main is pinned to exit 0 on the real baseline and 1 with the FAIL line on a lowered pin.
- Re-run safety: the artifacts folder and counts.json are overwritten safely; servers and temp folders are released in finally.
- Fail-closed: a missing or malformed baseline exits 1 in both scripts; a page that fails to render leaves its pin unmatched or adds a hard failure.
- The planted-defect test is consistent with counts_red.html and COUNT_JS; the per-gap static test fails if any regex is reverted.
- All 14 width_rules entries match the @media and @container lines in system.css; static counts use posix paths and are platform-independent.
- No dependency, credential, workflow, .gitlab-ci.yml or hosting change.
- Round 3, prior finding 2 resolved: rendered.pages holds 25 entries; 25 class pins plus 17 other pins equal the 42 empty pins the first pipeline failed on; the shape matches what compare_rendered reads and the baseline-shape test asserts.
- Remaining risk, not a defect: the pins come from one CI run; the next pipeline is the first repeat measurement and shows any page that is not deterministic.

## bi-analyst-reviewer
VERDICT: PASS
risks_checked:
- The block_standard.md edits are prose about the checks; they add no wireframe block, inventory element, field or metric, and nothing under site_v2/src or the export changes.
- The doc's list of lint counts and rendered counts matches counts(), COUNTS and COUNT_VIEWPORTS in the scripts; the Pages-table sentence matches unlisted_mock_modules and mock_modules.
- Round-1 note closed: the doc now says the rendered counts are compared only on the platform the baseline names, which matches compare_rendered.
- The added doc lines carry no date, issue or MR number, reviewer credit or story phrase.
- Round 3: the baseline pins record today's gaps (Home overflow 227, the two hub mocks 112 each) and hide none; no doc, page or display-contract file changed.

## escalations
(none)
