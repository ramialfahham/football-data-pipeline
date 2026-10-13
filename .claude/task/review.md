# Review — feat/176-match-window

diff_sha256: f1eb77546b3a94dcffa10592669d0fbd210721e49616cc2944056bd7d2d47aa0

rounds: 3

## analytics-engineer-reviewer
VERDICT: PASS
risks_checked:
- The match_window branch of int_team_momentum_window: match_legs gives candidate_legs' 41 columns in the same order and types; the trailing recency_rank <= 5 still binds only to the last-5 branch.
- Existing form rows unchanged: the old branches are untouched and match rows carry keys disjoint from upcoming fixtures (FT/AET/PEN/AWD/WO against NS/TBD), so the grain tests hold.
- Readers that must not see match rows filter them: the player builder, the form list, and the tests comparing against those; mart_matchday_insights joins upcoming fixtures only.
- The generated gates apply to a window of one: an awarded match blanks the team rates, a missing input blanks the rate; the formula and coverage tests now check the match rows too.
- The key rename reaches every consumer; the intermediates' persisted descriptions now describe the match window; the shared window_type doc block reads true on all six columns that carry it.

## bi-analyst-reviewer
VERDICT: PASS
risks_checked:
- The fixture payload keeps its form-block keys after the key rename; the unit tests feed fixture_sk-keyed rows and assert the exact block.
- metric_rows.json: the same 37 metric ids under the renamed table, order from the catalogue; served set and order unchanged.
- No match row reaches a page or payload: the export is upcoming-only and is_form_window is false on match rows.
- The block-to-mart map, the README and the window doc block name the new mart; no stale name left outside the design mocks reserved to #175.
- The built site is byte-identical to main; the window-of-one labels are the played match page's question, not this change's.

## platform-reviewer
VERDICT: PASS
risks_checked:
- Export form read: table, key column and _W1_DROP renamed together; the fixture payload keeps its keys; tests fail on a revert.
- The singular tests that read the renamed mart or the window selection, read by hand: aliases and match-row filters correct; the new coverage test fails on a missing, doubled or wrong-sized match window.
- The page-spec prebuild gate validates the renamed spec; deploy order fails closed before the first build on main.
- Pins recounted against the gates: code 744 lines in 185 files, README history 18, README long sentences 22, metric_rules.md unchanged at 2.
- Acceptance evidence demonstrates each criterion, with the page count reconciled and the README figures current.

## scope-auditor
VERDICT: PASS
risks_checked:
- Every changed path is inside scope_paths, the sentence-length pin file added by amendment.
- Each core-document edit matches its approved text: the decisions_taken texts and amendments (1) to (4), the last corrected after round 2 with its own approval.
- The reserved decisions are untouched: the prod table, the intermediates' names, mart_leaderboards, mart_team_fixture_stats.
- Threshold declarations honest: no new mechanism; the recurring-cost rise declared, to be measured.

## escalations
(none)
