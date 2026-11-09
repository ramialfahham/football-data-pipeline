# Review — claude/83-competition-dim-v2 — 2026-11-09

Rebound after replaying the reviewed commit onto gitlab/main 64cd5efe: every reviewed model, seed, script and doc blob is unchanged. Five test files (test_export_landing.py, test_export_matches.py, test_export_site_data.py, test_registry_seed_projection.py, test_sentence_length_in_docs.py) carry main's comment sweep merged with this branch's code; the decision-history pin is main's.

diff_sha256: 806eeca84dae4ad6ec1dc5d82d17220fd7b2a005a66a6bb3edd13c54b90db241

rounds: 3

## scope-auditor
VERDICT: PASS
risks_checked:
- Round 1 FAIL: the home-board queries filtered competition_group on mart_competition_index, which does not serve it. Round 2: they filter the leaderboard marts' own column; closed.
- Round 2 FAIL: the J1 2027 group change lacked CPO approval, and the seeds/schema.yml exemption contradicted criterion 5. Round 3: J1 2027 is back to calendar, so no seed value changes; the four seed tests ref dim_league and the check has no exemption; closed.
- Every file is in scope_paths; the one amendment cites the approved criterion and layering.md line; no new mechanism, no recurring cost, no secrets.
- decisions_reserved (nav.json removal, #101 rotation, sort_order) stay undecided in the diff.

## analytics-engineer-reviewer
VERDICT: PASS
risks_checked:
- Layer placement: dim_league is the only reader of the registry seed; core reads seeds and base only; intermediate refs no mart; new mart columns are plain joins with no metric math.
- Grain: dim_league unique on league_code (tested); dim_competition_season joins on season_sk or (league_code, season_api_year) are 1:1.
- Carry-forward in dim_competition_season is last_value ignore nulls per league_code ordered by season; every domestic-league map row carries today's registry tier and group, cups carry none.
- Round 1 findings (landing query column, J1 2027 value) closed in rounds 2 and 3; the four seed tests now ref dim_league, which holds the same 48 codes; no cycle (tests are leaf nodes).

## platform-reviewer
VERDICT: PASS
risks_checked:
- check_layer_contract.py fails closed; the seed-reader scan covers every sql/yml/yaml under dbt_project except target, dbt_packages and logs, allows dim_league.sql only, and matches the two-argument ref form.
- Plant tests cover a mart, a model yml, a singular test, a macro, a seeds schema.yml, the two-argument ref, ignored target files, and every marts-only export branch; reverting any rule turns a test red.
- export_site_data.py reads the marts dataset only; fetch_nav takes the client and the mart's tier, pinned by a test.
- sync_dbt_vars.py SEED_COLUMNS and check_registry_var_sync.py share one import; pins move down only; no dependency, workflow, hook or credential change.

## data-engineer-reviewer
VERDICT: PASS
risks_checked:
- No ingestion, raw table, provider ID, ingest_active or history_seasons change; registry hunks only delete tier and competition_group.
- Registry, sync_dbt_vars.py SEED_COLUMNS and the generated seed change together; check_registry_var_sync.py follows by import.
- competition_season_map carries every domestic-league row's registry tier and group (J1 2027 restored to calendar in round 3); the onboarding skill adds the season-map step.
- Stale tier docstrings in sync_dbt_vars.py stripped in round 2.

## escalations
(none)
