# Review — chore/reconcile-content-arch-status — 2026-06-30

> G3 Lock artifact. Doc-only status reconciliation: docs/content_architecture.md §3 (block ↔ mart) + §7
> reconciled to the verified built-vs-wired-vs-orphan-vs-not-built state, with a legend. Required set
> (routing): always → scope-auditor only — the diff touches docs/content_architecture.md (no specialist
> route) + .claude/task/contract.md (hashed). No code path.
> Round 1 FAILED (accuracy): the legend said "15 marts" (a comment-mention of mart_matchday_insights was
> miscounted → real = 14) and the Match-preview row listed mart_matchday_insights (the live-MVP mart, not
> queried by the v2 export) under a strict "built AND wired" legend. Both fixed: count → 14; Match-preview
> → v2 composition (W1/W2/standing/h2h) with mart_matchday_insights noted as the separate live-MVP feed.

diff_sha256: e6de1bb282bb2294a7b73ef9fe48be17ce243ef45ffb3fa72897f023ac2a3184

## scope-auditor
VERDICT: PASS
risks_checked:
- Mart-inventory accuracy: traced all explicit queries in export_site_data.py — 14 wired marts (mart_team_profile, mart_team_fixtures, mart_player_profile, mart_player_match_log, mart_team_momentum, mart_team_season_record, mart_fixture_standing_context, mart_head_to_head, mart_team_momentum_window, mart_player_momentum, mart_standings, mart_leaderboards, mart_team_fixture_stats, mart_player_fixture_stats) — cross-checked against the §3 ✓ rows; confirmed the orphan marts (mart_{team,player}_competition_benchmarks, mart_roster, mart_player_career) EXIST as model files but are NOT queried; confirmed the ✗ not-built marts (opponent-context, contribution-share) have no model file. Both prior findings fixed (count = 14; Match-preview corrected); the contract states 14 too (consistent).
- §10 decision boundary: the diff records factual STATUS only (built / wired / orphan / not-built) — it does NOT decide product/UX, screen specs, build schedule, or metric definitions; "⚠ orphan" is descriptive ("currently not wired"), not prescriptive. Whether/when to spec the orphan screens or build the Phase-D marts is reserved to the CPO. Scope is exactly docs/content_architecture.md + .claude/task/**.

## escalations
(none) — doc-only status reconciliation; records the verified current state and RESERVES (does not decide) whether/when to spec the orphan-mart screens, build the flagship marts, or run the broader wireframe doc-status sweep — all to the CPO.
