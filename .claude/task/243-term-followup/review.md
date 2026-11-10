# Review — claude/243-term-followup

diff_sha256: a06a24d1e20623a7067819e07b836e875ab1badf1c64aa012fc062dd815ab3c9

rounds: 7

rounds_cap_override: merge from main and the stale menu counts, approved in chat, 2026-11-10

## scope-auditor
VERDICT: PASS
risks_checked:
- Every changed path is in scope_paths; 10_home.md entered by a dated amendment, and its line 90 is the approved text.
- The merge from main leaves gen_competitions.py as main has it; the branch no longer changes it.
- The nav map's menu notes and the All matches card read the built pages; the Players note says designed, not built.
- The competition tabs sit under the competition page's design; the save word's approval is the note on the issue; the Standings address and word rows existed only for the Standings menu page.
- tests/test_sentence_length_in_docs.py entered by a dated amendment; its 10_home.md pin falls from 128 to 127 and nothing else in the test changes.

## platform-reviewer
VERDICT: PASS
risks_checked:
- The line 90 cut removed exactly one table-cell sentence over the limit, so 10_home.md counts 127 and the pin matches it in both directions.
- 09_chrome.md keeps its pinned count; site_architecture.md gains no long sentence.
- No other test, hook, script, workflow or dependency changes.

## bi-analyst-reviewer
VERDICT: PASS
risks_checked:
- Header, drawer and footer read one five-item list in EN, DE and FI; Competitions, Matches and Teams link, Players and Statistics do not, as 09_chrome.md and the nav map now say.
- One save reads save, Parade and torjunta; more read saves, Paraden and torjuntaa; the competition table section keeps Table, Tabelle and Sarjataulukko.
- The rendered evidence names its sources and why no screenshot was taken.

## escalations
(none)
