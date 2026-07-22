# Task contract — deserved vs actual: domestic leagues only, expressed in points

> Written on a CLEAN tree (branch `feat/deserved-vs-actual-in-points` off main @ 6eeef22).
> Two defects in one model, fixed together because they are the same block of SQL.

objective: >
  (1) RESTRICT the read to domestic leagues. `deserved_rank` ranks every team in a competition
  1..N, but a group-stage tournament's actual standing is a position WITHIN a group (1..4). The
  two are not comparable, so every tournament team carries a large false gap. Measured on the live
  mart: mean absolute rank gap is 3.43 for domestic leagues against 8.29 continental_championship,
  13.87 continental_club, 21.02 qualifying and 21.46 world_championship, over 224 non-domestic
  team-seasons. The existing gate assumed knockout competitions carry no standing and would drop
  out on their own; group-stage ones DO carry standings, just not comparable ones, so the gate
  checks that a position EXISTS rather than that it is the same KIND of number.

  (2) EXPRESS the read in points instead of rank. A fitted line in rank space can predict
  positions that do not exist, which is exactly why the approved team-page mock's hero draws 0.4
  and 21.3. Points space has no such defect. Re-run over 91 domestic league-seasons / 1,790
  team-seasons: `sot_difference_per_match` versus points is Pearson +0.84 (0.85 balanced, 0.83
  unbalanced), and the slope gives the first fan-readable magnitude this metric has ever had --
  one extra shot on target of difference per match is worth about 0.25 points per match, near 9.8
  points over a 38-game season.

  Honest counter-result, stated because a reviewer will ask: goal difference correlates +0.96 with
  points, far higher. But points are computed from those same goals, so it is near-tautological and
  cannot serve as a DESERVED (non-outcome) signal.

refs: >
  Verified this session against the live warehouse and the real tree, not recalled:
  - `int_team_season__metrics` already carries `points_won_sum_season` and `season_games_played`
    (confirmed by `mart_team_season.sql:34,40` reading exactly those two), and this model ALREADY
    refs it for `sot_difference_per_match`. The points inputs therefore cost no new `ref()`.
  - The domestic filter pattern already exists at `int_team_profile__yoy.sql:34-49`
    (`ref('competition_registry')` + `where r.competition_type = 'domestic_league'`). Reused, not
    invented.
  - The minimum-games threshold `>= 3` already exists at
    `int_team_competition_benchmark_metrics_long.sql:18`. Reused, not invented. Verified sufficient:
    at `>= 3` the out-of-range count is 0 and higher thresholds (5, 8, 10) buy nothing.
  - `assert_no_uncatalogued_season_metric` scans `int_player_season__metrics`,
    `int_player_club_season__metrics` and `int_team_season__metrics` -- NOT this model -- so the two
    new catalogue rows need no column on the season metrics model, exactly as `deserved_rank` and
    `sot_rank_gap` do not today.
  - `artifacts/site_data/**` greps positive for these columns but is GITIGNORED (`.gitignore:234`,
    `git ls-files artifacts/` returns 0). It is local export output, not repo content. No action.

scope_paths:
  - dbt_project/models/4_intermediate/domestic_league/team_season/int_team_season__deserved_vs_actual.sql
  - dbt_project/models/4_intermediate/domestic_league/team_season/int_team_season.yml
  - dbt_project/models/5_marts/shared/mart_team_profile.sql
  - dbt_project/models/5_marts/shared/shared.yml
  - dbt_project/seeds/metric_catalogue.csv
  - dbt_project/seeds/schema.yml
  - dbt_project/tests/assert_metric_catalogue_expr_resolvable.sql
  - .claude/active_work.md
  - .claude/task/escalations.log

