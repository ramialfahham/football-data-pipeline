# Review — feat/player-season-consolidation — 2026-06-17 (#480, narrow)

> Consolidates the three player-season aggregations onto one shared int
> (`int_player_season__metrics`); `mart_player_profile` + `mart_player_season` now COMPOSE it,
> inline aggregation removed. Profile byte-identical (faithful reproduction); season's pass accuracy
> corrected naive-avg → catalogue-weighted (an UNCONSUMED column). floor()→round() fix. Today's grain
> kept (per-club split deferred to §8.3). Reviewers: scope-auditor (always) + analytics-engineer (dbt).
>
> Re-spin: the first build failed CI on ONE test — the int's pass_accuracy_pct range test was written
> column-level (dbt_utils.expression_is_true prepends the column → invalid SQL); moved to model-level
> (the marts' working pattern). Everything else built green (PASS=580, incl. the (player_sk, season_sk)
> grain-unique + relationship tests). The branch was then collapsed to one commit (it had carried a
> rebase + a hash-rebind commit) so the staged diff == the PR diff == this hash. Both reviewers
> re-passed on the corrected diff.

diff_sha256: 6a2eac942503c08763869230cefaba1096bcd71fcd23a6d9325373a2e2b47765

## scope-auditor
VERDICT: PASS
risks_checked:
- pass_accuracy_pct numerical equivalence: the int computes passes_accurate =
  sum(round(passes_total*passes_accuracy_percent/100)) and passes_total = sum(coalesce(.,0)) — identical
  to mart_player_profile's removed inline agg; both marts now read the same safe_divide ratio →
  mart_player_profile byte-identical; only mart_player_season's (unconsumed) pass accuracy changes
  avg→weighted. mart_top_scorers reads goals/assists/shots_on_target etc., not the changed column.
- Grain uniqueness boundary (multi-competition player in one year): the new unique key (player_sk,
  season_sk) is at least as selective as the old (league_code, season_api_year, player_sk) — season_sk
  encodes one (league, season), so a player in two competitions yields two distinct rows; no collision.
  Narrow scope held (no per-club grain / side-by-side / appearance block); no §10 silently decided.

## analytics-engineer-reviewer
VERDICT: PASS
risks_checked:
- The CI-fix is a pure test-contract relocation, not a logic change: model-level
  dbt_utils.expression_is_true resolves pass_accuracy_pct as a column (the marts' valid pattern); the
  prior column-level form prepended the column → invalid SQL. Fires on the int's (player_sk, season_sk)
  grain — complete coverage; no value drift possible from the move.
- passes_accurate null-propagation (round(passes_total*pct/100) drops a per-fixture row when either
  input is null) is PRE-EXISTING — byte-identical to the removed mart_player_profile agg; the
  consolidation introduces no new drift. Byte-identity of mart_player_profile, consumed-column
  preservation in mart_player_season, layer compliance (int→core only; marts→int), and the
  grain/range/relationship tests all verified.

## escalations
(none)
