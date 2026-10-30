# Review — feat/235-team-page

diff_sha256: 8f1623b38b8941914e6c9cf5103b27def50c373933f2281704ba4c62c17eb15a

rounds: 3

## scope-auditor
VERDICT: PASS
risks_checked:
- Round 1 found four defects: content_architecture.md §4 still listed the old Team tabs; 11 and 14 read as live screens and metrics_display.md / 12_player_stats.md cited 14 as a rule carrier; the contract did not name where each reserved item was approved; the impact map lacked the cost per export run. Round 2: the Team rows read Overview, Matches and Performance; 11 and 14 open with a retirement note pointing to 02; the two strip-plot sentences point to 02; the amendments name each approval and add the four documents and .gitignore to scope_paths; the impact map states the cost per run (dim_competition_season billed 10 MB, the fixtures read whole either way, the export started by hand). No defect.
- Every file in the patch is inside scope_paths, and the ordering moved from the export to mart_team_fixtures (merged on main), so the export selects and derives nothing.
- Round 3 (gen_team_mock.py lint cleanup only): in scope; output kept byte-identical, so no new copy, page, metric, URL or mechanism; no network, process, environment or credential reach added. No defect.

## analytics-engineer-reviewer
VERDICT: PASS
risks_checked:
- Round 1 failed the Python sort of the mixed-competition schedule and the Results window. Round 2: `_team_schedule` lists rows in the mart's served `upcoming_order` and `result_order` (mart_team_fixtures.sql, with tests in shared.yml for nulls, positivity and uniqueness); the `season_api_year == featured year` filter is a selection on served columns, as in the competitions block. No defect.
- Tests: the schedule test feeds orders that disagree with the kick-offs and asserts the served order wins; a fetch test pins the season label read. Samples (165.json) list matches in served order with no order key in the payload.

## bi-analyst-reviewer
VERDICT: PASS
risks_checked:
- Round 1 failed four points: the rendered evidence covered another change; clean sheets showed the count, not the locked share; the competition filter left an empty section heading; run labels at one match. Round 2: rendered_page_evidence.md holds measured values at 280, 375 and 1100px; teamBinding in metricRows.ts binds the slot to clean_sheets_pct with its label and "percentage" line ("Clean sheets · percentage 29%, 5th"); sections carry data-slots and hide when they hold none of the chosen competition; runs are NULL below two matches in the mart. No defect.
- The squad grid is capped at two columns (one at 280 and 375px, two at 1100px), matching the design and the block standard row.

## platform-reviewer
VERDICT: PASS
risks_checked:
- Round 1 found a hard-coded repo path in gen_team_mock.py, an unignored `design-mocks/_astro/` copy, an unpinned season-label fetch, and an untested builtPlayers reader. Round 2: REPO derives from `__file__`; `.gitignore` ignores `design-mocks/_astro/`; a fetch test asserts `season_label` from dim_competition_season; builtPlayers.test.mjs covers a player on two boards, a row without an id and the empty case. No defect.
- The schedule test would fail if a kick-off sort returned; teamBinding's label stays required by the label tests; the bound rows are filtered before lookup, so a season without clean_sheets_pct cannot crash the build.
- Round 3 (gen_team_mock.py, the 28 ruff findings): `import csv` at the top, the five assigned lambdas as nested defs, the unused locals and the computations only they fed removed, `l` renamed. Ruff passes; no removed name is still referenced; the generated team.html is byte-identical from the same build. Round-2 fixes (REPO from `__file__`, the `_astro` ignore) intact. No defect.

## escalations
(none)
