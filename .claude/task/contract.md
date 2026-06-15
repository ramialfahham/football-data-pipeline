# Task contract — feat: player-endpoint staging models (PR-a2)

> Player-data initiative, PR-a2 — the staging half of PR-a (PR-a1 = ingestion code, merged as
> #473). Three generic staging models over the three new raw tables that PR-a1's loaders create
> + a backfill populates: stg_apif__squads, stg_apif__player_profiles, stg_apif__player_teams,
> plus their source declarations and generic-test entries. dbt-only; touches NO ingestion code,
> NO protected paths. Reviewers: scope-auditor + analytics-engineer-reviewer.
>
> HOLD-TO-COMMIT: this PR's staging models reference raw tables that only exist once the backfill
> dispatch (CPO-approved 2026-06-15, run 27532721705) creates them. Do NOT commit/open the PR until
> those tables exist AND real rows have been inspected AND the staging SQL has been validated
> against the real payloads (the transfers lesson — never green-build on assumed/empty data).
> See the approved plan §4, escalations.log 2026-06-15 (PR-a rulings R1–R4), and the layering note
> below.

objective: >
  Add three generic staging models (raw cleanup / 1:1 flatten only — no business logic) plus their
  source + test declarations:
  (1) stg_apif__squads — from RAW_APIF_SQUADS (/players/squads per team). Complete snapshot per
      run, so select the LATEST snapshot per league_code (like stg_apif__players), then flatten
      response[].squad_payload[].players[] → one row per (league_code, team_id, player_id) with
      shirt number / position / age / photo.
  (2) stg_apif__player_profiles — from RAW_APIF_PLAYER_PROFILES (/players/profiles per player).
      INCREMENTAL accumulation (skip-if-present loader: each snapshot holds only that run's new
      players), so UNION ALL snapshots (NOT latest-per-league — that would drop earlier players),
      flatten response[].profile_payload[].player → one row per raw profile record (grain carries
      raw_ingested_at; no entity dedup — base/PR-b assembles current-per-player). Bio columns:
      name, first/last, age, birth date/place/country, nationality, height, weight, number,
      position, photo.
  (3) stg_apif__player_teams — from RAW_APIF_PLAYER_TEAMS (/players/teams per player). INCREMENTAL
      like profiles → UNION ALL snapshots, flatten response[].teams_payload[] then unnest seasons →
      one row per (player_id, team_id, season_year, raw_ingested_at); no dedup.
  (4) sources.yml: declare raw_apif_squads / raw_apif_player_profiles / raw_apif_player_teams (no
      aggressive freshness — these are slow-moving). stg_apif__generic.yml: not_null on grain
      columns; unique only where a single snapshot is unique at that grain (squads only).

refs: >
  Approved plan §4 (staging models) + PR-a rulings R1–R4 (escalations.log 2026-06-15). PR-a1 (#473,
  merged) created the loaders + landing payload shapes this staging flattens. Backfill dispatch
  approved 2026-06-15 (run 27532721705).

scope_paths:
  - dbt_project/models/1_staging/api_football/sources.yml
  - dbt_project/models/1_staging/api_football/stg_apif__squads.sql
  - dbt_project/models/1_staging/api_football/stg_apif__player_profiles.sql
  - dbt_project/models/1_staging/api_football/stg_apif__player_teams.sql
  - dbt_project/models/1_staging/api_football/stg_apif__generic.yml
  - dbt_project/docs/layering.md
  - .claude/task/contract.md

decisions_taken: >
  Staging follows the layer contract (1:1 flatten, NO entity dedup / aggregation / joins — base
  does that). squads uses the standard latest-snapshot-per-league selection. profiles/teams UNION
  ALL snapshots because their loaders are skip-if-present (incremental landing) — the first
  incremental-accumulation raw tables in the repo; latest-per-league would silently drop players
  landed on earlier backfill days. This is the only approach consistent with the merged,
  CPO-approved cheap-ongoing loaders (the contract-clean alternative — re-fetch all players every
  run — contradicts the approved cost model). Landing payload shapes are fixed by PR-a1's loaders:
  response[]={team_id,squad_payload} / {player_id,profile_payload} / {player_id,teams_payload}.

decisions_reserved: >
  - The staging-contract CLARIFICATION that incremental-accumulation raw tables are staged by
    union-all-snapshots (vs the documented latest-per-league rule) may warrant a note in
    dbt_project/docs/layering.md / the stg_apif__generic.yml header. Whether that doc edit is a
    §10 layer-contract extension needing CPO sign-off is flagged FOR the analytics-engineer +
    scope-auditor review — not self-ruled here. layering.md is NOT edited in this draft; the
    rationale is documented inline in the models + the generic-yml header pending that ruling.
  - Anything beyond staging (base entity-dedup / current-per-player, core dim_player bio,
    fct_player_team_season, the affiliation timeline) is PR-b / PR-c.
  - If validation against the real backfilled payloads reveals a shape mismatch, fix the SQL — do
    not reshape the raw landing (that is PR-a1, merged).

done_when:
  - Three stg models compile (`dbt parse`) and, after the backfill, `dbt build --select` of the
    three models succeeds and their grain holds on REAL rows (squads unique at (league_code,
    team_id, player_id); profiles one row per player after base-dedup intent; teams unnested
    seasons present).
  - sources.yml declares the three raw tables; stg_apif__generic.yml has the three entries with
    not_null grain tests (+ unique only where a single snapshot is unique).
  - Real rows inspected in all three raw tables (non-empty payloads) BEFORE commit.
  - validate-local clean; sqlfluff lint passes on the three models.
  - reviewers: scope-auditor (always) + analytics-engineer-reviewer (dbt_project/**) both PASS.

amendments:
  - 2026-06-15: + dbt_project/docs/layering.md to scope_paths. Authority: CPO ruling Path B
    (escalations.log E1, 2026-06-15) — both cold reviewers escalated whether the incremental-
    accumulation staging deviation is a §10 layer-contract extension; CPO chose Path B (record it
    as a recognized pattern in the layering rulebook, with sign-off) over Path A (yml-note-only
    clarification). layering.md is NOT a protected path, so this is an ordinary in-scope amendment
    (no protected_override). Clean-tree amendment (the dbt changes were stashed, contract amended,
    then unstashed). Also folds in the analytics-engineer test-finding fixes (grain descriptions
    for squads/player_teams tightened to admit provider dupes / nullable seasons — verified in the
    real data: 10 squad grain dupes, 995 null season_year; no failing unique/not_null tests added,
    matching the stg_apif__players / transfers precedent).
