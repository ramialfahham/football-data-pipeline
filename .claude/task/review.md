# Review — feat/lineup-research-pl

diff_sha256: 99a62e6adc22a93952d4e457dfec91f95aacf5f802f0b41882fe25810b4cd691

rounds: 2

## scope-auditor
VERDICT: PASS
risks_checked:
- Only the contract and the seed change, both in scope_paths; only Premier League matches of 2025-26 and 2026-27 are researched, so the next leagues and the older seasons stay reserved.
- Every rule the rows follow is in decisions_taken with a named approval: the research order and sources, the outgoing-player rule in its corrected wording, and the half-time minute convention; the official minute where it differs and the team-sheet id for a player with two provider ids follow the approved scope.
- No new mechanism and no recurring cost; nothing in Appendix A applies.

## analytics-engineer-reviewer
VERDICT: PASS
risks_checked:
- All 999 rows read: 25 matches, two participant teams each, 11 distinct starters per sheet, no player on both sheets, no starter with a minute on.
- Every substitute's replaced player is on the same team's sheet with a matching minute off, extras included, and same-minute changes pair one to one.
- One formation per sheet, matching the grid positions checked; source, source kind and note constant per match, and each note's fact matches its rows.
- The contract's rules and the evidence count (25 of the 26 missing substitutions had an outgoing player who came on earlier) match the rows.

## escalations
- question: Official match pages show half-time substitutions at 45' and the provider at 46'; which minute do the researched rows store?
  CPO ANSWER: approved in chat, 2026-10-12: keep the provider's 46'.
