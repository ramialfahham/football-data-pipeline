# Review — feat/259-player-export — 2026-11-06

diff_sha256: a9d50c4cefcd1c7023f2c325b7334b9189f9f184a4963bd3278eb54dc0d25f04

rounds: 2

## scope-auditor
VERDICT: PASS
risks_checked:
- Round 1 doc-sync: docs/site_architecture.md carries the approved Player row and dbt_project/docs/layering.md names is_in_page_window.
- docs/wireframes/03_player_profile.md stays until the next MR retires it, as the contract states; no page output changes here, so no reader acts on it.
- All changed files are in scope_paths; players is not in deploy:export, so the export's cadence and volume do not change.
- The reserved decisions stay undecided: the payload carries the blanks.

## analytics-engineer-reviewer
VERDICT: PASS
risks_checked:
- Round 1 point 1: match_involvement is served by the mart with an accepted_values test, and the export only filters on it.
- Round 1 point 2: assert_player_page_windows now compares each tab's played matches with its Appearances card, over the same status filter, window join and stat rows, so a mismatch fails it.
- Grain: int_player_page__window_seasons is unique per player, window type and season, so the join cannot fan out the mart.
- No metric is created or redefined, and no competition is hardcoded.

## platform-reviewer
VERDICT: PASS
risks_checked:
- Round 1 finding: the peer query casts season_api_year, and a test fails if the cast goes; the same query shape validated on a dry run.
- export_all raises before any query or write when no boards exist, with a test that reaches the raise.
- fetch_player_metric_rows carries the metric_order guard of fetch_metric_rows.
- The linked-set duplication with builtPlayers.mjs stays accepted: both read the same two sources.

## escalations
- question: the exact text of the Player row in docs/site_architecture.md, a core document.
  CPO ANSWER: approved in chat, 2026-11-06, relayed by the coordinating session.
