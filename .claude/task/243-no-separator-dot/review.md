# Review — claude/243-no-separator-dot-ba088b — 2026-11-17

diff_sha256: ebc1d35157d37b2b015bfe567f379b2a67846357256af29d8a0a50f7115cf027

rounds: 4
rounds_cap_override: round 3 failed on one hunk, now reverted to main's text; round 4 verifies the revert

## scope-auditor
VERDICT: PASS
risks_checked:
- Round 4 verified the revert of the one hunk round 3 failed: the team header's venue unit again reads venue, comma, city, so only the facts-line wrapper differs from main there. Every file in the patch sits inside scope_paths, the component-registry and quick baselines are unchanged, the design-inventory baseline only falls, and the three jobs (facts as units, name over qualifier, dot to comma) are the only changes.

## bi-analyst-reviewer
VERDICT: PASS
risks_checked:
- Round 3 checked that no value, label or order changed, that the round names carry a comma in EN, DE and FI, and that a unit wider than the line takes its own line (measured at 280 to 1280px). Zero "·" on the six page kinds at 375 and 1280px.

## cto-reviewer
VERDICT: PASS
risks_checked:
- Round 2 checked new mechanisms, dependencies, recurring cost, the protected-path override for docs/design/components.yml and that no pin rises: only the facts-line CSS class is added, a client script is removed, one pin falls.

## platform-reviewer
VERDICT: PASS
risks_checked:
- Round 3 checked the shared rule (a unit has max-width 100% and min-width 0, no nowrap), the justify test over every rule of each aligned host, the removed dot mechanism and its test, and that the registry and design-inventory pins do not rise.

## escalations
(none)
