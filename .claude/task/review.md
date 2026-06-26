# Review — refactor/500-drop-season-suffix — drop the `_season` suffix from season metric columns

> G3 Lock artifact. Reviewers spawned cold (blinded) on the staged diff (`.claude/task/review_input.patch`).
> Required set: dbt_project/** → analytics-engineer; docs/wireframes/** → bi-analyst; always → scope-auditor.
> #500 PR-d step 5 / Stage 2. dbt parse (via dbt MCP) = OK.
>
> POST-REVIEW DELTA: after the first 3-PASS review, CI's SQLFluff lint flagged 21 × AL09 ("column should
> not be self-aliased") — the rename had produced `m.<metric> as <metric>` / `goals_penalty as goals_penalty`.
> A follow-up de-alias fix (`m.<metric> as <metric>` → `m.<metric>`; `goals_penalty as goals_penalty` →
> `goals_penalty`) in the two already-in-scope files (int_team_season__metrics.sql, mart_team_season_record.sql)
> resolved all 21 (0 remain). Local sqlfluff couldn't run (needs the warehouse templater). scope-auditor +
> analytics-engineer RE-RAN on the full amended diff (below). bi-analyst PASS CARRIED FORWARD — its surface
> (the team-season page reads + the wireframe doc) is byte-unchanged by the SQL de-alias.
> (Note: `git grep -c "_sum_season"` now returns 53 — the extra is a COMMENT mentioning "_sum_season", not a column.)

diff_sha256: 870f894aaf2d27f26cc755937336d19ed0138c779cdc3236e476f719b8ad25e6

## scope-auditor  (re-run on amended diff)
VERDICT: PASS
risks_checked:
- Metric vs intermediate distinction: renamed metric columns cleanly separated from the preserved
  `*_sum_season` intermediates (zero metric `_season` patterns remain; 52 sum columns + 1 comment = 53). The
  DQ test validates metrics against their sums; the drift-guard strip is now a defensive no-op. No column masked/lost.
- De-alias behaviour-preservation + scope: `m.<x> as <x>` → `m.<x>` and `goals_penalty as goals_penalty` →
  `goals_penalty` both output the same column; zero self-aliases remain; the `m.<sum>_sum_season as <clean>`
  legitimate renames left intact. The fix touched only the two already-in-scope files (no scope expansion).
  metric_catalogue.csv untouched; export uses SELECT *; no new §10.

## analytics-engineer-reviewer  (re-run on amended diff)
VERDICT: PASS
risks_checked:
- De-alias output-name preservation: int_team_season__metrics.sql L74-75 are bare column refs (output names
  unchanged); goals_open_play (L76) is a computed expression with a legitimate alias; mart_team_season_record.sql
  L73-91 are bare `m.<metric>` pulls — zero AL09 self-aliases survive in either file.
- Rename completeness across the DAG: grep over all dbt model SQL for `_season` returns only `_sum_season`
  intermediates, structural names (mart_team_season, points_this_season YoY), and comments — zero live metric
  `_season` aliases. The benchmark macro pairs are now (X, X); int_/mart_team_competition_benchmarks inherit via
  the macro. The DQ consistency test refs the renamed metrics + the preserved `_sum_season` denominators (same-window).
- `clean_sheets_sum_season as clean_sheets` (mart_team_season_record L72) is a PRE-EXISTING design (the W2 mart
  surfaces a count, not the rate) — unchanged by this PR; the rate metric clean_sheets is not selected there, no collision.
escalations: none

## bi-analyst-reviewer  (PASS carried forward — page + wireframe doc byte-unchanged by the SQL de-alias)
VERDICT: PASS
risks_checked:
- Page/mart lockstep — all 11 rendered metric reads: every `row.<key>` the team-season page reads
  (goals_per_match … save_ratio) exists verbatim in mart_team_season_insights' SELECT; a site-wide grep for
  `row.<x>_season` returns ZERO — no stale read remains.
- `_sum_season` preserved + no value change: the suffix dropped only from metric columns; the raw totals are
  intact + still selected; no label/format/computed value changed (key rename only). The remaining `_season`
  tokens in the wireframe doc are non-metric YoY/coverage keys, not display metric keys.

## escalations
(none)
