# Review — feat/leaderboards-rate-boards — 2026-06-23

diff_sha256: e229ba1316afbc3cf0270370d693d7dda3981b2a7db38999fb95d58c6bf4112b

## scope-auditor
VERDICT: PASS
risks_checked:
- Downstream column isolation — `int_player_season__metrics` gains one column (`finishing_efficiency`); verified `mart_player_profile` and `int_player_career__metrics` use named SELECTs (not `select *` in their final), so the new column does not leak — their schemas and numbers are unchanged. Edits stay strictly within `scope_paths`; no §10 decision taken unilaterally (the metric extension, the qualification rule, and the i18n key are all recorded in `decisions_taken`).
- sort_value INT64→FLOAT64 widening + export boundary — verified the export (`scripts/export_site_data.py`) filters `metric_key` to `_LEADERBOARD_METRICS` (the 9 count boards only); the 5 rate keys are NOT added, so the live export is unchanged; count-board `sort_value` is JSON-numeric-equal (25 ≡ 25.0). Export wiring honestly deferred (#391). impact_map matches the actual files.

## analytics-engineer-reviewer
VERDICT: PASS
risks_checked:
- Unified-loop refactor correctness — verified the two loops were merged into one `boards` list (9 count + 5 rate = 14) ranked by a single loop with `{% if not loop.last %}union all{% endif %}`: compiles to exactly 14 branches / 13 `union all`, no dangling union; each WHERE is correct (count `key > 0`; rate `minutes >= 270 and <scope> and key > 0`; finishing adds `shots_on_target >= 10`; save is GK-only). The prior hidden "rate_boards non-empty" invariant is removed.
- Catalogue drift guard + range tests — `finishing_efficiency` column in the int model is non-exempt and normalises to `finishing_efficiency`; the new `(entity='player', metric_id='finishing_efficiency')` catalogue row satisfies `assert_no_uncatalogued_season_metric`. The 4 bounded-rate [0,1] tests are added; `finishing_efficiency` is correctly EXCLUDED (uncapped — a real 3-goal/2-SoT player-season exists). Mart SELECT matches the documented `shared.yml` column set; grain `(player_sk, season_sk, metric_key)` holds.

## football-analytics-expert-reviewer
VERDICT: PASS
risks_checked:
- Uncapped / >100% mechanism — the description now states a verified, mechanism-neutral condition ("rarely the source logs more goals than on-target shots ... can exceed 100%"), replacing the wrong "penalties" claim; matches the live data (1 breach in 11,809 player-seasons; 0 above the SoT>=10 board floor) and `safe_divide` null-on-zero behaviour. `goals / shots_on_target` is a sound player finishing definition; `lower_is_better=false` correct.
- Coverage-gap disclosure — "inherits player-stat coverage gaps, like the other player rates" is accurate and correctly framed as a shared property of all player rate metrics, not finishing-specific. SoT>=10 board floor defensible (a leaderboard qualification, kept out of the catalogue definition).

## escalations
(none)

## post-review delta (transparency)
The cold blinded review ran on staged hash
`cf42f9bbf62ed2fd9fe57fd635a1a9c8f14e08994f550898158d03cdc4429e51`
and returned the three PASS verdicts above. The football-analytics reviewer noted one non-blocking
residual: the SQL comment in `int_player_season__metrics.sql` still carried the stale "penalties can
exceed 100%" wording it had asked be corrected in the catalogue. That comment was then aligned to the
verified mechanism-neutral wording — a 2-line, semantically inert change with no effect on SQL
behaviour, layer rules, scope, metric definition, or any risk the reviewers assessed. The final staged
diff (`e229ba13...`, recorded in `diff_sha256` above) differs from the cold-reviewed diff ONLY by that
reviewer-requested comment correction. The verdicts therefore bind unchanged.
