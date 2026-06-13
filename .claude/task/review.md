# Review — feat/dim-player-team-season — 2026-06-13

> PR A of the player-model redesign: add the rostered player↔team↔season mapping
> (additive). base_apif__player_team_season (2_base) + dim_player_team_season_mapping
> (3_core relationship/mapping dim) + tests + layering.md rule clause/inventory.
> Required reviewers for dbt_project/**: scope-auditor + analytics-engineer-reviewer.
> Three cold blinded iterations: iter-1 analytics FAIL (season-lookup fan-out on the
> untested league_code↔league_api_id 1:1) → fixed with a dedup-guard qualify. iter-2
> scope-auditor FAIL (per layering.md the attribute-less association does not earn dim_
> status; classification unsanctioned + inventory stale) → CPO ruling (escalations.log
> 2026-06-13): keep dim_ + _mapping suffix, extend layering.md to recognize a
> "relationship (mapping) dimension"; layering.md updated (clause + inventory).
> iter-3: both reviewers PASS against the hash below.

diff_sha256: bb3dbb3780d393246586d0c338ff62227b7aab0ff716249abae1e675191522fa

## scope-auditor
VERDICT: PASS
risks_checked:
- Classification authority (§10): the model is a many-to-many relationship, not an entity,
  so it failed layering.md's dimension-qualification rules in iter-2. Verified the resolving
  CPO ruling is RECORDED in .claude/task/escalations.log (2026-06-13) and that layering.md
  now carries a "relationship (mapping) dimensions" clause sanctioning it (exempt from the
  Entity + degenerate-dimension rules; still requires Reuse + Conformance + a tested unique
  grain key) plus the inventory row — so the classification is CPO-authorized and the doc is
  internally consistent, not a silently-taken decision. The contract amendment A1 records
  layering.md in scope with that authority.
- Scope + additive: every changed path is in scope_paths (incl. layering.md); no protected
  path touched; no existing MODEL SQL or consumer changed (dim_player, base_apif__players(_global)
  untouched — grep) — only new model files, appended yml test blocks, and the layering.md
  rule/inventory. Tests are real guards (PK not_null+unique, grain unique_combination, FK
  relationships), not decorative.

## analytics-engineer-reviewer
VERDICT: PASS
risks_checked:
- Season-lookup fan-out: the dim_competition_season CTE qualifies to one row per
  (league_code, season_api_year) (deterministic hash tie-break) BEFORE the left join, so even
  if the untested league_code↔league_api_id 1:1 were violated the join cannot multiply rows;
  the surrogate key is generated from the pts-side columns. No residual fan-out path; the
  player_team_season_sk unique test is safe. Base grain (league_code, player_id, team_id,
  season_year) is unique after its qualify (stg_apif__players is one snapshot per league).
- FK relationships (ci-data-build predictions): player_sk → dim_player PASS by construction
  (same stg_apif__players source, player_id not null; dim_player globally dedups it);
  team_sk → dim_team PASS by construction (roster /players fetched only for already-discovered
  team_ids after load_teams; dim_team unions /teams + fixture team_ids); season_sk/league_sk
  relationships correct as nullable (left join; test fires on non-null only). Layer-compliant
  (base=view reads stg; core=table reads base + dim_competition_season, qualify allowed, no
  stg/json/union_all); SK over (player_id,team_id,league_code,season_year) is bijective with
  the unique_combination test columns.

## escalations
(none — iter-1 fan-out fixed (dedup guard); iter-2 classification resolved by the recorded
CPO ruling + layering.md extension; both reviewers PASS in iter-3. DQ proof (FK relationships
across all leagues) runs in ci-data-build, the authoritative gate.)
