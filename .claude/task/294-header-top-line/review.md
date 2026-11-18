# Review — claude/294-header-top-line — 2026-11-18

diff_sha256: e419d0ad4d64c006adf999f975b1696af21f6947ca65d0c278282639b9aea122

rounds: 1

## scope-auditor
VERDICT: PASS
risks_checked:
- The diff touches only Masthead.astro and the task folder, both in scope_paths.
- The user-visible change (no top line on cancelled, abandoned and awaiting-result pages) rests on #294 note 4265824946, approved in chat, 2026-11-18, and is declared in decisions_taken.
- The condition reads only the served unplayed_state; a played match keeps its status word; a not-started or postponed match keeps "Match preview".
- approved_design names the match page (#132); the impact map's grep shows the match route is Masthead's only consumer.
- No secret, new mechanism or recurring cost; the code comment states current behaviour only.

## bi-analyst-reviewer
VERDICT: PASS
risks_checked:
- Binding rule: the only field read is unplayed_state, already served and typed; no new field and no sample data touched.
- Branch logic covers every UnplayedState value with no fall-through; a played match cannot carry a state.
- A status page loses a line but no information: the status tag stays in the kick-off line.
- No new or changed string; the rendered evidence covers 6 kinds in EN/DE/FI at 280 to 768px with 0 defects, measured as DOM geometry, the one first-pass flag being the visually hidden title.
- The element is removed and no CSS added; the committed sample takes main's branch on every page.

## escalations
(none)
