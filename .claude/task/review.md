# Review — feat/gap15-team-fixtures-export — 2026-06-29

> Blinded review cycle (G3). Round 2 (final). All three required reviewers re-run fresh on the
> updated diff. Required set for the staged paths (scripts/export_*.py): scope-auditor (always) +
> analytics-engineer (dbt_project/**? — export consumes marts) + cto (scripts/export_*.py).
> Routing `scripts/export_*.py` → analytics-engineer + cto; scope-auditor always.

diff_sha256: 5d3c223eafb959116ca5572cc6036a0377ec4788d07fbbb095401b40ed22355b

## scope-auditor
VERDICT: PASS
risks_checked:
- §10 naming recorded with authority: the published key names next_fixture/recent_results are the one user-visible naming decision; the contract now records them in decisions_taken as CPO-decided (AskUserQuestion sign-off 2026-06-29), removed from decisions_reserved — no §10 taken silently. Scope is exactly the 3 declared files.
- Consumption-layer purity + empty-state: the export filters on the mart's precomputed upcoming_rank/recency_rank, selects display fields via a keep-list (_TEAM_FIXTURE_FIELDS), and strips all internal keys (asserted in the test); a season with no fixtures renders next_fixture=None + recent_results=[] (tested). No derivation/reinterpretation; impact_map honest (view over fct_fixture, one bounded scan/night).

## analytics-engineer-reviewer
VERDICT: PASS
risks_checked:
- Season-key lookup survives _strip_identity: the fixtures bucket is keyed (league_code, season_api_year) from raw rows; the post-strip profile row keeps both keys (not in the identity denylist), so fixtures attach to the right season — no silent empty-array from a key mismatch.
- Simplified filter `1 <= (recency_rank or 0) <= 5` is semantically identical to the prior form (None→0→excluded, 1-5 included, 6+ excluded); the test exercises the rank-6 exclusion boundary + the None/empty-season case; consumption purity holds (selection on precomputed ranks only).

## cto-reviewer
VERDICT: PASS
risks_checked:
- Cost characterization verified against mart_team_fixtures.sql line 1 (materialized='view'): one bounded scan per nightly export over the small fct_fixture fact, not a per-team N+1, zero API-Football quota, no new run — the contract's cost line is accurate; null ranks exclude live/postponed rows at the BQ WHERE before Python.
- SQL/refactor safety: the sample-path id_list uses str(int(t)) (ValueError before interpolation → injection structurally impossible, mirrors fetch_player_payloads); the WHERE `(upcoming_rank=1 or recency_rank<=5)` is correctly parenthesized vs the appended `and team_sk in (...)`; the sort lambda only sees in-range ranks (post-filter); shape_team_payload's new fixture_rows=None default keeps the pre-GAP-15 callsite/test backward-compatible.

## escalations
- question: The published JSON key names for the team fixtures section (next_fixture / recent_results) are a §10 naming decision (user-visible, permanent once published) — what names? (Raised by scope-auditor round 1.)
  CPO ANSWER: next_fixture / recent_results, nested per seasons[] row — explicit AskUserQuestion sign-off, 2026-06-29. Recorded in the contract's decisions_taken.
