# Review — refactor/dim-player-pure-entity — 2026-06-13

> PR B of the player-model redesign: make dim_player a pure global entity (drop
> league_code + last_known_*), collapse base_apif__players into one global dedup
> (grain player_api_id, ordered source_priority asc then raw_ingested_at desc), and
> DELETE base_apif__players_global. No consumer repointing needed (verified: no mart/
> export uses dim_player.league_code or last_known_*). Required reviewers for
> dbt_project/**: scope-auditor + analytics-engineer-reviewer. Both PASS first iteration.

diff_sha256: f92b450a3826854eda08528b746049a73960901e8a9fa5455f92cf7f3cf2f84d

## scope-auditor
VERDICT: PASS
risks_checked:
- Consumer-impact honesty (breaking change): independently grepped 4_intermediate, 5_marts,
  and scripts/export_site_data.py — confirmed no consumer selects dim_player.league_code or
  last_known_*; marts pull league_code from facts and only name/photo/bio from dim_player, and
  there are zero last_known references downstream. The contract's "no repointing needed" claim
  holds; dropping those columns + collapsing the grain breaks nothing.
- Dedup mechanism vs recorded design + scope: the memory (project-player-model-redesign)
  authorizes the GOAL ("dedup picks the best name/identity source by authority"); the
  source_priority-asc-then-recency ordering is the codified mechanism implementing that goal,
  not a new §10 decision — and it is bounded by the not_null(player_name) DQ test (the contract
  defers proof to ci-data-build with an explicit escalate-on-new-failure clause). Diff touches
  only declared scope_paths, no protected path, no remaining ref to the deleted players_global;
  layering.md inventory row updated (dim_player now a pure global, not-league-scoped entity).

## analytics-engineer-reviewer
VERDICT: PASS
risks_checked:
- Grain/uniqueness + not_null(player_name): the new qualify (partition by player_api_id) yields
  exactly one row per player_api_id → player_sk not_null+unique holds; the base grain test is
  updated to [player_api_id]. The single dedup ordered by source_priority FIRST is strictly
  superior to the old players_global recency-only collapse — a player with a priority-1 /players
  row in ANY league now wins globally rather than losing to a fixture-only row from another
  league — so it can only preserve or improve name quality, never add nulls (transfers, the prior
  null-name source, is already gone via #446). ci-data-build predicted PASS.
- FK integrity + dangling refs + layer: every surviving ERROR-severity relationship into
  dim_player (fct_fixture_player_stats.player_sk, fct_fixture_event.player_sk [where not null],
  dim_player_team_season_mapping.player_sk) still resolves — dim_player is composed from the same
  three sources (/players, fixture_players, fixture_events) that produce those player_sks; the
  fct_fixture_event nullif(player_id,0) and the fixture_events_src !=0 filter are symmetric.
  base_apif__players_global deleted with zero remaining ref(); base reads stg+base, core reads
  base only (layer-compliant); base=view, dim=table materialisation correct.

## escalations
(none — both reviewers PASS first iteration. DQ proof (grain uniqueness, not_null(player_name),
FK relationships across all leagues) runs in ci-data-build, the authoritative gate; the contract
reserves an escalate-on-new-failure path.)