impact_map: >
  writers: `int_team_season__deserved_vs_actual` only. No raw table, no loader, no ingestion path,
    no new source. The model is `materialized='table'`, not incremental, so no
    `--full-refresh` rename hazard applies.
  downstream: dbt lineage could NOT be run -- the dbt CLI is broken locally and the dbt MCP server
    is not connected, so this is enumerated from the real tree by grep over `dbt_project/` for BOTH
    models AND tests (the method fix banked from #804, whose impact_map missed a test consumer by
    grepping only `models/`). Every hit, verbatim:
      `models/5_marts/shared/mart_team_profile.sql:54` -- the ONLY `ref()` to this model anywhere.
      `models/5_marts/shared/shared.yml:261,314,316` -- column docs.
      `models/4_intermediate/.../int_team_season.yml:143` -- this model's own schema block.
      `models/4_intermediate/shared/int_player_profile__contribution.sql:20` -- a COMMENT mentioning
        the model by name; no ref, no dependency. Untouched.
      `tests/assert_metric_catalogue_expr_resolvable.sql` -- a COMMENT naming the blank-
        base_relation rows. Keys on `base_relation` being blank, never on the metric names, so its
        LOGIC is unaffected; the comment is corrected so it does not name a deleted row.
      `seeds/schema.yml:110,173` -- two prose claims naming the columns, one of them a COUNTED claim
        ("applies to exactly two"). Both corrected.
    NO frontend consumer: `site_v2/**` does not reference any of these columns, so nothing rendered
    changes. Nothing displays deserved-vs-actual today.
  layer_rules: intermediate composes intermediate and a seed; the mart selects passthroughs and
    derives nothing (consumption-layer contract). `python scripts/check_layer_contract.py` is the
    CI-enforced check and is run before commit.
  deploy_order: shared CI/prod datasets, so the model rebuilds in place on merge. `mart_team_profile`
    LOSES the `sot_rank_gap` column and GAINS two, which is a breaking schema change for any reader
    of that column -- there are none outside this repo, and none inside it after this commit. The
    04:00 UTC nightly rebuilds both models in dependency order; no manual sequencing needed.
  blast_radius: BOUNDED and measured against the live warehouse, not asserted.
    Before: 1,376 rows carry a deserved value -- 1,152 domestic and 224 non-domestic.
    After (prototyped as the exact final SQL against `intermediate.*` before writing the model):
    1,152 rows, all domestic, across 55 league-seasons. So the change REMOVES 224 misleading rows
    and preserves every legitimate one. Zero domestic rows are lost to the new games gate.

decisions_taken: >
  Five CPO rulings, all 2026-07-22, all via AskUserQuestion, all recorded in `escalations.log`
  BEFORE this contract was written:
  (1) "Deserved total points" -- the read is expressed in deserved TOTAL points, replacing rank as
      what the block communicates.
  (2) "Keep rank, derived from deserved points" -- `deserved_rank` survives but is re-derived by
      ranking `deserved_points`, so rank and points cannot disagree.
  (3) "actual minus deserved, negative = under" -- the gap sign convention. This is the OPPOSITE of
      the rank gap it replaces, which is why ruling (5) removes that rather than leaving both.
  (4) "deserved_points and sot_points_gap" -- the two metric ids. The `sot_` prefix stays accurate
      because deserved points is fitted FROM `sot_difference_per_match`.
  (5) "Drop the rank gap, keep one gap in points" -- `sot_rank_gap` is deleted from the model, the
      mart, both schemas and the catalogue.
  (6) "Whole points, integer" -- the display format for both new metrics.
  Taken by the builder, mechanically and NOT as judgement calls, because a guard forces them:
  `assert_metric_direction_lower_is_better_agree` requires `neutral` to pair with
  `lower_is_better = false`, so `sot_points_gap` is (neutral, false) exactly as `sot_rank_gap` was,
  and `deserved_points` is (higher_better, false).

decisions_reserved:
  - Whether a tournament-appropriate deserved-vs-actual is ever built. CPO 2026-07-22 said it
    "should be possible ... but let's skip for now", so it is wanted and explicitly NOT designed
    here. This task must not attempt one.
  - What the hero block actually looks like. This task changes only what the warehouse emits. The
    design is owed to the CPO as a PICTURE, never as prose, and is the next task.
  - Amending the locked display contract (`docs/wireframes/metrics_display.md`) to carry these
    metrics. Recorded as owed; out of scope here.

done_when:
  - `int_team_season__deserved_vs_actual` emits rows for domestic leagues ONLY, verified by a data
    test that joins every row's `league_code` to the registry, not by trusting the join.
  - No `deserved_points` falls outside `[0, 3 * season_games_played]`, enforced by a data test.
    Prototyped: 0 violations over 1,152 rows.
  - `sot_points_gap` is null exactly when `deserved_points` is null, else exactly
    `points_won_sum_season - deserved_points`. Pins the inverted sign convention.
  - `deserved_rank` reproduces the PREVIOUS ordering in every balanced league-season. Prototyped:
    0 drift over 43 balanced league-seasons. It diverges in 141 mid-season rows, which is the
    intended correction (the real table rewards games played; the old rank ignored them).
  - `sum(sot_points_gap)` within a league-season is EXACTLY 0 in a balanced season (prototyped:
    max absolute 0.0 over 43) and approximately 0 mid-season (prototyped: mean 3.9, max 9.6 over
    12), because each team's prediction is scaled by its own games played.
  - `python scripts/check_layer_contract.py` passes; both touched schema files parse as YAML;
    catalogue integrity holds (no duplicate id-entity pair, every row carries direction and
    interpretation).
  - ONE commit, pushed with an explicit refspec, PR opened. The CPO merges.

