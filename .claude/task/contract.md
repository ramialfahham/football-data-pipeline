# Task contract — feat: dim_team pure entity — drop the league_code stamp (Phase 2)

> CPO-approved this conversation (2026-06-17), the follow-up to Phase 1 (PR #488, merged: the new
> dim_team_competition_season_mapping membership dim). Phase 2 finishes the dim_team entity/affiliation
> split: dim_team becomes a PURE ENTITY by dropping its `league_code` column — the latest-ingest
> provenance stamp that was the root of the BL1/BL2 directory bug. Now that membership lives in
> dim_team_competition_season_mapping (Phase 1), nothing legitimately needs the stamp. Mirrors the
> player redesign (dim_player dropped league_code; affiliation is dim_player_team_season_mapping).
>
> Blast radius confirmed read-only: `mart_team_market_value` is the ONLY consumer that reads
> dim_team.league_code (its `where league_code='WC'`); every other mart takes only team_sk/name/logo
> from dim_team and gets league_code from fixtures/metrics. mart_team_market_value is NOT exported (no
> scripts/site reference) and has 0 rows with an actual market value (its source — the parked market-
> value automation #476/#418 — is empty), so the repoint is a structural correction with no live/shipped
> impact. Reviewers: scope-auditor (always) + analytics-engineer-reviewer (all paths dbt_project/**).

objective: >
  Make dim_team a pure team ENTITY by removing the league_code stamp, and repoint the one consumer.
  (a) Model `dbt_project/models/3_core/dim_team.sql` (MODIFIED): remove the `league_code` column from the
      SELECT. No other change — grain stays team_api_id; all identity/venue attributes unchanged. (Leave
      base_apif__teams_global as-is; its league_code becomes an unused passenger — base cleanup is out of
      scope.)
  (b) Schema `dbt_project/models/3_core/core.yml` (MODIFIED): remove the `league_code` column entry (+ its
      not_null test) from the dim_team block; update the dim_team description to mirror dim_player — "pure
      entity (identity only); carries no competition/season affiliation — membership lives in
      dim_team_competition_season_mapping, per-match facts in fct_fixture."
  (c) Mart `dbt_project/models/5_marts/shared/mart_team_market_value.sql` (MODIFIED): replace the
      `dim_team where league_code='WC'` filter with the WC team set from
      `dim_team_competition_season_mapping` (select distinct team_sk where league_code='WC'), inner-joined
      to dim_team for team_api_id/team_name/team_country. PRESERVE the output schema exactly (same columns
      incl. a literal `'WC' as league_code`, same grain one-row-per-team_sk, left join to
      int_team__market_value_latest for the value). This corrects the WC team set from the incomplete stamp
      (23 teams) to the full WC field (48 teams); all values stay null (source empty), mart not exported.
  (d) Docs `dbt_project/docs/layering.md` (MODIFIED): update the dim_team row of the dimension inventory to
      the pure-entity note (no affiliation; membership in dim_team_competition_season_mapping), mirroring
      the dim_player row.

refs: >
  This conversation 2026-06-17. Phase 2 of the dim_team entity/affiliation split; Phase 1 = PR #488
  (dim_team_competition_season_mapping), merged to main (cf2a0be). Mirrors the player model redesign
  (dim_player pure entity + dim_player_team_season_mapping). escalations.log 2026-06-17 (D6/D7).

scope_paths:
  - dbt_project/models/3_core/dim_team.sql
  - dbt_project/models/3_core/core.yml
  - dbt_project/models/5_marts/shared/mart_team_market_value.sql
  - dbt_project/docs/layering.md
  - .claude/task/contract.md
  - .claude/task/review.md

decisions_taken: >
  CPO (this conversation, 2026-06-17): (1) DROP dim_team.league_code (the stamp), making dim_team a pure
  entity — mirror dim_player; NOT keep-and-rename (renaming still forces the consumer repoint for no
  benefit and leaves a misuse-able column). (2) Repoint mart_team_market_value off the stamp onto the
  Phase-1 mapping dim, preserving its output schema. (3) Phase 2 = items (a)-(d) ONLY; the season-rollup
  enhancement (point mart_team_season at the spine to surface pre-season teams) is DEFERRED to its own PR
  (CPO: "keep Phase 2 to items 1-3"). (4) Leave base_apif__teams_global untouched (out of scope).

decisions_reserved:
  - The season-rollup enhancement (mart_team_season / int_team_season uses the mapping spine to include
    upcoming-only teams) — DEFERRED, separate PR. Do NOT touch mart_team_season or the int_team_season
    layer here.
  - base_apif__teams_global league_code cleanup — out of scope (left as an unused passenger column).
  - If a reviewer finds ANOTHER consumer of dim_team.league_code beyond mart_team_market_value, STOP and
    escalate rather than silently widening the repoint.
  - Any §10 (new mechanism, grain change, a shipped-output change to a LIVE mart) → escalate in plain language.

done_when:
  - dim_team builds without league_code; dbt parse clean; sqlfluff lint passes; check_layer_contract green.
  - No dangling reference to dim_team.league_code anywhere (grep + dbt parse clean); mart_team_market_value
    compiles against the new source.
  - Read-only BQ spot-check (or compiled-logic check): dim_team has no league_code; mart_team_market_value
    now yields the 48-team WC set (was 23), grain one-row-per-team, schema unchanged.
  - core.yml + layering.md reflect dim_team as a pure entity (no league_code; affiliation note).
  - ci-data-build green (the full BQ build + DQ tests, incl. dim_team's remaining tests and the mart).
  - reviewers: scope-auditor + analytics-engineer-reviewer both PASS (>=2 named risks each), no FAIL, every
    ESCALATE has a recorded CPO ANSWER.

amendments: (none)
