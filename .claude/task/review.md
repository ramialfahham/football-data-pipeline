# Review — feat/player-core-bio-appearances — 2026-06-16

diff_sha256: 379cc15f21a393f04ec900a41101ca0cf753068b15b14c8d8763855db63c488b

PR-b reduced to BIO ONLY — the player-season appearance rollup already exists (duplicated across
mart_player_season + mart_player_profile plus an orphaned int model with divergent metric
derivations), so its consolidation was split into a governed task (#480). This PR adds
base_apif__player_profiles, enriches dim_player with five bio fields (profile-wins coalesce on the
four overlapping descriptors), and surfaces them additively on mart_player_profile. Local gates
green: dbt parse, sqlfluff lint (ST06 column-order fixed), check_layer_contract. The full BQ build is
deferred to ci-data-build (shared warehouse mid-rebuild from a concurrent CPO-approved dispatch).

## scope-auditor
VERDICT: PASS
risks_checked:
- All seven edited paths are within the contract scope_paths; no protected path touched; no
  aggregation snuck into core (the appearance rollup is genuinely deferred to #480, not partly built
  here); no §10 decision self-made — the profile-wins descriptor refresh is authorized in
  decisions_taken + the 2026-06-16 escalations.log entry.
- Coalesce(profile, players) on the four overlapping descriptors (name, birth_date, nationality,
  photo) may refresh published descriptors — an authorized data-quality preference; no metric/numeric
  column changes; done_when verifies the existing mart columns pre/post. Left-join sparsity (NULL bio
  for players without a profile) is anticipated by done_when ("populated for the backfilled universe").

## analytics-engineer-reviewer
VERDICT: PASS
risks_checked:
- Fan-out: dim_player left-joins base_apif__player_profiles on player_api_id; the base is tested
  unique on player_api_id (base.yml), so the 1:1 join cannot multiply rows — dim_player.player_sk
  [not_null, unique] grain holds. base_apif__player_profiles is a valid base model (reads stg via
  ref, dedups to latest per player_id, inherits view materialization, grain tested).
- Catalogue governance (A1): the five added columns are raw bio descriptors absent from
  metric_catalogue — no metric created or redefined, no sign-off needed. mart_player_profile
  additions are purely additive (grain (player_sk, season_sk), aggregation, and catalogue ratios all
  unchanged).
- Non-blocking notes (recorded, not fixed — to avoid needless re-review churn; flagged for
  ci-data-build): (1) base safe_cast(player_id) is redundant (already int64 in stg) but matches the
  base_apif__players defensive idiom; (2) dim_player.raw_ingested_at reflects the identity source,
  not the profile, for enriched rows — an internal lineage column (not published on the mart),
  semantics slightly loose.

## escalations
(none)
