# Review — claude/36-crest-fill — 2026-11-22

diff_sha256: 51891e7a01537eab6ae835350455af74f5f270dd083a178e0f973f76ad1098f5

rounds: 1

## scope-auditor
VERDICT: PASS
risks_checked:
- Every changed file is in scope_paths; the CPO ruling is recorded with its date, and the protected_override names it for docs/design/components.yml.
- The diff removes CSS declarations and adds registry text: no new mechanism, dependency or recurring cost; the placeholder ink is a visual detail under the visual-details mandate.
- block_standard.md is generated from measured rows only, so the unchanged table needs no regeneration; the border pin 11 to 9 matches the two removed declarations.

## cto-reviewer
VERDICT: PASS
risks_checked:
- The existing part key `rule` on three parts already recorded as `gap: mock-css` is new use of an existing field, not a new mechanism; the contract states that no check enforces the text until #340 adds the measured row.
- The guarded class set of check_page_css.py is unchanged, because rows() skips mock-css gap parts; no hook, workflow or CI file is touched.
- The border pin falls, which tightens the ratchet; no dependency, cost or credential change.

## platform-reviewer
VERDICT: PASS
risks_checked:
- The border pin 11 to 9 traced through declarations(), _governed() and unchecked_properties(): the two removed border declarations account for exactly the fall; the background pin is correctly unchanged.
- `rule` is an allowed part key and gap parts are skipped by rows(), so the generated block standard stays byte-identical.
- The other consumers of .crest and .pphoto are layout rules that do not depend on the removed background or border.

## bi-analyst-reviewer
VERDICT: PASS
risks_checked:
- The diff touches only the three image-spot rules, registry text and the pin: no component field, label, string or sample data changes.
- The evidence reads computed style and box geometry at 280px and 375px in both themes, with the instrument and its limit (remote images did not load) stated.
- No stray override re-adds a background, border or radius for these classes in either theme; geometry is unchanged.

## escalations
(none)
