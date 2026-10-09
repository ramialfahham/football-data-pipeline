# Review — feature/166-site-chrome

diff_sha256: f11a1eaf4ceff3cbe6187a086fc5b1235a7bc33dba40ad2ccfc22e455a880a99

rounds: 1

## scope-auditor
VERDICT: PASS
risks_checked:
- Every path is in scope_paths; the two pin tests come with a dated approved amendment.
- The section on every page is the approved reading; pages only pass a prop, no page-side logic.
- The Imprint label, links inside text, the team page's rows, Home's intros and the Rankings tab order are untouched.

## bi-analyst-reviewer
VERDICT: PASS
risks_checked:
- menu.ts uses existing keys present in EN, DE and FI; no new strings; all 9 Layout callers pass the right section, Home none.
- The marked item matches the render's rule: aria-current, ink and 700, the inset 2px line only in the menu; the footer row follows the menu.
- The evidence parses all 2,538 built pages and measures the look at 1010 and 375px.

## platform-reviewer
VERDICT: PASS
risks_checked:
- `.mainnav .on` and `.drawer .on` cannot reach `.comp-tabs .tab.on`, and they beat the menu's base rules.
- `section` is optional through Layout and SiteHeader; the page set is unchanged.
- The two pins only move down, matching the removed comment lines and long sentence; no dependency, credential or CI change.

## escalations
(none)
