# Task contract — GAP-15 + GAP-19 (items 1–4): consumption-layer migration to dbt (Pilot PR1)

> CPO directions (this session, escalations.log 2026-06-14): the Pilot is sliced into TWO PRs.
> THIS is PR1 — the unblocked work. Move four consumption-layer computations out of the Python
> export into dbt (anti-pattern A5: logic/ranking in the frontend), and add the GAP-15
> team-fixtures mart. Slugs (GAP-19 item 5) are PR2; GAP-16 affiliation is deferred to the new
> player-data ingestion initiative. See docs/working_agreement.md §2/§6/§10, Appendix A (A3/A5).

objective: >
  Make the v2 export pure selection for these four surfaces by sourcing the facts from dbt:
  (1) GAP-19.1 leaderboard ranks — add goals_rank / assists_rank / shots_on_target_rank to
      mart_player_profile (DENSE_RANK over (league_code, season_api_year), zero performers
      unranked — the mart_top_scorers.scorer_rank pattern the CPO cited).
  (2) GAP-19.2 top-player rank — add top_player_rank to mart_momentum__player (ROW_NUMBER per
      (upcoming_fixture_sk, team_sk) ordered goals → assists → key passes → player_sk; the
      goals→assists→key-passes order is named in the GAP).
  (3) GAP-19.3 nav taxonomy — add a display_group column to the competition_types seed (a
      faithful migration of the export's _GROUP_OF_TYPE dict: same 9 mappings; the 3 friendly
      types map to empty = not in nav) + a seeds/schema.yml accepted_values test.
  (4) GAP-19.4 H2H canonical pair — add pair_key + is_canonical to mart_head_to_head.
  (5) GAP-15 — a new mart_team_fixtures (one row per (team, fixture), team perspective): next
      fixture + last-5 results, built on fct_fixture (both-side spine) + int_legs__team_match
      (finished perspective result, NOT re-derived) + dim_team (opponent identity), with
      upcoming_rank / recency_rank so the export selects rather than computes. NO slug column.
  Then shrink scripts/export_site_data.py: delete the Python ranking (shape_top_players,
  shape_leaderboards), the _GROUP_OF_TYPE nav dict in build_nav, and the H2H pair_keys
  computation; replace each with selection of the new dbt columns. Update the affected unit
  tests in tests/test_export_site_data.py. The slug code (slugify / fixture_slug / slug_map)
  and the form_window JSON key are NOT touched.

refs: GAP-15, GAP-19 (docs/wireframes/99_gaps_register.md, approved 2026-06-11); audit F4/F5/F6
  (F5 slug deferred); CPO Pilot rulings (escalations.log 2026-06-14).

scope_paths:
  - dbt_project/models/5_marts/shared/mart_team_fixtures.sql
  - dbt_project/models/5_marts/shared/mart_head_to_head.sql
  - dbt_project/models/5_marts/shared/mart_momentum__player.sql
  - dbt_project/models/5_marts/shared/mart_player_profile.sql
  - dbt_project/models/5_marts/shared/shared.yml
  - dbt_project/seeds/competition_types.csv
  - dbt_project/seeds/schema.yml
  - scripts/export_site_data.py
  - tests/test_export_site_data.py
  - .claude/task/contract.md

decisions_taken: >
  Approved by the CPO this session ("PR1 approved", 2026-06-14). The four migrations and the
  GAP-15 mart implement CPO-approved GAP dispositions (gaps_register 2026-06-11) — no new
  product/metric/naming decisions. Ranking method follows the cited codified pattern:
  leaderboard ranks use DENSE_RANK + >0 exclusion (= mart_top_scorers.scorer_rank); per-side
  SELECTION ranks (top_player_rank, upcoming_rank, recency_rank) use ROW_NUMBER (strict pick
  order). display_group is a 1:1 migration of the shipped _GROUP_OF_TYPE values (no new nav
  identifiers). mart_team_fixtures reuses the tested int_legs__team_match for finished results
  (no result re-derivation); it materialises as a view (thin denormalisation over tested core,
  no heavy aggregate) — consistent with the parked stash's choice.

decisions_reserved:
  - SLUGS (GAP-19.5, E2 where produced / E3 spelling) are NOT in this PR — they are PR2, pending
    the two blinded CPO rulings. Do NOT add any slug column, and do NOT reintroduce the stash's
    url_slugs UDF macros or the dbt_project.yml on-run-start hook (anti-pattern A3). If a slug
    surfaces in this diff, it is a defect.
  - GAP-16 team affiliation is NOT in this PR — deferred to the player-data ingestion initiative.
    mart_player_profile gets ONLY the leaderboard rank columns; no latest_team / team history.
  - Leaderboard SET is fixed to the shipped _LEADERBOARD_METRICS (goals, assists,
    shots_on_target). Adding/removing a board, or any per-90/new metric, is a CPO catalogue
    decision — out of scope.
  - If a reviewer finds a consumer of the removed export functions that this PR misses, or any
    behaviour change in the published JSON beyond "same values, now sourced from dbt", STOP and
    surface it — the export migration must be value-preserving (the form_window key, slug_map,
    and all non-migrated payloads unchanged).

done_when:
  - mart_team_fixtures exists (grain (team_sk, fixture_sk); upcoming_rank/recency_rank; no slug)
    with relationships + grain + result accepted_values tests in shared.yml.
  - mart_head_to_head has pair_key + is_canonical; mart_momentum__player has top_player_rank;
    mart_player_profile has goals_rank/assists_rank/shots_on_target_rank — each with a
    shared.yml test.
  - competition_types.csv has display_group (9 mapped + 3 empty); seeds/schema.yml asserts its
    accepted_values; the values byte-match the retired _GROUP_OF_TYPE dict.
  - export_site_data.py computes none of the four in Python (functions removed/replaced by
    selection); tests/test_export_site_data.py updated; slug code + form_window key untouched.
  - `dbt parse` succeeds (all refs resolve); sqlfluff clean on changed SQL; validate-local gates
    (layer contract, registry sync, python) pass; python export unit tests pass.
  - reviewers: scope-auditor (always) + analytics-engineer-reviewer (dbt_project/** + export_*)
    + cto-reviewer (scripts/export_* + tests/**) — PASS against the locked diff hash.

amendments: (none)
