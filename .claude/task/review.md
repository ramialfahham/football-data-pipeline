# Review — feat/gap15-gap19-marts — 2026-06-14

> Pilot PR1 (CPO rulings, escalations.log 2026-06-14): GAP-15 (mart_team_fixtures) + GAP-19
> items 1-4 (leaderboard ranks, top-player rank, nav display_group seed, H2H canonical pair) —
> move four consumption-layer computations out of scripts/export_site_data.py into dbt; the
> export shrinks to pure selection. Slugs (GAP-19 item 5) and GAP-16 affiliation are OUT
> (PR2 / the player-data initiative). Local validation: export unit tests (17) PASS, py_compile
> OK, layer-contract + registry-sync gates PASS, dbt parse resolves all refs, sqlfluff clean.
>
> Review cycle: THREE cold iterations (routed reviewers: scope-auditor + analytics-engineer-
> reviewer + cto-reviewer). Iter 1 — all FAIL (scope-auditor: export re-derived the canonical
> pair_key in Python (A5); analytics: is_finished semantic + missing rank/pair tests; cto:
> _display_group_of_type + null-rank untested). Iter 2 — scope-auditor + analytics PASS; cto
> FAIL (H2H team-id membership over-fetch (~N^2); silent-empty on missing rank column). Iter 3
> — all PASS against the hash below. Fixes applied across iterations: H2H lookup is now pure
> directed-(team,opponent)-tuple selection (no identity derivation, no over-fetch);
> is_finished -> has_result with recency_rank gated on it; assists_rank/shots_on_target_rank/
> top_player_rank-uniqueness/is_canonical-consistency tests added; _display_group_of_type +
> null-rank exclusion tests added; leaderboard sort lambda binds rank_col. The cto's residual
> "KeyError under mart-schema drift" note is non-blocking (a Python fallback would reintroduce
> the A5 ranking just removed; reliance on the mart column is the consumption-layer contract).
> Deferred (out of this locked scope): layering.md mart-inventory row for mart_team_fixtures
> (separate doc-sync task); slug rulings E2/E3 (PR2); GAP-16 affiliation (player-data initiative).

diff_sha256: 745410d5a2748b4ecfdf455d9ee25234df4a18e878e17c4fa11ebaa4b19e6f3c

## scope-auditor
VERDICT: PASS
risks_checked:
- §10/Appendix-A integrity: all changed files are within scope_paths; no slug column or
  url_slugs UDF / on-run-start hook reintroduced (A3); no GAP-16 affiliation column on
  mart_player_profile; the export now SELECTS the new dbt columns and the H2H lookup filters
  mart_head_to_head by the directed (team_sk, opponent_team_sk) key — no canonical pair
  identity derived in Python (A5 resolved from iter 1).
- Boundary/decisions_reserved: leaderboard set unchanged (goals/assists/shots_on_target, the
  shipped _LEADERBOARD_METRICS — no invented metric, A1); display_group is a byte-faithful
  migration of the retired _GROUP_OF_TYPE values (no new published nav identifier); the
  form_window JSON key and non-migrated payloads are untouched; mart_team_fixtures is a view
  shipped consumer-later (ship-the-mart-first), not a scope expansion.

## analytics-engineer-reviewer
VERDICT: PASS
risks_checked:
- mart_team_fixtures grain + rank populations: (team_sk, fixture_sk) is unique from the
  union-all spine (the where s.team_sk is not null filter removes one-sided rows; the grain
  test guards it); has_result = (result leg exists) cleanly partitions the recency population
  and recency_rank is null-gated so non-result rows carry no rank — covered by
  team_fixtures_result_present + team_fixtures_recency_has_result.
- Ranking correctness vs the codified pattern: mart_player_profile leaderboard ranks use
  DENSE_RANK over (league_code, season_api_year) order goals desc, assists desc, minutes asc —
  byte-identical to mart_top_scorers.scorer_rank — with CASE goals>0 zero-exclusion; per-side
  selection ranks (top_player_rank, upcoming/recency) use ROW_NUMBER; every new shown column
  now has a shared.yml/seeds test; no hardcoded league_code anywhere.

## cto-reviewer
VERDICT: PASS
risks_checked:
- H2H directed-pair filter correctness + safety (export_site_data.py): ids are int()-cast
  before interpolation (no injection); the directed (team_sk=home and opponent_team_sk=away)
  OR-filter retrieves exactly the home-perspective row per fixture (no team-id cross product /
  over-fetch from iter 2) and is indexed by the directed key; pair_key/is_canonical added to
  _H2H_DROP so the published head_to_head payload stays byte-identical.
- Export selection purity + tests: shape_top_players/shape_leaderboards/build_nav compute
  nothing — they select by top_player_rank / <metric>_rank / display_group; the leaderboard
  sort lambda binds rank_col via default-arg (no late-binding); _display_group_of_type mirrors
  the existing fetch_glossary seed-read pattern (no new mechanism, A3); updated tests assert
  the selection contract incl. null-rank exclusion + the seed read. Residual KeyError-under-
  schema-drift is non-blocking (a fallback would reintroduce A5).

## escalations
(none — three cold iterations; all three routed reviewers PASS against the locked hash. No
reviewer raised a §10 question on this diff. The two slug rulings (E2 where produced, E3
spelling) are recorded in escalations.log as PENDING for PR2 and are NOT part of this PR;
GAP-16 affiliation is deferred to the player-data ingestion initiative.)
