# Review — claude/231-hyphen-tolerance — 2026-11-21

diff_sha256: e10867cb16604aa3fc3cd375197c72e023f53af753623d5e43160b597777ac18

rounds: 1

## scope-auditor
VERDICT: PASS
risks_checked:
- Scope: the four changed files are in scope_paths and the contract has no amendments; no defect.
- protected_override: it names the approval source and date and declares both locked files; no section 10 class is decided; no defect.
- New mechanism or recurring cost: the probe is a transient DOM node inside the existing counting script; no added run, query or call; no defect.
- Coverage cut: the break-after-hyphen loop is untouched and a word that fits its line is still counted; no defect.
- Approved design: no page output changes; no defect.

## cto-reviewer
VERDICT: PASS
risks_checked:
- Guard loosening: only the width test changed, from the sum of character widths over the line plus a pixel to the one-line probe width over the line; every break not after a hyphen still counts and the exemption stays limited to the part marked breaks hyphens; no defect.
- The new criterion matches the registry rule that a club name breaks at its hyphens only where it is wider than the line; no defect.
- Probe inflation: no rule in system.css gives a classless span under .club, .cn or .nb padding, margin or a font; no defect.
- Authority: the override names where and when and matches the two protected paths in the diff; the impact map is not a placeholder; no defect.

## platform-reviewer
VERDICT: PASS
risks_checked:
- The probe inside the TreeWalker loop is appended after the text node is read and removed before the next node; the walker never visits it and no count reads it; no defect.
- The probe width equals the real one-line width: inherited font, letter-spacing and text-transform carry over, and nowrap overrides hyphens and overflow-wrap; no defect.
- Fail direction: a broken probe reads zero or smaller and the word is counted, so the check fails closed; no defect.
- Tests: the wider-than-line test returned split 1 on the old code and fails on revert; both box widths are measured in the page, so neither depends on a font; no defect.
- Baseline: a count can only fall, and a fall already forces a baseline edit that the contract reserves as an amendment; no defect.

## escalations
(none)
