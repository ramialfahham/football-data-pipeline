# Review — claude/297-players-to-watch-bbb7cc — 2026-11-21

diff_sha256: 915dc46728366b30c007c7135d32f1faaef59aaeeccd4931a95d3d449e6f38cb

rounds: 3

Rounds: round 1 passed on the analytics engineer; the scope auditor escalated the English article rule and the Statistics-tab intro change, the CTO failed the design-inventory pins that rose above main's, the BI analyst failed the missing rendered evidence and the "last season" label over a this-season side, and the platform reviewer failed the phone test's glob, the stale README matchday count and the 592px switch. Round 2 is the delta: the English article rule and the Statistics-intro change were reverted (the Finnish inessive stays on the Players to watch intro only), the mixed-window intro was added as fan wording before go-live (the coordinating session's call), the guard scripts were fixed on main and the baselines now only fall, the phone glob moved to a next-round match, the README count was corrected and the rendered evidence was written; all four reviewers passed. Round 3 is two contract lines (the baseline sentence made accurate, an empty bullet removed); the scope auditor passed it.

## scope-auditor
VERDICT: PASS
risks_checked:
- The round-1 escalation does not stand: inCompetition and the Statistics-tab intros are as on main; the Finnish inessive applies to the Players to watch intro only and cites a named, dated approval.
- The mixed-window intro is fan wording before go-live, recorded in decisions_taken as the coordinating session's call of 21 Nov 2026; no decision reserved to the CPO is newly taken.
- The two contract lines of round 3 against the design-inventory diff: each baseline changes one value, the Match page scroll pin, and it falls; the new sentence is accurate.

## analytics-engineer-reviewer
VERDICT: PASS
risks_checked:
- shape_players_to_watch selects by the mart's scorer_points_rank and ball_actions_per90_rank and does not rank, tie-break or derive a window (A5); outfield-only, ties and window are enforced in mart_player_season_record.
- The fetch query names columns that exist in the mart; board names and formats come from metric_catalogue.csv through _board_catalogue; no seed or dbt model changes; the impact_map pastes the leaf result of dbt ls.
- scripts/export_site_data.py and tests/test_export_site_data.py are unchanged since this pass.

## platform-reviewer
VERDICT: PASS
risks_checked:
- tests/test_phone_built_pages_231.py now reaches the Bayern München v 1. FC Köln next-round page, which carries the block, so the phone rules run on it at 260-768px in EN, DE and FI.
- site_v2/src/data/README.md says nine matchdays played, matching the sample; the other counts agree with the files.
- The three design baselines differ from main only by falling Match page scroll pins; the chart screenshot manifest changes only the three scatter-375 hashes its amendment names; no hook, workflow, requirements, package or credential change.

## bi-analyst-reviewer
VERDICT: PASS
risks_checked:
- rendered_page_evidence.md exists and covers 280, 375, 575 and 1010px with the instrument named; the two boards, 12 rows, no overflow, split level at 1010px.
- A mixed pair of windows now picks playersIntroMixed, only two last-season sides pick playersIntroPrev; the EN, DE and FI texts match the contract word for word.
- Every rendered field traces to the export; board names resolve in all three languages; no percentage, tier or extra metric; the German "Vorsaison" intro and the Ball actions per 90 format stay reserved.

## cto-reviewer
VERDICT: PASS
risks_checked:
- The three baselines change one value each, the Match page scroll pin, and each falls; no pin rises and no guard is relaxed.
- docs/design/components.yml is the only guard path touched; protected_override names dated approvals and impact_map is filled in.
- No new mechanism, dependency, run cadence or credential; the export keeps one query against an existing mart.

## escalations
(none)