amendments:
  - 2026-07-22: DESERVED_RANK GAINS A SECOND GATE. No path added; no §10 decision taken.
    AUTHORITY: **CPO, AskUserQuestion 2026-07-22: "Withhold all three, from all four"**, to a
    discrete question offering three paths (withhold from all four / keep the points read for MLS /
    park the change until a continuity signal exists). Recorded in `escalations.log`.
    THIS AMENDMENT FIRST CLAIMED SOMETHING WEAKER AND WAS WRONG TO: that the CPO's already-recorded
    reasoning for excluding tournaments ("not comparable, so do not show it") covered this case by
    application rather than extension. The scope-auditor FAILed that, and correctly: §10's meta-rule
    says that when a case does not clearly match a written rule the CLASSIFICATION is itself the
    CPO's decision, and "it is analogous to X" is not a licence. He ruled "domestic leagues";
    narrowing that set is his. This is the THIRD §10 misclassification of the same shape in one day,
    after the metric rename and the review routing. The correction is recorded here rather than
    silently overwritten, because the pattern matters more than the instance.
    THE FINDING, and it is the same class this task exists to fix: restricting to
    `competition_type = 'domestic_league'` is sufficient for a POINTS comparison but NOT for a RANK.
    Some domestic leagues do not run one table either -- MLS ranks within Eastern/Western
    conferences, and the Apertura/Clausura formats split a season -- so `actual_rank` restarts at 1
    per section. A competition-wide 1..N `deserved_rank` then has no counterpart, which is exactly
    the "a position EXISTS but is not the same KIND of number" defect quoted in this contract's own
    objective. I fixed the instance (tournaments) and missed the class (non-comparable tables).
    MEASURED, not argued: 9 of the 55 fittable league-seasons and 232 of the 1,152 rows -- MLS, LMX,
    APD, J1. Roughly one row in five would have shipped a non-comparable rank.
    THE REVIEWER'S EVIDENCE WAS PARTLY WRONG AND ITS CONCLUSION STILL RIGHT, recorded because the
    distinction matters: it argued from `group_description` carrying several values per
    league-season. That column holds QUALIFICATION ANNOTATIONS ("Champions League", "Relegation"),
    so it is multi-valued for single-table leagues like the Premier League too and proves nothing.
    The defect was confirmed instead by the decisive property -- whether `actual_rank` is a 1..N
    permutation -- which is also what the fix now tests.
    THE FIX IS THE PROPERTY, NOT A LEAGUE LIST: `actual_table_is_single_ladder`
    (`count(distinct actual_rank) = count(*)` per league-season). A league list would need editing
    every time a conference league is onboarded, breaking the zero-file rule.
    IT GATES ALL THREE OUTPUTS, and the first attempt at this amendment was WRONG to gate only the
    rank. That version argued points stay comparable even where table position does not. True for
    MLS -- one continuous season, and its own Supporters' Shield compares points across conferences
    -- and FALSE for Apertura/Clausura, where one `season_sk` spans two separate competitions whose
    points reset, so `points_won_sum_season` sums across both. VERIFIED, after the claim was
    challenged: APD 2025 carries 30 teams, a 15-position standings table, and 32-37 games per team,
    which is a whole calendar year of two tournaments. A deserved-points total there is a figure
    nobody tracks. Telling MLS apart from Liga MX needs a real "is this one continuous competition"
    signal that does not exist and would be a design decision, so this errs toward WITHHOLDING, at
    the known cost of a read MLS could probably support. Recorded as owed.
    CONSEQUENCE for the guards: because the condition now sits inside `league_season_fittable`,
    `deserved_points` and `deserved_rank` null together again, so the BICONDITIONAL test is
    RESTORED. It had briefly been replaced by a one-directional version, which left `deserved_rank`
    with no positive-existence guard at all -- the column could have gone silently empty with every
    test still green (analytics-engineer-reviewer). A test may become NARROWER when a change makes
    it partly untrue; it must never become SHORTER. A second test asserts the single-ladder
    condition held, rather than trusting the gate to have applied it.
    RE-VERIFIED against the live warehouse: 920 rows over 46 league-seasons (down from 1,152 over
    55, the 232 non-single-ladder rows now withheld entirely), 0 violations on every test including
    the restored biconditional, and the gap still sums to exactly 0 across a balanced season.

  - 2026-07-22: the same reviewer's secondary note, accepted. The catalogue descriptions enumerated
    the null conditions but omitted the `safe_divide` path -- a league-season whose signal has no
    spread yields an undefined slope, not a flat one. Added to all three descriptions and to the
    model comment. It produces a correct NULL rather than a wrong value, so this was documentation
    accuracy rather than a defect.
