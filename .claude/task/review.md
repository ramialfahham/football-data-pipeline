# Review — fix/remove-unapproved-performance-gap — 2026-06-23

> CPO-ordered removal of the uncatalogued, unapproved `performance_vs_results_gap` metric
> (= shot_share_season − points_capture_season) from mart_team_profile. Surgical: one
> derived column + its yml column-doc + its range test + the "deserved vs actual" doc
> framing. The two catalogued input metrics (shot_share_season, points_capture_season) are
> retained; metric_catalogue.csv untouched.

diff_sha256: 86bca24ed6b45884f4e0ab3d264410466d09d494694c42f5609ef303c5a8bc6a

## scope-auditor
VERDICT: PASS
risks_checked:
- Scope creep on the catalogued inputs: verified shot_share_season + points_capture_season remain in the SELECT and keep their range tests; metric_catalogue.csv is untouched. Removing them would have been a silent §10 change beyond the CPO's surgical order.
- Incomplete/inconsistent removal: verified the removal is complete and consistent across the SQL (column + comment + header doc), the yml (range test + column doc + description reframed), with zero remaining references in dbt_project/ or scripts/; the redesign is correctly reserved as a separate thread (not smuggled into a removal PR).

## analytics-engineer-reviewer
VERDICT: PASS
risks_checked:
- SQL last-SELECT-item validity: the removed expression was the final SELECT column; post-removal `s.scoring_run` is the new final item with no trailing comma, immediately followed by `from metrics as m` — syntactically valid (model builds, 9 tests pass).
- Downstream export breakage: `scripts/export_site_data.py:342` does `select *` and never names the dropped column (grep: 0 hits in scripts/), so the payload loses one key silently with no consumer break; mart_team_profile is a leaf (no dbt downstream).
- NOTE (non-blocking, deferred): stale references remain in docs OUTSIDE scope — `docs/content_architecture.md` (still claims the team deserved-vs-actual is "Built"), `docs/wireframes/02_team_profile.md`, `docs/audits/2026-06_alignment_audit.md`. Not executable, not in scope_paths/done_when; to be handled in the deserved-vs-actual redesign thread.

## escalations
(none)
