# Review — claude/297-board-window — 2026-11-18

diff_sha256: d72dea9600307267c81c775daa722b9df33529b8a784a832d3b91ee0858da08e

rounds: 1

## scope-auditor
VERDICT: PASS
risks_checked:
- Every changed file and the task folder sit inside scope_paths; no amendment.
- decisions_reserved is none; the board's place and label and the window rule rest on #132's notes of 2026-11-10; no new metric, label text, URL or slug.
- No new mechanism or recurring cost: an existing test class, a join to the model's own team_matches CTE, a one-off 90 MB read.
- The impact_map carries the dbt ls lineage and measured counts (89 of 6,641 sides, rows 164,802 to 162,737).
- approved_design match: #132 covers both affected pages, the played match page and the upcoming match page.

## analytics-engineer-reviewer
VERDICT: PASS
risks_checked:
- Layer placement: the window rule is in the mart, reading int_legs__team_match; the played_now join reuses team_matches, one row per (team_sk, league_code, season_api_year), so no fan-out.
- SQL logic: fixture_season_api_year in both union branches; the where clause runs before qualify, so previous-season rows survive only while the team has no non-awarded match this season.
- The new singular test recounts against fct_fixture's season with the same awarded-result exclusion; no test removed; the yml description and window_type doc block still state the rule.
- No catalogue change: ball_actions_player and its label key already exist; the export only catches up with the mart's match_boards.
- Competition-agnostic, no seed or project config change, the same-window floor still pairs minutes and team_matches of one season.

## platform-reviewer
VERDICT: PASS
risks_checked:
- Re-run safety: stateless SELECT, constant tuple, read-only test.
- Test coverage: the subset-to-equality change fails on a revert (the mart lists eight match boards); the order matches the catalogue (group 3 order 6, group 3 order 8, then group 4); the label key is covered by check-metric-labels.test.mjs.
- No hook, workflow, dependency, credential or hosting change; build health unchanged (fewer mart rows, one more board per played payload).

## bi-analyst-reviewer
VERDICT: PASS
risks_checked:
- The one site_v2/src change is a METRIC_TERMS entry: playerMetrics.ballActions.label maps to ballActions (EN Ball actions, DE Ballaktionen, FI Pallotoiminnot), not in PER_90, correct for a count board.
- Binding rule: the export takes the board's name key and format from the catalogue; no committed sample is touched.
- The locked board order matches the test and #132's note of 2026-11-10 17:43; the window labelling (prev_season / season_to_date) is unchanged and no stale-season number reaches the page.

## escalations
(none)
