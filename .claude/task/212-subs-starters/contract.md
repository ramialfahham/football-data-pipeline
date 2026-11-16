# Task contract — season starts and substitute appearances from the checked team sheets

objective: >
  Issue 212: a player's season starts and substitute appearances read the provider's stat line,
  which files bench players as starters. Where a confirmed or researched team sheet names the
  player, the player-match leg takes "on the bench at kick-off" from that sheet, as the match page
  (mart_player_fixture_stats) already does; elsewhere the stat line stands. A start stays a match
  with minutes > 0 and not on the bench, so starts plus substitute appearances still equal
  appearances.

refs: >
  Issue 212. Requested by the coordinating session; go-live gate issue 290. The rule is the
  approved Line-ups line of cleaning_rules.md (checked or researched sheets are the line-ups shown)
  and the doc block is_substitute__fixture already published for the match page.

scope_paths:
  - dbt_project/models/4_intermediate/shared/int_legs__player_match.sql
  - dbt_project/models/4_intermediate/shared/int_legs.yml
  - dbt_project/models/docs/shared_columns.md
  - dbt_project/tests/assert_player_leg_bench_follows_checked_sheet.sql
  - dbt_project/tests/assert_player_season_starts_from_checked_sheets.sql
  - .claude/task/212-subs-starters/contract.md
  - .claude/task/212-subs-starters/review.md
  - .claude/task/212-subs-starters/review_input.patch

impact_map: >
  writers: int_legs__player_match is written only by its own model; it reads
  fct_fixture_player_stats and fct_fixture, and gains a left join to fct_fixture_lineup
  (lineup_state confirmed or researched). Measured on prod 16 Nov: 0 duplicate
  (fixture_sk, player_sk) among those sheet rows out of 2,266,246, so the join cannot fan out.
  downstream: `dbt ls --select int_legs__player_match+ --resource-type model` lists 50 models,
  among them int_player_season__metrics, int_player_club_season__metrics, mart_player_profile,
  mart_player_career, mart_player_index, int_player_match__metrics and the team models built from
  player legs. Only int_player_season__metrics and int_player_club_season__metrics read
  is_starter or is_substitute from the leg (grep of dbt_project/models for both columns), to count
  starts and substitute_appearances; mart_player_profile carries those two columns.
  layer_rules: intermediate reads core only (fct_fixture_lineup is core); no partition_by or
  cluster_by; no per-competition file.
  deploy_order: none needed; the change is one model's projection, rebuilt by the next nightly
  after merge.
  blast_radius: starts and substitute_appearances of every player-season or player-club-season
  with a checked sheet that disagrees with the stat line. Measured on prod 16 Nov: 31,936
  player-match rows where a checked sheet puts the player on the bench while the stat line makes
  him a starter, concentrated in seasons 2016-2019 of the big five and the current season of
  UCL, UEL, MLS, KL1, LMX and J1. Appearances and minutes do not change. The MR comparison lists
  every changed player-season.

approved_design:
  - none: no page output changes; starts and substitute appearances change value, not display.

depends_on:
  - none: no MR is open on 16 Nov (glab mr list), and the change needs only main.

shared_files:
  - none: no design baseline, chart manifest or chart pin changes.

decisions_taken: >
  The checked team sheet decides who was on the bench, as on the match page; this is the fix the
  coordinating session ordered for issue 212 on 16 Nov, under the approved Line-ups and
  researched-sheet rules of cleaning_rules.md. is_starter on the leg keeps its published
  definition (minutes > 0 and not on the bench), so no start is counted without pitch time and the
  starts-plus-substitutes test still holds. A sheet starter with no minutes is therefore a starter
  on the match page but not a season start, as an appearance needs pitch time. The starts and
  substitute_appearances descriptions in shared_columns.md gain the same sheet-first sentence the
  match page's is_substitute__fixture already carries. No new mechanism, no new model, no recurring cost;
  read-only BigQuery only.

decisions_reserved:
  - none: the rule is the coordinating session's order on approved cleaning rules; no label,
    metric id or display changes.

done_when:
  - assert_player_season_starts_from_checked_sheets passes in data:build:mr (D. Ings, Premier
    League 2019, Southampton: 32 starts, 6 substitute appearances, 38 appearances, hand-worked from
    the raw sheets; the stat lines give 36 starts). A finished season, so the value cannot move.
  - assert_player_leg_bench_follows_checked_sheet passes in data:build:mr.
  - python scripts/ci_local.py --mr is green before every round and push.
  - The MR pipeline is green, including data:build:mr.
  - A read-only comparison of the ci_mr tables against prod (under 20 GB) lists every
    player-season whose starts or substitute_appearances changed, posted on the MR.

amendments: (none)
